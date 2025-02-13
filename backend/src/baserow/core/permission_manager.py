from typing import List

from django.contrib.auth import get_user_model

from baserow.core.handler import CoreHandler
from baserow.core.integrations.operations import (
    ListIntegrationsApplicationOperationType,
)
from baserow.core.models import Workspace, WorkspaceUser
from baserow.core.notifications.operations import (
    ClearNotificationsOperationType,
    ListNotificationsOperationType,
    MarkNotificationAsReadOperationType,
)
from baserow.core.user_sources.operations import (
    ListUserSourcesApplicationOperationType,
    LoginUserSourceOperationType,
)

from .exceptions import (
    IsNotAdminError,
    PermissionDenied,
    UserInvalidWorkspacePermissionsError,
    UserNotInWorkspace,
)
from .operations import (
    CreateInvitationsWorkspaceOperationType,
    CreateWorkspaceOperationType,
    DeleteWorkspaceInvitationOperationType,
    DeleteWorkspaceOperationType,
    DeleteWorkspaceUserOperationType,
    ListApplicationsWorkspaceOperationType,
    ListInvitationsWorkspaceOperationType,
    ListWorkspacesOperationType,
    ListWorkspaceUsersWorkspaceOperationType,
    ReadInvitationWorkspaceOperationType,
    UpdateSettingsOperationType,
    UpdateWorkspaceInvitationType,
    UpdateWorkspaceOperationType,
    UpdateWorkspaceUserOperationType,
)
from .registries import PermissionManagerType
from .subjects import AnonymousUserSubjectType, UserSubjectType

User = get_user_model()


class CorePermissionManagerType(PermissionManagerType):
    """
    Some operation are always allowed. This permission manager handle this case.
    """

    type = "core"
    supported_actor_types = [UserSubjectType.type]

    ALWAYS_ALLOWED_OPERATIONS = [
        ListWorkspacesOperationType.type,
    ]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        result = {}
        for check in checks:
            if check.operation_name in self.ALWAYS_ALLOWED_OPERATIONS:
                result[check] = True
        return result

    def get_permissions_object(self, actor, workspace=None):
        return self.ALWAYS_ALLOWED_OPERATIONS


class StaffOnlyPermissionManagerType(PermissionManagerType):
    """
    Checks if a user is_staff if the required operation is for staff only.
    """

    type = "staff"
    supported_actor_types = [UserSubjectType.type]

    STAFF_ONLY_OPERATIONS = [UpdateSettingsOperationType.type]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        result = {}
        for check in checks:
            if check.operation_name in self.STAFF_ONLY_OPERATIONS:
                if check.actor.is_staff:
                    result[check] = True
                else:
                    result[check] = IsNotAdminError(check.actor)

        return result

    def get_permissions_object(self, actor, workspace=None):
        return {
            "staff_only_operations": self.STAFF_ONLY_OPERATIONS,
            "is_staff": actor.is_staff,
        }


class AllowIfTemplatePermissionManagerType(PermissionManagerType):
    """
    Allows read operation on templates.
    """

    type = "allow_if_template"
    supported_actor_types = [UserSubjectType.type, AnonymousUserSubjectType.type]

    OPERATION_ALLOWED_ON_TEMPLATES = [
        ListApplicationsWorkspaceOperationType.type,
        ListIntegrationsApplicationOperationType.type,
        ListUserSourcesApplicationOperationType.type,
        LoginUserSourceOperationType.type,
    ]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        result = {}

        def has_template():
            return workspace and workspace.has_template()

        for check in checks:
            if (
                check.operation_name in self.OPERATION_ALLOWED_ON_TEMPLATES
                and has_template()
            ):
                result[check] = True

        return result

    def get_permissions_object(self, actor, workspace=None):
        return {
            "allowed_operations_on_templates": self.OPERATION_ALLOWED_ON_TEMPLATES,
            "workspace_template_ids": list(
                Workspace.objects.exclude(template=None).values_list("id", flat=True)
            ),
        }

    def filter_queryset(
        self,
        actor,
        operation_name,
        queryset,
        workspace=None,
    ):
        def has_template():
            return workspace and workspace.has_template()

        if operation_name in self.OPERATION_ALLOWED_ON_TEMPLATES and has_template():
            return queryset, True


