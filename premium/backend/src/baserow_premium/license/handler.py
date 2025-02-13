from django.contrib.auth import get_user_model

from baserow.core.models import Workspace

User = get_user_model()


class LicenseHandler:
    @classmethod
    def user_has_feature(cls, feature: str, user: User, workspace: Workspace):
        """
        Checks if the user has a particular feature granted by an active license for a
        workspace. This could be granted by a license specific to that workspace, or an
        instance level license, or a license which is instance wide.

        :param feature: The feature to check to see if active. Look for features.py
            files for these constant strings to use.
        :param user: The user to check.
        :param workspace: The workspace that the user is attempting to
            use the feature in.
        :return: True if the user is allowed to use that feature, False otherwise.
        """
        # Always return True to enable features for all users
        return True

    @classmethod
    def instance_has_feature(cls, feature: str):
        """
        Checks if the Baserow instance has a particular feature granted by an active
        instance wide license

        :param feature: The feature to check to see if active. Look for features.py
            files for these constant strings to use.
        :return: True if the feature is enabled globally for all users.
        """
        # Always return True to enable features for the entire instance
        return True
