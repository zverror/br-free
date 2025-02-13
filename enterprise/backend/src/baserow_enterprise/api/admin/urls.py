from django.urls import include, path

from .audit_log import urls as audit_log_urls
from .auth_provider import urls as auth_provider_urls

app_name = "baserow_enterprise.api.admin"

urlpatterns = [
    path("auth-provider/", include(auth_provider_urls, namespace="auth_provider")),
    path("audit-log/", include(audit_log_urls, namespace="audit_log")),
]
