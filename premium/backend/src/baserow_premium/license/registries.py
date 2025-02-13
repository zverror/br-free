import abc
import dataclasses
from typing import Dict, List, Optional

from baserow_premium.license.models import License

from baserow.core.models import Workspace
from baserow.core.registry import Instance, Registry


@dataclasses.dataclass
class SeatUsageSummary:
    seats_taken: int
    free_users_count: int
    num_users_with_highest_role: Dict[str, int] = dataclasses.field(
        default_factory=dict
    )
    highest_role_per_user_id: Dict[int, str] = dataclasses.field(default_factory=dict)


class LicenseType(abc.ABC, Instance):
    """
    A type of license that a user can install into Baserow to unlock extra
    functionality. This interface provides the ability for different types of licenses
    to have different behaviour by implementing the various hook methods differently.
    """

    features: List[str] = []
    """
    A list of features that this license type grants.
    """

    order: int
    """The higher the order the more features/more expensive the license is. Out of
    all instance-wide licenses a user might have, the one with the highest order will
    be shown as a badge in the top of the sidebar in the GUI. """

    instance_wide: bool = False
    """
    When true every user in the instance will have this license if it is active
    regardless of if they are added to a seat on the license or not.
    """

    seats_manually_assigned: bool = True

    def has_feature(self, feature: str):
        return feature in self.features

    def get_seat_usage_summary(
        self, license_object_of_this_type: License
    ) -> Optional[SeatUsageSummary]:
        """
        If it makes sense for a license to have seat usage then it should be calculated
        and returned herre.
        If it doesn't make sense for this license type then this should return None.
        """

        return None

    def get_seat_usage_summary_for_workspace(
        self, workspace: Workspace
    ) -> Optional[SeatUsageSummary]:
        """
        If it makes sense for a workspace to have seat usage, then this should return
        a summary of it. If it doesn't make sense for this license type then this
        should return None.
        """

        return None

    @abc.abstractmethod
    def handle_seat_overflow(self, seats_taken: int, license_object: License):
        pass


class LicenseTypeRegistry(Registry):
    name = "license_type"

    def get(self, *args, **kwargs):
        from .license_types import PremiumLicenseType
        return PremiumLicenseType()

    def user_has_feature(self, feature: str, user: AbstractUser, workspace: Workspace):
        return True

    def instance_has_feature(self, feature: str, instance_id: int):
        return True

    def get_active_instance_wide_license_types(self, user: AbstractUser):
        return [self.get()]

    def get_active_per_workspace_licenses(self, user: AbstractUser):
        return {}

license_type_registry = LicenseTypeRegistry()
