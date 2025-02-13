import json
from io import BytesIO
from unittest.mock import Mock

from django.db import transaction

import pytest

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.models import SORT_ORDER_ASC, SORT_ORDER_DESC
from baserow.contrib.database.views.view_filters import ContainsViewFilterType
from baserow.contrib.integrations.local_baserow.mixins import (
    LocalBaserowTableServiceFilterableMixin,
    LocalBaserowTableServiceSearchableMixin,
    LocalBaserowTableServiceSortableMixin,
)
from baserow.contrib.integrations.local_baserow.service_types import (
    LocalBaserowTableServiceType,
)
from baserow.core.handler import CoreHandler
from baserow.core.registries import ImportExportConfig
from baserow.test_utils.pytest_conftest import FakeDispatchContext


def get_test_service_type(mixin_class):
    class FakeServiceType(mixin_class, LocalBaserowTableServiceType):
        model_class = Mock()

    return FakeServiceType()


@pytest.mark.django_db
def test_local_baserow_table_service_filterable_mixin_get_queryset(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceFilterableMixin)
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Names", table=table)
    table_model = table.get_model()
    service = data_fixture.create_local_baserow_list_rows_service(table=table)

    [alessia, alex, alastair, alexandra] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "Alessia"},
            {f"field_{field.id}": "Alex"},
            {f"field_{field.id}": "Alastair"},
            {f"field_{field.id}": "Alexandra"},
        ],
    )

    dispatch_context = FakeDispatchContext()

    # No filters of any kind.
    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alastair.id, alexandra.id]

    # Service filter ensures that the name contains "Ale",
    # which matches Alex, Alexandra and Alessia
    data_fixture.create_local_baserow_table_service_filter(
        service=service,
        field=field,
        value="Ale",
        type=ContainsViewFilterType.type,
        value_is_formula=False,
    )

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alexandra.id]

    # Adhoc filter ensures that we also filter on "Alexa", which matches Alexandra.
    dispatch_context = Mock()
    dispatch_context.filters.return_value = json.dumps(
        {
            "groups": [],
            "filter_type": "AND",
            "filters": [
                {
                    "field": field.id,
                    "type": ContainsViewFilterType.type,
                    "value": "Alexa",
                }
            ],
        }
    )

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alexandra.id]


@pytest.mark.django_db(transaction=True)
def test_local_baserow_table_service_filterable_mixin_import_export(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    table = data_fixture.create_database_table(database=database)
    text_field = data_fixture.create_text_field(name="Text", table=table)
    single_select_field = data_fixture.create_single_select_field(
        table=table, name="Single", order=1
    )
    single_option = data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    page = data_fixture.create_builder_page(builder=builder)
    integration = data_fixture.create_local_baserow_integration(application=builder)
    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page, table=table, integration=integration
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=data_source.service, field=text_field, value="foobar", order=0
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=data_source.service, field=text_field, value="123", order=1
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=data_source.service,
        field=single_select_field,
        value=single_option.id,
        order=2,
    )
    data_fixture.create_builder_table_element(
        page=page,
        data_source=data_source,
        fields=[
            {
                "name": "Click me",
                "type": "button",
                "config": {"label": "'Click'"},
            },
        ],
    )

    config = ImportExportConfig(include_permission_data=False)
    exported_applications = CoreHandler().export_workspace_applications(
        workspace, BytesIO(), config
    )

    # Ensure the values are json serializable
    try:
        json.dumps(exported_applications)
    except Exception as e:
        pytest.fail(f"Exported applications are not json serializable: {e}")

    imported_applications, _ = CoreHandler().import_applications_to_workspace(
        workspace, exported_applications, BytesIO(), config, None
    )
    imported_database, imported_builder = imported_applications

    # Pluck out the imported database records.
    imported_table = imported_database.table_set.get()
    imported_text_field = imported_table.field_set.get(name="Text")
    imported_single_select_field = imported_table.field_set.get(name="Single").specific
    imported_select_option = imported_single_select_field.select_options.get()

    # Pluck out the imported builder records.
    imported_page = imported_builder.page_set.get()
    imported_datasource = imported_page.datasource_set.get()
    imported_filters = [
        {"field_id": sf.field_id, "value": sf.value}
        for sf in imported_datasource.service.service_filters.all()
    ]

    assert imported_filters == [
        {"field_id": imported_text_field.id, "value": "foobar"},
        {"field_id": imported_text_field.id, "value": "123"},
        {
            "field_id": imported_single_select_field.id,
            "value": str(imported_select_option.id),
        },
    ]


