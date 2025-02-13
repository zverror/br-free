import pytest

from baserow.contrib.builder.elements.element_types import (
    ButtonElementType,
    CheckboxElementType,
    ChoiceElementType,
    FormContainerElementType,
    HeadingElementType,
    IFrameElementType,
    ImageElementType,
    InputTextElementType,
    LinkElementType,
    TableElementType,
    TextElementType,
)
from baserow.contrib.builder.elements.models import (
    ButtonElement,
    CheckboxElement,
    ChoiceElement,
    Element,
    FormContainerElement,
    HeadingElement,
    IFrameElement,
    ImageElement,
    InputTextElement,
    LinkElement,
    TextElement,
)


@pytest.fixture
def formula_generator_fixture(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source_1 = data_fixture.create_builder_local_baserow_get_row_data_source()
    data_source_2 = data_fixture.create_builder_local_baserow_get_row_data_source()
    formula_1 = f"get('data_source.{data_source_1.id}.field_1')"
    formula_2 = f"get('data_source.{data_source_2.id}.field_1')"
    id_mapping = {"builder_data_sources": {data_source_1.id: data_source_2.id}}

    return {
        "user": user,
        "page": page,
        "data_source_1": data_source_1,
        "data_source_2": data_source_2,
        "formula_1": formula_1,
        "formula_2": formula_2,
        "id_mapping": id_mapping,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "element_cls,element_type",
    [
        (ButtonElement, ButtonElementType),
        (CheckboxElement, CheckboxElementType),
        (ChoiceElement, ChoiceElementType),
        (FormContainerElement, FormContainerElementType),
        (HeadingElement, HeadingElementType),
        (IFrameElement, IFrameElementType),
        (ImageElement, ImageElementType),
        (InputTextElement, InputTextElementType),
        (LinkElement, LinkElementType),
        (TextElement, TextElementType),
    ],
)
def test_element_formula_generator_mixin(
    data_fixture,
    formula_generator_fixture,
    element_cls,
    element_type,
):
    """
    Test the ElementFormulaGenerator mixin.

    This test assumes that the Element types store formulas as direct
    attributes of its class. If the Element type also stores formulas
    elsewhere, those formula fields need to be tested separately.

    E.g. the LinkElementType stores formulas differently; it has a JSON field
    named page_parameters which may contain formulas. This is further tested
    in the test_link_element_formula_generator() test case.
    """

    simple_formula_fields = {
        formula_field: formula_generator_fixture["formula_1"]
        for formula_field in element_type.simple_formula_fields
    }
    exported_element = data_fixture.create_builder_element(
        element_cls,
        **simple_formula_fields,
    )
    serialized_element = element_type().export_serialized(exported_element)

    imported_element = element_type().import_serialized(
        formula_generator_fixture["page"],
        serialized_element,
        formula_generator_fixture["id_mapping"],
    )

    for formula_field in element_type.simple_formula_fields:
        assert (
            getattr(imported_element, formula_field)
            == formula_generator_fixture["formula_2"]
        )


@pytest.mark.django_db
def test_link_element_formula_generator(data_fixture, formula_generator_fixture):
    """
    Test the LinkElementType's formula_generator().

    Although the LinkElement's general formula fields are already tested in
    test_element_formula_generator_mixin(), there are additional formulas
    in its page_parameters JSON field that need to be specifically tested.
    """

    exported_element = data_fixture.create_builder_element(
        LinkElement,
        value=formula_generator_fixture["formula_1"],
        page_parameters=[
            {
                "name": "foo",
                "value": formula_generator_fixture["formula_1"],
            },
            {
                "name": "bar",
                "value": formula_generator_fixture["formula_1"],
            },
        ],
    )
    serialized_element = LinkElementType().export_serialized(exported_element)

    imported_element = LinkElementType().import_serialized(
        formula_generator_fixture["page"],
        serialized_element,
        formula_generator_fixture["id_mapping"],
    )

    assert imported_element.value == formula_generator_fixture["formula_2"]

    for page_param in imported_element.page_parameters:
        assert page_param.get("value") == formula_generator_fixture["formula_2"]


@pytest.mark.django_db
def test_table_element_formula_generator(data_fixture, formula_generator_fixture):
    """Test that the formulas are imported for TableElementType."""

    table, _, _ = data_fixture.build_table(
        user=formula_generator_fixture["user"],
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["FooRow", "BarRow"],
        ],
    )

    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=formula_generator_fixture["page"],
        table=table,
    )

    exported = {
        "id": 1,
        "order": "1.0",
        "type": "table",
        "parent_element_id": None,
        "roles": [],
        "role_type": Element.ROLE_TYPES.ALLOW_ALL,
        "fields": [
            {
                "uid": "7778cf93-77e5-4064-ab32-3342e2b1656a",
                "name": "Field",
                "type": "button",
                "config": {"label": "get('current_record.field_999')"},
            }
        ],
        "data_source_id": 888,
    }
    id_mapping = {
        "builder_data_sources": {888: data_source.id},
        "database_fields": {999: 111},
    }

    table_element = TableElementType().import_serialized(
        formula_generator_fixture["page"],
        exported,
        id_mapping,
    )

    assert table_element.fields.get().config == {
        "label": "get('current_record.field_111')"
    }
    assert table_element.data_source_id == data_source.id
