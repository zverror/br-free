from typing import Dict

from django.db import transaction

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_body_custom_fields,
)
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.api.utils import (
    CustomFieldRegistryMappingSerializer,
    DiscriminatorCustomFieldsMappingSerializer,
    type_from_data_or_registry,
    validate_data_custom_fields,
)
from baserow.contrib.builder.api.data_sources.errors import (
    ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
)
from baserow.contrib.builder.api.elements.errors import ERROR_ELEMENT_DOES_NOT_EXIST
from baserow.contrib.builder.api.pages.errors import ERROR_PAGE_DOES_NOT_EXIST
from baserow.contrib.builder.api.workflow_actions.errors import (
    ERROR_DATA_DOES_NOT_EXIST,
    ERROR_WORKFLOW_ACTION_CANNOT_BE_DISPATCHED,
    ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST,
    ERROR_WORKFLOW_ACTION_FORM_DATA_INVALID,
    ERROR_WORKFLOW_ACTION_IMPROPERLY_CONFIGURED,
    ERROR_WORKFLOW_ACTION_NOT_IN_ELEMENT,
)
from baserow.contrib.builder.api.workflow_actions.serializers import (
    BuilderWorkflowActionSerializer,
    CreateBuilderWorkflowActionSerializer,
    OrderWorkflowActionsSerializer,
    UpdateBuilderWorkflowActionsSerializer,
)
from baserow.contrib.builder.data_providers.exceptions import (
    FormDataProviderChunkInvalidException,
)
from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.data_sources.exceptions import (
    DataSourceImproperlyConfigured,
)
from baserow.contrib.builder.elements.exceptions import ElementDoesNotExist
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.pages.exceptions import PageDoesNotExist
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.workflow_actions.exceptions import (
    BuilderWorkflowActionCannotBeDispatched,
    BuilderWorkflowActionImproperlyConfigured,
    WorkflowActionNotInElement,
)
from baserow.contrib.builder.workflow_actions.handler import (
    BuilderWorkflowActionHandler,
)
from baserow.contrib.builder.workflow_actions.registries import (
    builder_workflow_action_type_registry,
)
from baserow.contrib.builder.workflow_actions.service import (
    BuilderWorkflowActionService,
)
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.workflow_actions.exceptions import WorkflowActionDoesNotExist


class BuilderWorkflowActionsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates a workflow action for the builder page related to "
                "the provided value.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder workflow actions"],
        operation_id="create_builder_page_workflow_action",
        description="Creates a new builder workflow action",
        request=DiscriminatorCustomFieldsMappingSerializer(
            builder_workflow_action_type_registry,
            CreateBuilderWorkflowActionSerializer,
            request=True,
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                builder_workflow_action_type_registry, BuilderWorkflowActionSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_PAGE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
            ElementDoesNotExist: ERROR_ELEMENT_DOES_NOT_EXIST,
        }
    )
    @validate_body_custom_fields(
        builder_workflow_action_type_registry,
        base_serializer_class=CreateBuilderWorkflowActionSerializer,
    )
    def post(self, request, data: Dict, page_id: int):
        type_name = data.pop("type")
        workflow_action_type = builder_workflow_action_type_registry.get(type_name)
        page = PageHandler().get_page(page_id)

        workflow_action = BuilderWorkflowActionService().create_workflow_action(
            request.user, workflow_action_type, page, **data
        )

        serializer = builder_workflow_action_type_registry.get_serializer(
            workflow_action, BuilderWorkflowActionSerializer
        )

        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only the workflow actions of the page related to "
                "the provided Id.",
            )
        ],
        tags=["Builder workflow actions"],
        operation_id="list_builder_page_workflow_actions",
        description=(
            "Lists all the workflow actions of the page related to the provided parameter "
            "if the user has access to the related builder's workspace. "
            "If the workspace is related to a template, then this endpoint will be "
            "publicly accessible."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                builder_workflow_action_type_registry,
                BuilderWorkflowActionSerializer,
                many=True,
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
                workflow_action, BuilderWorkflowActionSerializer
            ).data
            for workflow_action in workflow_actions
        ]

        return Response(data)


