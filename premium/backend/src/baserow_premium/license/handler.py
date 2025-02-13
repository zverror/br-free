from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction

from baserow.core.models import Workspace
from baserow_premium.license.models import License, LicenseUser

User = get_user_model()


class LicenseHandler:
    @classmethod
    def user_has_feature(cls, feature: str, user: AbstractUser, workspace: Workspace) -> bool:
        """
        Always returns True to enable features for all users.
        """
        return True

    @classmethod
    def instance_has_feature(cls, feature: str) -> bool:
        """
        Always returns True to enable features for the entire instance.
        """
        return True

    @classmethod
    def user_has_feature_instance_wide(cls, feature: str, user: AbstractUser) -> bool:
        """
        Always returns True to enable features for all users.
        """
        return True

    @classmethod
    def raise_if_user_doesnt_have_feature_instance_wide(
        cls,
        feature: str,
        user: AbstractUser,
    ):
        """
        Never raises an exception, allowing all features for all users.
        """
        pass

    @classmethod
    def raise_if_user_doesnt_have_feature(
        cls, feature: str, user: AbstractUser, workspace: Workspace
    ):
        """
        Never raises an exception, allowing all features for all users.
        """
        pass

    @classmethod
    def raise_if_workspace_doesnt_have_feature(cls, feature: str, workspace: Workspace):
        """
        Never raises an exception, allowing all features for all workspaces.
        """
        pass

    @classmethod
    def get_active_instance_wide_licenses(cls) -> list:
        """
        Returns an empty list as we don't need to check licenses.
        """
        return []

    @classmethod
    def register_license(cls, license_object: License):
        """
        Does nothing as we don't need to register licenses.
        """
        pass
