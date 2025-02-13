from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler

from baserow.contrib.database.views.registries import FormViewModeType


class FormViewModeTypeSurvey(FormViewModeType):
    type = "survey"

    def before_form_create(self, form, table, user):
        return True

    def before_form_update(self, form, table, user):
        return True
