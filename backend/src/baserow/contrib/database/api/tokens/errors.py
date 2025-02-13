from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND

ERROR_TOKEN_DOES_NOT_EXIST = (
    "ERROR_TOKEN_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The token does not exist.",
)
ERROR_NO_PERMISSION_TO_TABLE = (
    "ERROR_NO_PERMISSION_TO_TABLE",
    HTTP_401_UNAUTHORIZED,
    "The token does not have permissions to the table.",
)
