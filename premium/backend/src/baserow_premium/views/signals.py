from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.views.models import OWNERSHIP_TYPE_PERSONAL

from baserow.contrib.database.views import signals as view_signals
from baserow.contrib.database.views.models import OWNERSHIP_TYPE_COLLABORATIVE
from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Workspace

from .handler import delete_personal_views

User = get_user_model()


def check_premium_feature(sender, user, workspace, **kwargs):
    return True


def premium_check_ownership_type(user, workspace, ownership_type):
    return True


@receiver(view_signals.view_created)
def view_created(sender, view, user, **kwargs):
    workspace = view.table.database.workspace
    # premium_check_ownership_type(user, workspace, view.ownership_type)


def before_user_permanently_deleted(sender, instance, **kwargs):
    delete_personal_views(instance.id)


def connect_to_user_pre_delete_signal():
    pre_delete.connect(before_user_permanently_deleted, User)


__all__ = [
    "view_created",
    "connect_to_user_pre_delete_signal",
]
