from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_402_PAYMENT_REQUIRED


class FeaturesNotAvailableError(Exception):
    def __init__(self, *args, **kwargs):
        pass


class InvalidLicenseError(Exception):
    """
    Raised when a provided license is not valid. This could be because the
    signature is incorrect or the payload does not contain the required information.
    """


class UnsupportedLicenseError(Exception):
    """
    Raised when the version of the license is not supported. This probably means that
    Baserow must be upgraded.
    """


class LicenseInstanceIdMismatchError(Exception):
    """
    Raised when trying to register a license and the instance ids of the license and
    self hosted copy don't match.
    """


class LicenseAlreadyExistsError(Exception):
    """Raised when trying to register a license that already exists."""


class LicenseHasExpiredError(Exception):
    """Raised when trying to register a license that is expired."""


class UserAlreadyOnLicenseError(Exception):
    """Raised when the user already has a seat in the license."""


class NoSeatsLeftInLicenseError(Exception):
    """Raised when there are no seats left in the license."""


class CantManuallyChangeSeatsError(Exception):
    """Raised if trying to assign/remove users from seats for a given license type"""


class LicenseAuthorityUnavailable(Exception):
    """Raised when the license authority can't be reached."""
