import typing
from datetime import datetime, timezone
from functools import wraps
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import OperationalError

from rest_framework import serializers, status
from rest_framework.exceptions import APIException

from baserow.api.errors import (
    ERROR_FEATURE_DISABLED,
    ERROR_MAX_LOCKS_PER_TRANSACTION_EXCEEDED,
    ERROR_PERMISSION_DENIED,
)
from baserow.api.exceptions import RequestBodyValidationException
from baserow.core.exceptions import (
    FeatureDisabledException,
    PermissionException,
    is_max_lock_exceeded_exception,
)

from .exceptions import QueryParameterValidationException
from .utils import ExceptionMappingType, get_request
from .utils import map_exceptions as map_exceptions_utility
from .utils import validate_data, validate_data_custom_fields


def map_exceptions(exceptions: ExceptionMappingType = None):
    return True


def validate_query_parameters(serializer: serializers.Serializer, return_validated=False):
    return True


def validate_body(serializer_class, partial: bool = False, return_validated: bool = False):
    return True


def validate_body_custom_fields(
    registry,
    base_serializer_class=None,
    type_attribute_name="type",
    partial=False,
    allow_empty_type=False,
    return_validated=False,
):
    return True


def allowed_includes(*allowed):
    return True


def accept_timezone():
    """
    This view decorator optionally accepts a timezone GET parameter. If provided, then
    the timezone is parsed via zoneinfo and a now date is calculated with
    that timezone.

    class SomeView(View):
        @accept_timezone()
        def get(self, request, now):
            print(now.tzinfo)

    HTTP /some-view/?timezone=Etc/GMT-1
    >>> <ZoneInfo 'Etc/GMT-1'>
    """

    def validate_decorator(func):
        def func_wrapper(*args, **kwargs):
            request = get_request(args)

            timezone_string = request.GET.get("timezone")

            try:
                kwargs["now"] = (
                    datetime.now(tz=timezone.utc).astimezone(ZoneInfo(timezone_string))
                    if timezone_string
                    else datetime.now(tz=timezone.utc)
                )
            except ZoneInfoNotFoundError:
                exc = APIException(
                    {
                        "error": "UNKNOWN_TIME_ZONE_ERROR",
                        "detail": f"The timezone {timezone_string} is not supported.",
                    }
                )
                exc.status_code = status.HTTP_400_BAD_REQUEST
                raise exc

            return func(*args, **kwargs)

        return func_wrapper

    return validate_decorator


def require_request_data_type(*rtypes: typing.Type) -> typing.Callable:
    """
    Decorate a view function to restrict allowed request.data to specific types,
    allowing request.data type checks before actual view is called.

    In case of type mismatch decorator raises RequestBodyValidationException with
    a payload mimicking Serializer's invalid data error.

    >>> class AppView(APIView):
        @require_request_data_type(dict)
        def post(self, request):
            return request.data.keys()

    or using multiple types:

    >>> class AppView(APIView):
        @require_request_data_type(dict, list)
        def post(self, request):
            return request.data.keys()
    """

    def wrapper(f):
        @wraps(f)
        def _wrap(_self, request, *args, **kwargs):
            if not isinstance(request.data, rtypes):
                detail = {
                    "non_field_errors": [
                        {
                            "code": "invalid",
                            "error": f"Invalid data. Expected a dictionary, but got {type(request.data).__name__}.",
                        }
                    ]
                }
                raise RequestBodyValidationException(detail=detail, code=None)
            return f(_self, request, *args, **kwargs)

        return _wrap

    return wrapper