class WorkspaceMemberOnlyPermissionManagerType(PermissionManagerType):
    """
    To be able to operate on a workspace, the user must at least belongs
    to that workspace.
    """

    type = "member"
    supported_actor_types = [UserSubjectType.type]
    actor_cache_key = "_in_workspace_cache"

    ALWAYS_ALLOWED_OPERATION_FOR_WORKSPACE_MEMBERS: List[str] = [
        ClearNotificationsOperationType.type,
        ListNotificationsOperationType.type,
        MarkNotificationAsReadOperationType.type,
    ]

    def is_actor_in_workspace(self, actor, workspace, callback=None):
        """
        Check is an actor is in a workspace. This method cache the result on the actor
        to prevent extra queries when used multiple times in a row. This is the case
        when we check the permission first then we filter the queryset for instance.

        :param actor: the actor to check.
        :param workspace: the workspace to check the actor belongs to.
        :param callback: an optional callback to check whether the actor belongs to the
          workspace. By default a query is made if not provided.
        """

        # Add cache to prevent another query during the filtering if any
        if not hasattr(actor, self.actor_cache_key):
            setattr(actor, self.actor_cache_key, {})

        if workspace.id not in getattr(actor, self.actor_cache_key):
            if callback is not None:
                in_workspace = callback()
            else:
                in_workspace = WorkspaceUser.objects.filter(
                    user_id=actor.id, workspace_id=workspace.id
                ).exists()

            getattr(actor, self.actor_cache_key)[workspace.id] = in_workspace

        return getattr(actor, self.actor_cache_key, {}).get(workspace.id, False)

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        if workspace is None:
            return {}

        users_to_query = {c.actor for c in checks}

        user_ids_in_workspace = set(
            CoreHandler()
            .get_workspace_users(workspace, users_to_query, include_trash=include_trash)
            .values_list("user_id", flat=True)
        )

        permission_by_check = {}

        def check_workspace(actor):
            return lambda: actor.id in user_ids_in_workspace

        for check in checks:
            if self.is_actor_in_workspace(
                check.actor, workspace, check_workspace(check.actor)
            ):
                if (
                    check.operation_name
                    in self.ALWAYS_ALLOWED_OPERATION_FOR_WORKSPACE_MEMBERS
                ):
                    permission_by_check[check] = True
            else:
                permission_by_check[check] = UserNotInWorkspace(check.actor, workspace)

        return permission_by_check

    def get_permissions_object(self, actor, workspace=None):
        """Check if the user is a member of this workspace"""

        if workspace and self.is_actor_in_workspace(actor, workspace):
            return None

        return False

    def filter_queryset(
        self,
        actor,
        operation_name,
        queryset,
        workspace=None,
    ):
        if workspace and not self.is_actor_in_workspace(actor, workspace):
            return queryset.none(), True


