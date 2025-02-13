from django.contrib.auth.models import AbstractUser
from baserow.core.models import Workspace


class LicenseHandler:
    @classmethod
    def raise_if_user_doesnt_have_feature_instance_wide(
        cls,
        feature: str,
        user: AbstractUser,
    ):
        """
        Always returns True to enable premium features for all users.
        """
        return True

    @classmethod
    def raise_if_user_doesnt_have_feature(
        cls, feature: str, user: AbstractUser, workspace: Workspace
    ):
        """
        Always returns True to enable premium features for all users.
        """
        return True

    @classmethod
    def raise_if_workspace_doesnt_have_feature(cls, feature: str, workspace: Workspace):
        """
        Always returns True to enable premium features for all workspaces.
        """
        return True

    @classmethod
    def user_has_feature(cls, feature: str, user: AbstractUser, workspace: Workspace) -> bool:
        """
        Always returns True to enable premium features for all users.
        """
        return True

    @classmethod
    def user_has_feature_instance_wide(cls, feature: str, user: AbstractUser) -> bool:
        """
        Always returns True to enable premium features for all users.
        """
        return True
