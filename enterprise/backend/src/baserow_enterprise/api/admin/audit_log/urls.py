from django.urls import re_path

from baserow_enterprise.api.audit_log.views import (
    AsyncAuditLogExportView,
    AuditLogActionTypeFilterView,
    AuditLogUserFilterView,
    AuditLogView,
    AuditLogWorkspaceFilterView,
)

app_name = "baserow_enterprise.api.audit_log"

urlpatterns = [
    re_path(r"^$", AuditLogView.as_view(), name="list"),
    re_path(r"users/$", AuditLogUserFilterView.as_view(), name="users"),
    re_path(r"workspaces/$", AuditLogWorkspaceFilterView.as_view(), name="workspaces"),
    re_path(
        r"action-types/$", AuditLogActionTypeFilterView.as_view(), name="action_types"
    ),
    re_path(r"export/$", AsyncAuditLogExportView.as_view(), name="export"),
]
