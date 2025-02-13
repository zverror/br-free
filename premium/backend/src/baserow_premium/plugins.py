from django.urls import include, path
from django.contrib.auth.models import AbstractUser
from baserow.core.models import Workspace

from baserow_premium.api import urls as api_urls
from baserow_premium.license.plugin import LicensePlugin

from baserow.core.registries import Plugin


class PremiumPlugin(Plugin):
    type = "premium"

    def get_api_urls(self):
        return [
            path("", include(api_urls, namespace=self.type)),
        ]

    def get_license_plugin(self, cache_queries: bool = False) -> LicensePlugin:
        return LicensePlugin(cache_queries)

    def user_has_feature(self, feature: str, user: AbstractUser, workspace: Workspace):
        return True

    def instance_has_feature(self, feature: str):
        return True

    def workspace_has_feature(self, feature: str, workspace: Workspace):
        return True

    def user_has_feature_instance_wide(self, feature: str, user: AbstractUser):
        return True

    def get_active_instance_wide_license_types(self, user: AbstractUser):
        from baserow_premium.license.registries import license_type_registry
        return [license_type_registry.get()]

    def get_active_per_workspace_licenses(self, user: AbstractUser):
        return {}
