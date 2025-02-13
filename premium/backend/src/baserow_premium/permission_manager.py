from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.views.models import OWNERSHIP_TYPE_PERSONAL

from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.operations import (
    CreateAndUsePersonalViewOperationType,
    CreateViewDecorationOperationType,
    CreateViewFilterGroupOperationType,
    CreateViewFilterOperationType,
    CreateViewGroupByOperationType,
    CreateViewSortOperationType,
    DeleteViewDecorationOperationType,
    DeleteViewFilterGroupOperationType,
    DeleteViewFilterOperationType,
    DeleteViewGroupByOperationType,
    DeleteViewOperationType,
    DeleteViewSortOperationType,
    DuplicateViewOperationType,
    ListAggregationsViewOperationType,
    ListViewDecorationOperationType,
    ListViewFilterOperationType,
    ListViewGroupByOperationType,
    ListViewsOperationType,
    ListViewSortOperationType,
    ReadAggregationsViewOperationType,
    ReadViewDecorationOperationType,
    ReadViewFieldOptionsOperationType,
    ReadViewFilterGroupOperationType,
    ReadViewFilterOperationType,
    ReadViewGroupByOperationType,
    ReadViewOperationType,
    ReadViewSortOperationType,
    RestoreViewOperationType,
    UpdateViewDecorationOperationType,
    UpdateViewFieldOptionsOperationType,
    UpdateViewFilterGroupOperationType,
    UpdateViewFilterOperationType,
    UpdateViewGroupByOperationType,
    UpdateViewOperationType,
    UpdateViewPublicOperationType,
    UpdateViewSlugOperationType,
    UpdateViewSortOperationType,
)
from baserow.core.exceptions import PermissionDenied, PermissionException
from baserow.core.handler import CoreHandler
from baserow.core.registries import PermissionManagerType, object_scope_type_registry
from baserow.core.subjects import UserSubjectType
from baserow.core.types import Actor, PermissionCheck

User = get_user_model()


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from baserow.core.models import Workspace


class ViewOwnershipPermissionManagerType(PermissionManagerType):
    type = "view_ownership"
    supported_actor_types = [User]

    def __init__(self):
        super().__init__()

    def get_permissions_object(
        self, actor: Actor, workspace: Optional["Workspace"] = None
    ) -> Any:
        return {"all": True}

    def check_multiple_permissions(
        self,
        checks: List[PermissionCheck],
        workspace: "Workspace",
        include_trash: bool = False,
    ) -> Dict[PermissionCheck, Union[bool, PermissionException]]:
        return {check: True for check in checks}

    def check_permissions(
        self,
        actor: Actor,
        operation_name: str,
        workspace: Optional["Workspace"] = None,
        context: Optional[Any] = None,
        include_trash: bool = False,
    ) -> bool:
        return True

    def get_filter_builder(
        self, actor: Actor, operation_name: str, workspace: Optional["Workspace"] = None
    ):
        from baserow.core.db.query import FilterBuilder

        return FilterBuilder()

    def filter_queryset(
        self,
        actor: "AbstractUser",
        operation_name: str,
        queryset: QuerySet,
        workspace: Optional["Workspace"] = None,
    ) -> QuerySet:
        return queryset