class BuilderWorkflowActionView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workflow_action_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the workflow action",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder workflow actions"],
        operation_id="delete_builder_page_workflow_action",
        description="Deletes the workflow action related by the given id.",
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkflowActionDoesNotExist: ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST,
        }
    )
    def delete(self, request, workflow_action_id: int):
        workflow_action = BuilderWorkflowActionHandler().get_workflow_action(
            workflow_action_id
        )

        BuilderWorkflowActionService().delete_workflow_action(
            request.user, workflow_action
        )

        return Response(status=204)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workflow_action_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the workflow action",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder workflow actions"],
        operation_id="update_builder_page_workflow_action",
        description="Updates an existing builder workflow action.",
        request=CustomFieldRegistryMappingSerializer(
            builder_workflow_action_type_registry,
            UpdateBuilderWorkflowActionsSerializer,
            request=True,
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                builder_workflow_action_type_registry, BuilderWorkflowActionSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            WorkflowActionDoesNotExist: ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST,
        }
    )
    def patch(self, request, workflow_action_id: int):
        workflow_action = BuilderWorkflowActionHandler().get_workflow_action(
            workflow_action_id
        )
        workflow_action_type = type_from_data_or_registry(
            request.data, builder_workflow_action_type_registry, workflow_action
        )
        data = validate_data_custom_fields(
            workflow_action_type.type,
            builder_workflow_action_type_registry,
            request.data,
            base_serializer_class=UpdateBuilderWorkflowActionsSerializer,
            partial=True,
        )

        workflow_action_updated = BuilderWorkflowActionService().update_workflow_action(
            request.user, workflow_action, **data
        )

        serializer = builder_workflow_action_type_registry.get_serializer(
            workflow_action_updated, BuilderWorkflowActionSerializer
        )
        return Response(serializer.data)


class OrderBuilderWorkflowActionsView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The page the workflow actions belong to",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder workflow actions"],
        operation_id="order_builder_workflow_actions",
        description="Apply a new order to the workflow actions of a page",
        request=OrderWorkflowActionsSerializer,
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_PAGE_DOES_NOT_EXIST",
                    "ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST",
                    "ERROR_WORKFLOW_ACTION_NOT_IN_ELEMENT",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            PageDoesNotExist: ERROR_PAGE_DOES_NOT_EXIST,
            WorkflowActionDoesNotExist: ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST,
            WorkflowActionNotInElement: ERROR_WORKFLOW_ACTION_NOT_IN_ELEMENT,
        }
    )
    @validate_body(OrderWorkflowActionsSerializer)
    def post(self, request, data: Dict, page_id: int):
        page = PageHandler().get_page(page_id)
        element_id = data.get("element_id", None)
        element = (
            ElementHandler().get_element(element_id) if element_id is not None else None
        )

        BuilderWorkflowActionService().order_workflow_actions(
            request.user, page, data["workflow_action_ids"], element=element
        )

        return Response(status=204)


class DispatchBuilderWorkflowActionView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="workflow_action_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the workflow_action you want to "
                "call the dispatch for.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
        ],
        tags=["Builder workflow actions"],
        operation_id="dispatch_builder_page_workflow_action",
        description=(
            "Dispatches the service of the related workflow_action and returns "
            "the result."
        ),
        responses={
            400: get_error_schema(
                [
                    "ERROR_WORKFLOW_ACTION_CANNOT_BE_DISPATCHED",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            DoesNotExist: ERROR_DATA_DOES_NOT_EXIST,
            WorkflowActionDoesNotExist: ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST,
            ServiceImproperlyConfigured: ERROR_WORKFLOW_ACTION_IMPROPERLY_CONFIGURED,
            BuilderWorkflowActionCannotBeDispatched: ERROR_WORKFLOW_ACTION_CANNOT_BE_DISPATCHED,
            BuilderWorkflowActionImproperlyConfigured: ERROR_WORKFLOW_ACTION_IMPROPERLY_CONFIGURED,
            DataSourceImproperlyConfigured: ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED,
            FormDataProviderChunkInvalidException: ERROR_WORKFLOW_ACTION_FORM_DATA_INVALID,
        }
    )
    def post(self, request, workflow_action_id: int):
        """
        Call the given workflow_action related service dispatch method.
        """

        workflow_action = BuilderWorkflowActionHandler().get_workflow_action(
            workflow_action_id
        )

        dispatch_context = BuilderDispatchContext(
            request, workflow_action.page, workflow_action=workflow_action
        )

        response = BuilderWorkflowActionService().dispatch_action(
            request.user, workflow_action, dispatch_context  # type: ignore
        )

        if not isinstance(response, Response):
            response = Response(response)
        return response
