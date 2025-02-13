from baserow_premium.license.features import PREMIUM
from baserow_premium.license.models import License, LicenseUser
from baserow_premium.license.registries import LicenseType, SeatUsageSummary
from typing import Dict, Any

from baserow.core.models import User


class PremiumLicenseType(LicenseType):
    type = "premium"
    order = 10
    product_code = "premium"
    features = ["premium"]
    instance_wide = True
    seats_manually_assigned = False

    def get_seat_usage_summary(self, license_object: "License") -> Dict[str, Any]:
        return {
            "seats_taken": 0,
            "seats_limit": 999999,
            "seats_available": 999999,
        }

    def is_valid(self):
        return True

    def calculate_seats(self, license_object):
        return {
            "seats_taken": 0,
            "seats_limit": 999999,
            "free_users_count": 0,
            "num_active_users": 0,
            "invalid_users_count": 0
        }

    def handle_seat_overflow(self, seats_taken, license_object):
        return True

    def get_seat_usage_summary_for_workspace(self, workspace):
        return SeatUsageSummary(seats_taken=0, free_users_count=0, seats_available=999999)

    def get_seats_taken(self, workspace):
        return 0

    def get_seat_overflow_count(self, license_object):
        return 0