@pytest.mark.django_db
def test_local_baserow_table_service_filterable_mixin_get_used_field_names(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceFilterableMixin)
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Names", table=table)
    service = data_fixture.create_local_baserow_list_rows_service(table=table)
    service_filter = data_fixture.create_local_baserow_table_service_filter(
        service=service,
        field=field,
        value="'A'",
        order=0,
    )

    field_names = {
        "all": {service.id: []},
        "external": {service.id: []},
        "internal": {},
    }

    dispatch_context = FakeDispatchContext(public_formula_fields=field_names)

    result = service_type.get_used_field_names(service, dispatch_context)

    assert result == [field.db_column]


@pytest.mark.django_db
def test_local_baserow_table_service_sortable_mixin_get_queryset(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceSortableMixin)
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Names", table=table)
    table_model = table.get_model()
    service = data_fixture.create_local_baserow_list_rows_service(table=table)

    [aardvark, badger, crow, dragonfly] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "Aardvark"},
            {f"field_{field.id}": "Badger"},
            {f"field_{field.id}": "Crow"},
            {f"field_{field.id}": "Dragonfly"},
        ],
    )

    dispatch_context = FakeDispatchContext()

    # No sorts of any kind.
    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [aardvark.id, badger.id, crow.id, dragonfly.id]

    # Service sort ensures that the names are sorted DESC.
    data_fixture.create_local_baserow_table_service_sort(
        service=service, field=field, order_by=SORT_ORDER_DESC, order=0
    )

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [dragonfly.id, crow.id, badger.id, aardvark.id]

    # Adhoc sort overrides the service sort.
    dispatch_context = Mock()
    dispatch_context.filters.return_value = None
    dispatch_context.sortings.return_value = field.db_column

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [aardvark.id, badger.id, crow.id, dragonfly.id]


@pytest.mark.django_db
def test_local_baserow_table_service_sortable_mixin_get_used_field_names(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceSortableMixin)
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Names", table=table)
    service = data_fixture.create_local_baserow_list_rows_service(table=table)
    service_sort = data_fixture.create_local_baserow_table_service_sort(
        service=service, field=field, order_by=SORT_ORDER_ASC, order=0
    )
    field_names = {
        "all": {service.id: []},
        "external": {service.id: []},
        "internal": {},
    }

    dispatch_context = FakeDispatchContext(public_formula_fields=field_names)

    result = service_type.get_used_field_names(service, dispatch_context)

    assert result == [field.db_column]


@pytest.mark.django_db(transaction=True)
def test_local_baserow_table_service_searchable_mixin_get_queryset(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceSearchableMixin)

    with transaction.atomic():
        user = data_fixture.create_user()
        table = data_fixture.create_database_table(user=user)
        field = data_fixture.create_text_field(name="Names", table=table)
        service = data_fixture.create_local_baserow_list_rows_service(table=table)
        [alessia, alex, alastair, alexandra] = RowHandler().create_rows(
            user,
            table,
            rows_values=[
                {f"field_{field.id}": "Alessia"},
                {f"field_{field.id}": "Alex"},
                {f"field_{field.id}": "Alastair"},
                {f"field_{field.id}": "Alexandra"},
            ],
        )

    table_model = table.get_model()
    dispatch_context = FakeDispatchContext()

    # No search query of any kind.
    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alastair.id, alexandra.id]

    # Add a service level search query
    service.search_query = "'Ale'"

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alexandra.id]

    # Adhoc search queries extend the service search query.
    dispatch_context = FakeDispatchContext(
        searchable_fields=[field.db_column], search_query="Alexa"
    )

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alexandra.id]


@pytest.mark.django_db
def test_local_baserow_table_service_searchable_mixin_get_used_field_names(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceSearchableMixin)
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Names", table=table)
    service = data_fixture.create_local_baserow_list_rows_service(
        table=table, search_query="'a'"
    )
    field_names = {
        "all": {service.id: []},
        "external": {service.id: []},
        "internal": {},
    }

    dispatch_context = FakeDispatchContext(public_formula_fields=field_names)

    result = service_type.get_used_field_names(service, dispatch_context)

    assert result == [field.tsv_db_column]
