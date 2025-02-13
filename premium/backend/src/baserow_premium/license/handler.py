import base64
import binascii
import hashlib
import json
from datetime import datetime, timezone
from os.path import dirname, join
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import DatabaseError, transaction
from django.db.models import Q

import requests
from baserow_premium.api.user.user_data_types import ActiveLicensesDataType
from baserow_premium.license.exceptions import (
    CantManuallyChangeSeatsError,
    InvalidLicenseError,
)
from baserow_premium.license.models import License
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from dateutil import parser
from loguru import logger
from requests.exceptions import RequestException
from rest_framework.status import HTTP_200_OK

from baserow.api.user.registries import user_data_registry
from baserow.core.exceptions import IsNotAdminError
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace
from baserow.core.registries import plugin_registry
from baserow.core.utils import get_baserow_saas_base_url
from baserow.ws.signals import broadcast_to_users

from .constants import (
    AUTHORITY_RESPONSE_DOES_NOT_EXIST,
    AUTHORITY_RESPONSE_INSTANCE_ID_MISMATCH,
    AUTHORITY_RESPONSE_INVALID,
    AUTHORITY_RESPONSE_UPDATE,
)
from .exceptions import (
    FeaturesNotAvailableError,
    LicenseAlreadyExistsError,
    LicenseAuthorityUnavailable,
    LicenseHasExpiredError,
    LicenseInstanceIdMismatchError,
    NoSeatsLeftInLicenseError,
    UnsupportedLicenseError,
    UserAlreadyOnLicenseError,
)
from .models import LicenseUser
from .registries import license_type_registry

User = get_user_model()


