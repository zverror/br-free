from dataclasses import Field
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Type, Union

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models.query import QuerySet

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from baserow.api.pagination import PageNumberPagination
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.api.views.serializers import serialize_group_by_metadata
from baserow.contrib.database.rows.registries import row_metadata_registry
from baserow.contrib.database.table.models import GeneratedTableModel
from baserow.contrib.database.views.filters import AdHocFilters
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.registries import view_type_registry


def get_public_view_authorization_token(request: Request) -> Optional[str]:
    """
    Returns the permission token to access a public view, if any.

    :param request: The request.
    :return: The public view permission token.
    """

    auth_header = request.headers.get(settings.PUBLIC_VIEW_AUTHORIZATION_HEADER, None)
    try:
        _, token = auth_header.split(" ", 1)
    except (AttributeError, ValueError):
        return None
    return token


def get_view_filtered_queryset(
    view: Type[View],
    filters: Optional[AdHocFilters] = None,
    order_by: Optional[str] = None,
    query_params: Optional[Dict[str, Any]] = None,
    model: Optional[GeneratedTableModel] = None,
) -> QuerySet:
    """
    Returns a queryset that is filtered based on the provided view, adhoc filters, and
    query parameters (i.e. search value).

    :param view: The view to filter the queryset by.
    :param filters: The adhoc filters to apply to the queryset.
    :param order_by: The order by string to apply to the queryset.
    :param query_params: The query parameters to apply to the queryset.
    :param model: The model to filter the queryset by.
    :return: The filtered queryset.
    """

    if model is None:
        model = view.table.get_model()

    if query_params is None:
        query_params = {}

    has_adhoc_filters = filters is not None and filters.has_any_filters
    has_adhoc_sorts = order_by is not None
    search_value = query_params.get("search")
    search_mode = query_params.get("search_mode")

    queryset = ViewHandler().get_queryset(
        view,
        apply_sorts=not has_adhoc_sorts,
        apply_filters=not has_adhoc_filters,
        search=search_value,
        search_mode=search_mode,
        model=model,
    )

    if has_adhoc_sorts:
        queryset = queryset.order_by_fields_string(order_by, False)

    if has_adhoc_filters:
        queryset = filters.apply_to_queryset(model, queryset)
    return queryset


class PublicViewFilteredQuerySet(NamedTuple):
    queryset: QuerySet
    field_ids: Iterable[int]
    publicly_visible_field_options: Dict[str, Any]


def get_public_view_filtered_queryset(
    view: Type[View], request: Request, query_params: Dict[str, Any]
) -> PublicViewFilteredQuerySet:
    """
    Returns a queryset that is filtered based on the provided publicly shared view and
    request.

    :param view: The publicly shared view to filter the queryset by.
    :param request: The request to filter the queryset by.
    :param query_params: The already validated request query parameters to filter the
        queryset by.
    :return: The filtered queryset.
    """

    search = query_params.get("search")
    search_mode = query_params.get("search_mode")
    order_by = request.GET.get("order_by")
    group_by = request.GET.get("group_by")
    include_fields = request.GET.get("include_fields")
    exclude_fields = request.GET.get("exclude_fields")
    adhoc_filters = AdHocFilters.from_request(request)
    view_type = view_type_registry.get_by_model(view)
    model = view.table.get_model()

    (
        queryset,
        field_ids,
        publicly_visible_field_options,
    ) = ViewHandler().get_public_rows_queryset_and_field_ids(
        view,
        search=search,
        search_mode=search_mode,
        order_by=order_by,
        group_by=group_by,
        include_fields=include_fields,
        exclude_fields=exclude_fields,
        adhoc_filters=adhoc_filters,
        table_model=model,
        view_type=view_type,
    )
    return PublicViewFilteredQuerySet(
        queryset=queryset,
        field_ids=field_ids,
        publicly_visible_field_options=publicly_visible_field_options,
    )


class PaginatedData(NamedTuple):
    response: Response
    page: QuerySet
    paginator: Union[LimitOffsetPagination, PageNumberPagination]


def paginate_and_serialize_queryset(
    queryset: QuerySet[GeneratedTableModel],
    request: Request,
    field_ids: Optional[Iterable[int]],
) -> PaginatedData:
    """
    Paginate and serialize the data for the provided queryset and view.

    :param queryset: The queryset to paginate and serialize.
    :param request: The request containing the pagination query parameters.
    :param field_ids: The (optional) field IDs to restrict the serialized data to.
    :return: The paginated data containing the paginator, the page of results, and
        response containing the serialized data.
    """

    if LimitOffsetPagination.limit_query_param in request.GET:
        paginator = LimitOffsetPagination()
    else:
        paginator = PageNumberPagination()

    page = paginator.paginate_queryset(queryset, request)
    serializer_class = get_row_serializer_class(
        queryset.model,
        RowSerializer,
        is_response=True,
        field_ids=field_ids,
    )
    serializer = serializer_class(page, many=True)

    response = paginator.get_paginated_response(serializer.data)
    return PaginatedData(response, page, paginator)


def serialize_view_field_options(
    view: Type[View],
    model: GeneratedTableModel,
    create_if_missing: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Serializes the view field options for the provided view and the given model.

    :param view: The view to serialize the field options for.
    :param model: The model to serialize the field options for.
    :param create_if_missing: Whether to create the field options if they are missing.
    :param context: The context to serialize the field options with.
    :return: The serialized view field options.
    """

    if context is None:
        context = {"fields": [o["field"] for o in model._field_objects.values()]}

    view_type = view_type_registry.get_by_model(view)
    serializer_class = view_type.get_field_options_serializer_class(
        create_if_missing=create_if_missing
    )
    return serializer_class(view, context=context).data


def serialize_rows_metadata(
    user: AbstractUser, view: Type[View], rows: QuerySet[GeneratedTableModel]
) -> Dict[str, Any]:
    """
    Serializes the metadata for the provided rows.

    :param user: The user to serialize the metadata for.
    :param view: The view to serialize the metadata for.
    :param rows: The rows to serialize the metadata for.
    :return: The serialized metadata for the provided rows.
    """

    return row_metadata_registry.generate_and_merge_metadata_for_rows(
        user, view.table, (row.id for row in rows)
    )


def serialize_group_by_fields_metadata(
    queryset: QuerySet[GeneratedTableModel],
    group_by_fields: List[Field],
    page: QuerySet[GeneratedTableModel],
):
    group_by_metadata = ViewHandler().get_group_by_metadata_in_rows(
        group_by_fields, page, queryset
    )
    serialized_group_by_metadata = serialize_group_by_metadata(group_by_metadata)
    return serialized_group_by_metadata