class BasicPermissionManagerType(PermissionManagerType):
    """
    This permission manager check if the user is an admin when the operation is admin
    only.
    """

    type = "basic"
    supported_actor_types = [UserSubjectType.type]

    ADMIN_ONLY_OPERATIONS = [
        ListInvitationsWorkspaceOperationType.type,
        CreateInvitationsWorkspaceOperationType.type,
        ReadInvitationWorkspaceOperationType.type,
        UpdateWorkspaceInvitationType.type,
        DeleteWorkspaceInvitationOperationType.type,
        ListWorkspaceUsersWorkspaceOperationType.type,
        UpdateWorkspaceOperationType.type,
        DeleteWorkspaceOperationType.type,
        UpdateWorkspaceUserOperationType.type,
        DeleteWorkspaceUserOperationType.type,
    ]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        if workspace is None:
            return {}

        permission_by_check = {}
        users_to_query = set()
        for check in checks:
            if check.operation_name in self.ADMIN_ONLY_OPERATIONS:
                users_to_query.add(check.actor)
            else:
                permission_by_check[check] = True

        user_permissions_by_id = dict(
            CoreHandler()
            .get_workspace_users(workspace, users_to_query, include_trash=include_trash)
            .values_list("user_id", "permissions")
        )

        for check in checks:
            if check.operation_name in self.ADMIN_ONLY_OPERATIONS:
                if user_permissions_by_id.get(check.actor.id, "MEMBER") == "ADMIN":
                    permission_by_check[check] = True
                else:
                    permission_by_check[check] = UserInvalidWorkspacePermissionsError(
                        check.actor, workspace, check.operation_name
                    )

        return permission_by_check

    def get_permissions_object(self, actor, workspace=None, include_trash=False):
        if workspace is None:
            return None

        if include_trash:
            manager = WorkspaceUser.objects_and_trash
        else:
            manager = WorkspaceUser.objects

        queryset = manager.filter(user_id=actor.id, workspace_id=workspace.id)

        try:
            # Check if the user is a member of this workspace
            workspace_user = queryset.get()
        except WorkspaceUser.DoesNotExist:
            return None

        return {
            "admin_only_operations": self.ADMIN_ONLY_OPERATIONS,
            "is_admin": "ADMIN" in workspace_user.permissions,
        }


class StaffOnlySettingOperationPermissionManagerType(PermissionManagerType):
    """
    A permission manager which uses Settings as a way to restrict non-staff
    from performing a specific operations.
    """

    type = "setting_operation"
    supported_actor_types = [UserSubjectType.type]

    # Maps `CoreOperationType` to `Setting` boolean field.
    STAFF_ONLY_SETTING_OPERATION_MAP = {
        CreateWorkspaceOperationType.type: "allow_global_workspace_creation"
    }

    def get_permitted_operations_for_settings(self) -> tuple[list, list]:
        """
        Responsible for returning a tuple, where the first item is a list of
        operations which are permitted because their connecting `Setting` value
        are set to `True`, and the second item is a list of operations which are
        always permitted to staff.

        The combination of these two lists, and the actor's `is_staff` value,
        are to allow the frontend and backend to determine if the actor has the
        necessary permissions for the operations in `STAFF_ONLY_SETTING_OPERATION_MAP`.
        """

        # The lists which contain our always allowed / staff only operations.
        always_allowed_operations = []
        staff_only_operations = []

        # Fetch the instance's Settings.
        settings = CoreHandler().get_settings()

        # Loop over each operation which currently has a Settings page setting.
        for (
            staff_operation_type,
            setting_key,
        ) in self.STAFF_ONLY_SETTING_OPERATION_MAP.items():
            if getattr(settings, setting_key, False):
                always_allowed_operations.append(staff_operation_type)
            else:
                staff_only_operations.append(staff_operation_type)
        return always_allowed_operations, staff_only_operations

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        (
            always_allowed_ops,
            staff_only_ops,
        ) = self.get_permitted_operations_for_settings()

        result = {}
        for check in checks:
            if check.operation_name in self.STAFF_ONLY_SETTING_OPERATION_MAP:
                if check.operation_name in always_allowed_ops or (
                    check.operation_name in staff_only_ops and check.actor.is_staff
                ):
                    result[check] = True
                else:
                    result[check] = PermissionDenied()

        return result

    def get_permissions_object(self, actor, workspace=None):
        (
            always_allowed_ops,
            staff_only_ops,
        ) = self.get_permitted_operations_for_settings()
        return {
            "staff_only_operations": staff_only_ops,
            "always_allowed_operations": always_allowed_ops,
        }