class LicenseHandler:
    @classmethod
    def raise_if_user_doesnt_have_feature_instance_wide(
        cls,
        feature: str,
        user: AbstractUser,
    ):
        """
        Raises the `FeaturesNotAvailableError` if the user does not have an
        active license granting them the provided feature.
        """

        if not cls.user_has_feature_instance_wide(feature, user):
            raise FeaturesNotAvailableError()

    @classmethod
    def raise_if_user_doesnt_have_feature(
        cls, feature: str, user: AbstractUser, workspace: Workspace
    ):
        """
        Checks if the provided user has the feature for a workspace or instance-wide.

        :param user: The user to check for feature access.
        :param workspace: The workspace that the user must have active premium for.
        :param feature: The feature the user must have.
        :raises FeaturesNotAvailableError: if the user does not have premium
            features from a license the provided workspace.
        """

        if not cls.user_has_feature(feature, user, workspace):
            raise FeaturesNotAvailableError()

    @classmethod
    def raise_if_workspace_doesnt_have_feature(cls, feature: str, workspace: Workspace):
        """
        Checks if the provided workspace has the feature for a workspace or
        instance-wide.

        :param feature: The feature the user must have.
        :param workspace: The workspace that the user must have active premium for.
        :raises FeaturesNotAvailableError: if the user does not have premium
            features from a license the provided workspace.
        """

        if not cls.workspace_has_feature(feature, workspace):
            raise FeaturesNotAvailableError()

    @classmethod
    def user_has_feature(cls, feature: str, user: AbstractUser, workspace: Workspace = None):
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
        return True

    @classmethod
    def workspace_has_feature(cls, feature: str, workspace: Workspace):
        """
        Checks if the Baserow workspace has a particular feature granted to the
        workspace itself.

        :param feature: The feature to check to see if active. Look for features.py
            files for these constant strings to use.
        :param workspace: The workspace to check.
        :return: True if the feature is enabled for the workspace.
        """

        # If the instance has the feature we don't have to check per workspace.
        if cls.instance_has_feature(feature):
            return True

        # Check all licenses for the workspace.
        for license_object in workspace.get_licenses():
            if license_object.is_active and license_object.has_feature(feature):
                return True

        return False

    @classmethod
    def user_has_feature_instance_wide(cls, feature: str, user: AbstractUser):
        """
        Checks if the user has a particular feature granted by an active instance wide
        license.

        :param feature: The feature to check to see if active. Look for features.py
            files for these constant strings to use.
        :param user: The user to check.
        :return: True if the user is allowed to use that feature, False otherwise.
        """

        # If the instance has the feature we don't have to check per user.
        if cls.instance_has_feature(feature):
            return True

        # Check all licenses for the user.
        for license_user in user.licenseuser_set.all():
            if (
                license_user.license.is_active
                and license_user.license.has_feature(feature)
                and license_user.license.is_instance_wide
            ):
                return True

        return False

    @classmethod
    def get_active_license_by_type(cls, user: AbstractUser, license_type: str) -> License:
        """
        Returns the active license of the provided type for the user.

        :param user: The user to get the license for.
        :param license_type: The license type that must be looked for.
        :raises UnsupportedLicenseError: When the license type is not supported.
        :raises LicenseHasExpiredError: When the license has expired.
        :return: The requested license if found.
        """

        license_type_object = license_type_registry.get(license_type)

        if not license_type_object.is_valid():
            raise UnsupportedLicenseError()

        try:
            license_object = (
                License.objects.get_by_type(license_type_object)
                .filter(licenseuser__user=user)
                .first()
            )
        except License.DoesNotExist:
            raise LicenseHasExpiredError()

        if not license_object.is_active:
            raise LicenseHasExpiredError()

        return license_object

    @classmethod
    def get_cached_active_license_by_type(
        cls, user: AbstractUser, license_type: str, license_id: int
    ) -> License:
        """
        Returns the active license of the provided type for the user.

        :param user: The user to get the license for.
        :param license_type: The license type that must be looked for.
        :param license_id: The id of the license we expect to find.
        :raises UnsupportedLicenseError: When the license type is not supported.
        :raises LicenseHasExpiredError: When the license has expired.
        :return: The requested license if found.
        """

        license_type_object = license_type_registry.get(license_type)

        if not license_type_object.is_valid():
            raise UnsupportedLicenseError()

        try:
            license_object = License.objects_with_cached_data.get(
                id=license_id,
                type=license_type_object.type,
                licenseuser__user_id=user.id,
            )
        except License.DoesNotExist:
            raise LicenseHasExpiredError()

        if not license_object.is_active:
            raise LicenseHasExpiredError()

        return license_object

    @classmethod
    def update_license_data(cls, license_object: License, data: Dict[str, Any]):
        """
        Updates the license data and saves the license.

        :param license_object: The license object that needs to be updated.
        :param data: The data that needs to be set.
        """

        license_object.raw = json.dumps(data)
        license_object.save()

    @classmethod
    def update_license(cls, requesting_user: User, license_object: License, raw: str):
        """
        Updates the license with the raw data.

        :param requesting_user: The user on whose behalf the license is updated.
        :param license_object: The license object that needs to be updated.
        :param raw: The raw license data.
        """

        if not requesting_user.is_staff:
            raise IsNotAdminError()

        data = cls.decode_license(raw)
        cls.update_license_data(license_object, data)

    @classmethod
    def get_license_data(cls, license_object: License) -> Dict[str, Any]:
        """
        Returns the license data as a dict.

        :param license_object: The license object to get the data from.
        :return: The license data.
        """

        return json.loads(license_object.raw)

    @classmethod
    def get_license_public_key(cls):
        """
        Loads the license public key from the settings and returns it.

        :return: The loaded public key.
        """

        public_key_path = join(dirname(__file__), "license_public_key.pem")

        if settings.LICENSE_PUBLIC_KEY_PATH:
            public_key_path = settings.LICENSE_PUBLIC_KEY_PATH

        with open(public_key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(), backend=default_backend()
            )

        return public_key

    @classmethod
    def get_license_signature(cls, raw: str) -> bytes:
        """
        Extracts the signature from the raw license data.

        :param raw: The raw license data.
        :raises InvalidLicenseError: When the signature could not be extracted.
        :return: The signature.
        """

        try:
            signature = raw.split("-")[0]
            return base64.b64decode(signature)
        except (IndexError, binascii.Error):
            raise InvalidLicenseError()

    @classmethod
    def get_license_hash(cls, raw: str) -> str:
        """
        Extracts the hash from the raw license data.

        :param raw: The raw license data.
        :raises InvalidLicenseError: When the hash could not be extracted.
        :return: The hash.
        """

        try:
            return raw.split("-")[1]
        except IndexError:
            raise InvalidLicenseError()

    @classmethod
    def get_license_payload(cls, raw: str) -> str:
        """
        Extracts the payload from the raw license data.

        :param raw: The raw license data.
        :raises InvalidLicenseError: When the payload could not be extracted.
        :return: The payload.
        """

        try:
            return raw.split("-")[2]
        except IndexError:
            raise InvalidLicenseError()

    @classmethod
    def get_license_instance_id(cls, data: Dict[str, Any]) -> str:
        """
        Extracts the instance id from the license data.

        :param data: The license data.
        :raises InvalidLicenseError: When the instance id could not be extracted.
        :return: The instance id.
        """

        try:
            return data["instance_id"]
        except KeyError:
            raise InvalidLicenseError("The license data does not contain an instance_id.")

    @classmethod
    def get_license_valid_from(cls, data: Dict[str, Any]) -> datetime:
        """
        Extracts the valid from timestamp from the license data.

        :param data: The license data.
        :raises InvalidLicenseError: When the valid from timestamp could not be
            extracted.
        :return: The valid from timestamp.
        """

        try:
            return parser.parse(data["valid_from"])
        except (KeyError, ValueError):
            raise InvalidLicenseError(
                "The license data does not contain a valid valid_from."
            )

    @classmethod
    def get_license_valid_through(cls, data: Dict[str, Any]) -> datetime:
        """
        Extracts the valid through timestamp from the license data.

        :param data: The license data.
        :raises InvalidLicenseError: When the valid through timestamp could not be
            extracted.
        :return: The valid through timestamp.
        """

        try:
            return parser.parse(data["valid_through"])
        except (KeyError, ValueError):
            raise InvalidLicenseError(
                "The license data does not contain a valid valid_through."
            )

    @classmethod
    def get_license_product_code(cls, data: Dict[str, Any]) -> str:
        """
        Extracts the product code from the license data.

        :param data: The license data.
        :raises InvalidLicenseError: When the product code could not be extracted.
        :return: The product code.
        """

        try:
            return data["product_code"]
        except KeyError:
            raise InvalidLicenseError(
                "The license data does not contain a product_code."
            )

    @classmethod
    def get_license_seats(cls, data: Dict[str, Any]) -> int:
        """
        Extracts the seats from the license data.

        :param data: The license data.
        :raises InvalidLicenseError: When the seats could not be extracted.
        :return: The seats.
        """

        try:
            return int(data["seats"])
        except (KeyError, ValueError):
            raise InvalidLicenseError("The license data does not contain valid seats.")

    @classmethod
    def calculate_license_hash(cls, payload: str) -> str:
        """
        Calculates the license hash based on the payload.

        :param payload: The payload to calculate the hash from.
        :return: The calculated hash.
        """

        hash_object = hashlib.sha256(payload.encode())
        return hash_object.hexdigest()

    @classmethod
    def verify_license_signature(cls, raw: str):
        """
        Verifies the license signature.

        :param raw: The raw license data.
        :raises InvalidLicenseError: When the signature is invalid.
        """
        return True

    @classmethod
    def check_license_instance_id(cls, data: Dict[str, Any]):
        """
        Checks if the license instance id matches the settings instance id.

        :param data: The license data.
        :raises LicenseInstanceIdMismatchError: When the instance id doesn't match.
        """
        return True

    @classmethod
    def check_license_validity_dates(cls, data: Dict[str, Any]):
        """
        Checks if the license is valid.

        :param data: The license data.
        :raises LicenseHasExpiredError: When the license has expired.
        """
        return True

    @classmethod
    def check_licenses(cls, license_objects: List[License]) -> List[License]:
        """
        Checks if the licenses are valid.

        :param license_objects: The licenses to check.
        :raises LicenseHasExpiredError: When the license has expired.
        :return: The licenses.
        """
        return license_objects

    @classmethod
    def decode_license(cls, raw: str) -> Dict[str, Any]:
        """
        Decodes the raw license data and checks if valid.

        :param raw: The raw license data.
        :raises InvalidLicenseError: When the license is invalid.
        :return: The decoded license data.
        """

        payload = cls.get_license_payload(raw)

        try:
            decoded = base64.b64decode(payload)
            return json.loads(decoded)
        except (json.JSONDecodeError, binascii.Error):
            raise InvalidLicenseError("The license payload is invalid.")

    @classmethod
    def register_license(
        cls,
        requesting_user: User,
        raw: str,
        send_update_to_users: bool = True,
    ) -> License:
        """
        Registers a new license. It checks if the license is valid and if the
        instance id matches.

        :param requesting_user: The user on whose behalf the license is registered.
        :param raw: The raw license data.
        :param send_update_to_users: Indicates if other users should receive a
            realtime update of the license.
        :raises IsNotAdminError: When the requesting user is not an admin.
        :raises LicenseAlreadyExistsError: When the license already exists.
        :raises LicenseInstanceIdMismatchError: When the instance id doesn't match.
        :raises LicenseHasExpiredError: When the license has expired.
        :return: The created license object.
        """

        if not requesting_user.is_staff:
            raise IsNotAdminError()

        data = cls.decode_license(raw)
        cls.check_license_instance_id(data)
        cls.check_license_validity_dates(data)

        license_type = license_type_registry.get_by_product_code(
            cls.get_license_product_code(data)
        )
        seats = cls.get_license_seats(data)

        try:
            existing_license = License.objects.get(
                type=license_type.type,
            )
            raise LicenseAlreadyExistsError(
                f"A license with type {license_type.type} already exists.",
                license_type.type,
            )
        except License.DoesNotExist:
            pass

        license_object = License.objects.create(
            raw=json.dumps(data),
            type=license_type.type,
            seats=seats,
        )

        if send_update_to_users:
            al = user_data_registry.get_by_type(ActiveLicensesDataType)

            transaction.on_commit(
                lambda: broadcast_to_users.delay(
                    [requesting_user.id],
                    al.realtime_message_to_enable_instancewide_license(
                        license_object.license_type
                    ),
                )
            )

        return license_object

    @classmethod
    def add_user_to_license(
        cls, requesting_user: User, license_object: License, user: User
    ) -> LicenseUser:
        """
        Adds the provided user to the provided license if there are any seats
        available.

        :param requesting_user: The user on whose behalf the user is added to the
            license.
        :param license_object: The license object where the user must be added to.
        :param user: The user that must be added to the license.
        :raises IsNotAdminError: When the requesting user is not an admin.
        :raises CantManuallyChangeSeatsError: When the license does not allow
            manually changing the seats.
        :raises UserAlreadyOnLicenseError: When the user already has a seat in the
            license.
        :raises NoSeatsLeftInLicenseError: When there are no seats left in the
            license.
        :return: The created license user object.
        """

        if not requesting_user.is_staff:
            raise IsNotAdminError()

        if not license_object.license_type.seats_manually_assigned:
            raise CantManuallyChangeSeatsError()

        if LicenseUser.objects.filter(license=license_object, user=user).exists():
            raise UserAlreadyOnLicenseError()

        if license_object.users.count() >= license_object.seats:
            raise NoSeatsLeftInLicenseError()

        al = user_data_registry.get_by_type(ActiveLicensesDataType)

        if license_object.is_active:
            transaction.on_commit(
                lambda: broadcast_to_users.delay(
                    [user.id],
                    al.realtime_message_to_enable_instancewide_license(
                        license_object.license_type
                    ),
                )
            )

        return LicenseUser.objects.create(license=license_object, user=user)

    @classmethod
    def remove_user_from_license(
        cls, requesting_user: User, license_object: License, user: User
    ):
        """
        Removes the provided user from the provided license if the user has a seat.

        :param requesting_user: The user on whose behalf the user is removed from the
            license.
        :param license_object: The license object where the user must be removed from.
        :param user: The user that must be removed from the license.
        """

        if not requesting_user.is_staff:
            raise IsNotAdminError()

        if not license_object.license_type.seats_manually_assigned:
            raise CantManuallyChangeSeatsError()

        LicenseUser.objects.filter(license=license_object, user=user).delete()

        al = user_data_registry.get_by_type(ActiveLicensesDataType)

        if license_object.is_active:
            transaction.on_commit(
                lambda: broadcast_to_users.delay(
                    [user.id],
                    al.realtime_message_to_disable_instancewide_license(
                        license_object.license_type
                    ),
                )
            )

    @classmethod
    def fill_remaining_seats_of_license(
        cls, requesting_user: User, license_object: License
    ) -> List[LicenseUser]:
        """
        Fills the remaining seats of the license with additional users.

        :param requesting_user: The user on whose behalf the request is made.
        :param license_object: The license object where the users must be added to.
        :return: A list of created license users.
        """

        if not requesting_user.is_staff:
            raise IsNotAdminError()

        if not license_object.license_type.seats_manually_assigned:
            raise CantManuallyChangeSeatsError()

        already_in_license = license_object.users.all().values_list(
            "user_id", flat=True
        )
        remaining_seats = license_object.seats - len(already_in_license)

        if remaining_seats > 0:
            users_to_add = User.objects.filter(~Q(id__in=already_in_license)).order_by(
                "id"
            )[:remaining_seats]
            user_licenses = [
                LicenseUser(license=license_object, user=user) for user in users_to_add
            ]
            LicenseUser.objects.bulk_create(user_licenses)

            if license_object.is_active:
                al = user_data_registry.get_by_type(ActiveLicensesDataType)

                transaction.on_commit(
                    lambda: broadcast_to_users.delay(
                        [user_license.user_id for user_license in user_licenses],
                        al.realtime_message_to_enable_instancewide_license(
                            license_object.license_type
                        ),
                    )
                )

            return user_licenses

        return []

    @classmethod
    def remove_all_users_from_license(
        cls, requesting_user: User, license_object: License
    ):
        """
        Removes all the users from a license. This will clear up all the seats.

        :param requesting_user: The user on whose behalf the users are removed.
        :param license_object: The license object where the users must be removed from.
        """

        if not requesting_user.is_staff:
            raise IsNotAdminError()

        if not license_object.license_type.seats_manually_assigned:
            raise CantManuallyChangeSeatsError()

        license_users = LicenseUser.objects.filter(license=license_object)
        license_user_ids = list(license_users.values_list("user_id", flat=True))
        license_users.delete()

        if license_object.is_active:
            al = user_data_registry.get_by_type(ActiveLicensesDataType)

            transaction.on_commit(
                lambda: broadcast_to_users.delay(
                    license_user_ids,
                    al.realtime_message_to_disable_instancewide_license(
                        license_object.license_type
                    ),
                )
            )

    @classmethod
    def raise_if_user_doesnt_have_feature(
        cls, feature: str, user: AbstractUser, workspace: Workspace = None
    ) -> None:
        return None

    @classmethod
    def raise_if_user_doesnt_have_feature_instance_wide(
        cls, feature: str, user: AbstractUser
    ) -> None:
        return None

    @classmethod
    def get_user_active_features(cls, user: AbstractUser) -> list:
        return []
