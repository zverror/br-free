from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.applications.errors import ERROR_APPLICATION_DOES_NOT_EXIST
from baserow.api.decorators import map_exceptions
from baserow.api.errors import ERROR_PERMISSION_DENIED
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.api.utils import (
    DiscriminatorCustomFieldsMappingSerializer,
    apply_exception_mapping,
)
from baserow.contrib.builder.api.data_sources.errors import (
    ERROR_DATA_DOES_NOT_EXIST,
    ERROR_DATA_SOURCE_DOES_NOT_EXIST,
    ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
    ERROR_DATA_SOURCE_REFINEMENT_FORBIDDEN,
)
from baserow.contrib.builder.api.data_sources.serializers import (
    DispatchDataSourceRequestSerializer,
)
from baserow.contrib.builder.api.domains.serializers import PublicBuilderSerializer
from baserow.contrib.builder.api.pages.errors import ERROR_PAGE_DOES_NOT_EXIST
from baserow.contrib.builder.api.workflow_actions.serializers import (
    BuilderWorkflowActionSerializer,
)
from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.data_sources.exceptions import (
    DataSourceDoesNotExist,
    DataSourceImproperlyConfigured,
    DataSourceRefinementForbidden,
)
from baserow.contrib.builder.data_sources.handler import DataSourceHandler
from baserow.contrib.builder.data_sources.service import DataSourceService
from baserow.contrib.builder.domains.service import DomainService
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.elements.service import ElementService
from baserow.contrib.builder.errors import ERROR_BUILDER_DOES_NOT_EXIST
from baserow.contrib.builder.exceptions import BuilderDoesNotExist
from baserow.contrib.builder.pages.exceptions import PageDoesNotExist
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.service import BuilderService
from baserow.contrib.builder.workflow_actions.registries import (
    builder_workflow_action_type_registry,
)
from baserow.contrib.builder.workflow_actions.service import (
    BuilderWorkflowActionService,
)
from baserow.core.exceptions import ApplicationDoesNotExist, PermissionException
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.registries import service_type_registry

from .serializers import PublicDataSourceSerializer, PublicElementSerializer


class PublicBuilderByDomainNameView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="domain_name",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.STR,
                description="Returns the builder published for the given domain name.",
            )
        ],
        tags=["Builder public"],
        operation_id="get_public_builder_by_domain_name",
        description=(
            "Returns the public serialized version of the builder for "
            "the given domain name and its pages ."
        ),
        responses={
            200: PublicBuilderSerializer,
            404: get_error_schema(["ERROR_BUILDER_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions({BuilderDoesNotExist: ERROR_BUILDER_DOES_NOT_EXIST})
    def get(self, request, domain_name):
        """
        Responds with a serialized version of the builder related to the query.
        Try to match a published builder for the given domain name. Used to display
        the public site.
        """

        builder = DomainService().get_public_builder_by_domain_name(
            request.user, domain_name
        )

        return Response(PublicBuilderSerializer(builder).data)


class PublicBuilderByIdView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="builder_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the builder related to the "
                "provided Id and its pages.",
            )
        ],
        tags=["Builder public"],
        operation_id="get_public_builder_by_id",
        description=(
            "Returns the public serialized version of the builder and its pages for "
            "the given builder id."
        ),
        responses={
            200: PublicBuilderSerializer,
            404: get_error_schema(["ERROR_BUILDER_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            BuilderDoesNotExist: ERROR_BUILDER_DOES_NOT_EXIST,
            ApplicationDoesNotExist: ERROR_APPLICATION_DOES_NOT_EXIST,
        }
    )
    def get(self, request, builder_id):
        """
        Returns a public version of the builder for the given id. This version can be
        used to display the preview before publishing.
        """

        builder = BuilderService().get_builder(request.user, builder_id)

        return Response(PublicBuilderSerializer(builder).data)


class PublicElementsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the elements of the page related to the "
                "provided Id.",
            )
        ],
        tags=["Builder elements"],
        operation_id="list_public_builder_page_elements",
        description=(
            "Lists all the elements of the page related to the provided parameter. "
            "If the user is Anonymous, the page must belong to a published builder "
            "instance to being accessible."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                element_type_registry, PublicElementSerializer, many=True
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, page_id):
        """
        Responds with a list of serialized elements that belongs to the given page id.
        """

        page = PageHandler().get_page(page_id)

        elements = ElementService().get_elements(request.user, page)

        data = [
            element_type_registry.get_serializer(element, PublicElementSerializer).data
            for element in elements
        ]
        return Response(data)


