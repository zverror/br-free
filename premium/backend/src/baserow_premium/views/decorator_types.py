from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler

from baserow.contrib.database.views.registries import DecoratorType


class PremiumDecoratorType(DecoratorType):
    def before_create_decoration(self, view, user):
        return True

    def before_update_decoration(self, view, user):
        return True


class LeftBorderColorDecoratorType(PremiumDecoratorType):
    type = "left_border_color"


class BackgroundColorDecoratorType(PremiumDecoratorType):
    type = "background_color"
