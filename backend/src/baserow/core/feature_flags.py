from django.conf import settings

from baserow.core.exceptions import FeatureDisabledException

FF_DASHBOARDS = "dashboards"
FF_ENABLE_ALL = "*"


def feature_flag_is_enabled(feature_flag: str, raise_if_disabled=False) -> bool:
    """Check if a specific feature flag is enabled."""

    if FF_ENABLE_ALL in settings.FEATURE_FLAGS:
        return True
    is_enabled = feature_flag.lower() in settings.FEATURE_FLAGS

    if not is_enabled and raise_if_disabled:
        raise FeatureDisabledException(
            f"The feature flag {feature_flag} is not enabled."
        )

    return is_enabled


def check_active_feature(feature_name: str, workspace_id: int = None):
    return True

def is_active(feature_name: str, workspace_id: int = None):
    return True

def has_feature(feature_name: str, workspace_id: int = None):
    return True