class PublicDataSourcesView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only the data_sources of the page related to the "
                "provided Id if the related builder is public.",
            )
        ],
        tags=["Builder data sources"],
        operation_id="list_public_builder_page_data_sources",
        description=(
            "Lists all the data_sources of the page related to the provided parameter "
            "if the builder is public."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                service_type_registry, PublicDataSourceSerializer, many=True
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, page_id):
        """
        Responds with a list of serialized data_sources that belong to the page if the
        user has access to it.
        """

        page = PageHandler().get_page(page_id)

        data_sources = DataSourceService().get_data_sources(request.user, page)

        data = [
            service_type_registry.get_serializer(
                data_source.service,
                PublicDataSourceSerializer,
                context={"data_source": data_source},
            ).data
            for data_source in data_sources
            if data_source.service and data_source.service.integration_id
        ]
        return Response(data)


class PublicBuilderWorkflowActionsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only the public workflow actions of the page related "
                "to the provided Id.",
            )
        ],
        tags=["Builder workflow actions"],
        operation_id="list_public_builder_page_workflow_actions",
        description=(
            "Lists all the workflow actions with their public accessible data. Some "
            "configuration might be omitted for security reasons such as passwords or "
            "PII."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                builder_workflow_action_type_registry,
                BuilderWorkflowActionSerializer,
                many=True,
                name_prefix="public_",
                extra_params={"public": True},
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, page_id: int):
        page = PageHandler().get_page(page_id)

        workflow_actions = BuilderWorkflowActionService().get_workflow_actions(
            request.user, page
        )

        data = [
            builder_workflow_action_type_registry.get_serializer(
                workflow_action,
                BuilderWorkflowActionSerializer,
                extra_params={"public": True},
            ).data
            for workflow_action in workflow_actions
        ]

        return Response(data)


class PublicDispatchDataSourceView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="data_source_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the data_source you want to call the dispatch "
                "for",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder data sources"],
        operation_id="dispatch_public_builder_page_data_source",
        description=(
            "Dispatches the service of the related data_source and returns "
            "the result."
        ),
        request=DispatchDataSourceRequestSerializer,
        responses={
            404: get_error_schema(
                [
                    "ERROR_DATA_SOURCE_DOES_NOT_EXIST",
                    "ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED",
                    "ERROR_IN_DISPATCH_CONTEXT",
                    "ERROR_DATA_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            DataSourceDoesNotExist: ERROR_DATA_SOURCE_DOES_NOT_EXIST,
            DataSourceImproperlyConfigured: ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
            ServiceImproperlyConfigured: ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
            DataSourceRefinementForbidden: ERROR_DATA_SOURCE_REFINEMENT_FORBIDDEN,
            DoesNotExist: ERROR_DATA_DOES_NOT_EXIST,
        }
    )
    def post(self, request, data_source_id: int):
        """
        Call the given data_source related service dispatch method.
        """

        data_source = DataSourceHandler().get_data_source(data_source_id)

        serializer = DispatchDataSourceRequestSerializer(
            data=request.data, context={"data_source": data_source}
        )
        serializer.is_valid(raise_exception=True)

        # An `element` will be provided if we're dispatching a collection
        # element's data source with adhoc refinements.
        element = serializer.validated_data.get("data_source").get("element")

        dispatch_context = BuilderDispatchContext(
            request,
            data_source.page,
            element=element,
            only_expose_public_formula_fields=True,
        )
        response = DataSourceService().dispatch_data_source(
            request.user, data_source, dispatch_context
        )

        return Response(response)


class PublicDispatchDataSourcesView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The page we want to dispatch the data source for.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder data sources"],
        operation_id="dispatch_public_builder_page_data_sources",
        description="Dispatches the service of the related page data_sources",
        responses={
            404: get_error_schema(
                [
                    "ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED",
                    "ERROR_IN_DISPATCH_CONTEXT",
                    "ERROR_DATA_DOES_NOT_EXIST",
                    "ERROR_PAGE_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
            ServiceImproperlyConfigured: ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
            DoesNotExist: ERROR_DATA_DOES_NOT_EXIST,
        }
    )
    def post(self, request, page_id: str):
        """
        Call the given data_source related service dispatch method.
        """

        page = PageHandler().get_page(int(page_id))
        dispatch_context = BuilderDispatchContext(
            request, page, only_expose_public_formula_fields=True
        )
        service_contents = DataSourceService().dispatch_page_data_sources(
            request.user, page, dispatch_context
        )

        responses = {}

        for service_id, content in service_contents.items():
            if isinstance(content, Exception):
                _, error, detail = apply_exception_mapping(
                    {
                        DataSourceDoesNotExist: ERROR_DATA_SOURCE_DOES_NOT_EXIST,
                        DataSourceImproperlyConfigured: ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
                        ServiceImproperlyConfigured: ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
                        DoesNotExist: ERROR_DATA_DOES_NOT_EXIST,
                        PermissionException: ERROR_PERMISSION_DENIED,
                    },
                    content,
                    with_fallback=True,
                )
                responses[service_id] = {"_error": error, "detail": detail}
            else:
                responses[service_id] = content

        return Response(responses)
