from copy import deepcopy
from typing import Dict, List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.base import ModelBase

from loguru import logger
from rest_framework import serializers

from baserow.api.search.serializers import SearchQueryParamSerializer
from baserow.api.utils import get_serializer_class
from baserow.contrib.database.api.rows.fields import UserFieldNamesField
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.models import RowHistory
from baserow.contrib.database.rows.registries import row_metadata_registry


class RowSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "order",
        )
        extra_kwargs = {"id": {"read_only": True}, "order": {"read_only": True}}


def serialize_rows_for_response(rows, model, user_field_names=False, many=True):
    return get_row_serializer_class(
        model,
        RowSerializer,
        is_response=True,
        user_field_names=user_field_names,
    )(rows, many=many).data


def is_read_only(value):
    raise ValidationError(message="This field is read_only", code="read_only")


def get_row_serializer_class(
    model,
    base_class=None,
    is_response=False,
    field_ids=None,
    field_names_to_include=None,
    user_field_names=False,
    field_kwargs=None,
    include_id=False,
    required_fields=None,
):
    """
    Generates a Django rest framework model serializer based on the available fields
    that belong to this model. For each table field, used to generate this serializer,
    a serializer field will be added via the `get_serializer_field` method of the field
    type.

    :param model: The model for which to generate a serializer.
    :type model: Model
    :param base_class: The base serializer class that will be extended when
        generating the serializer. By default this is a regular ModelSerializer.
    :type base_class: ModelSerializer
    :param is_response: Indicates if the serializer is going to be used for a response
        instead of handling input data. If that is the case other serializer fields
        might be used depending on the field type.
    :type is_response: bool
    :param field_ids: If provided only the field ids in the list will be
        included in the serializer. By default all the fields of the model are going
        to be included. Note that the field id must exist in the model in
        order to work.
    :type field_ids: Optional[Iterable[int]]
    :param field_names_to_include: If provided only the field names in the list will be
        included in the serializer. By default all the fields of the model are going
        to be included. Note that the field name must exist in the model in
        order to work.
    :type field_names_to_include: list or None
    :param field_kwargs: A dict containing additional kwargs per field. The key must
        be the field name and the value a dict containing the kwargs.
    :type field_kwargs: dict
    :param include_id: Whether the generated serializer should contain the id field
    :type include_id: bool
    :param required_fields: List of field names that should be present even when
        performing partial validation.
    :type required_fields: list[str]
    :return: The generated serializer.
    :rtype: ModelSerializer
    """

    if not field_kwargs:
        field_kwargs = {}

    field_objects = model._field_objects
    field_names = []
    field_overrides = {}

    for field in field_objects.values():
        field_id_matches = field_ids is None or (field["field"].id in field_ids)
        field_name_matches = field_names_to_include is None or (
            field["field"].name in field_names_to_include
        )

        if field_id_matches and field_name_matches:
            name = field["field"].name if user_field_names else field["name"]
            extra_kwargs = field_kwargs.get(field["name"], {})
            # If the field is configured to be read-only, then we want the API to
            # respond with an error if the key is provided. It should be possible to
            # update the cell value via handlers because the value is then managed by
            # something internally.
            if field["field"].read_only:
                if "validators" not in extra_kwargs:
                    extra_kwargs["validators"] = []
                extra_kwargs["validators"].append(is_read_only)
                extra_kwargs.pop("required", None)

            if field["name"] != name:
                # If we are building a serializer with names which do not match the
                # database column then we have to set the source.
                # We don't always do this if user_field_names is True as a user could
                # have named fields "field_1" etc, in which case if we also set source
                # DRF would crash as it only wants source set if the db column differs.
                extra_kwargs["source"] = field["name"]

            if is_response:
                serializer = field["type"].get_response_serializer_field(
                    field["field"], **extra_kwargs
                )
            else:
                serializer = field["type"].get_serializer_field(
                    field["field"], **extra_kwargs
                )
            field_overrides[name] = serializer
            field_names.append(name)

    if include_id:
        field_names.append("id")
        field_overrides["id"] = serializers.IntegerField()

    return get_serializer_class(
        model,
        field_names,
        field_overrides,
        base_class,
        required_fields=required_fields,
    )


def get_batch_row_serializer_class(row_serializer_class):
    class_name = "BatchRowSerializer"

    def validate(self, value):
        if "items" not in value:
            raise serializers.ValidationError({"items": "This field is required."})
        return value

    fields = {
        "items": serializers.ListField(
            child=row_serializer_class(),
            min_length=1,
            max_length=settings.BATCH_ROWS_SIZE_LIMIT,
        ),
        "validate": validate,
    }

    class_object = type(class_name, (serializers.Serializer,), fields)
    return class_object


class BatchDeleteRowsSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=settings.BATCH_ROWS_SIZE_LIMIT,
    )


def get_example_row_serializer_class(example_type="get", user_field_names=False):
    """
    Generates a serializer containing a field for each field type. It is only used for
    example purposes in the openapi documentation.

    :param example_type: Sets various parameters. Can be get, post, patch.
    :type example_type: str
    :param user_field_names: Whether this example serializer help text should indicate
        the fields names can be switched using the `user_field_names` GET parameter.
    :type user_field_names: bool
    :return: Generated serializer containing a field for each field type.
    :rtype: Serializer
    """

    config = {
        "get": {
            "class_name": "ExampleRowResponseSerializer",
            "add_id": True,
            "add_order": True,
            "read_only_fields": True,
        },
        "post": {
            "class_name": "ExampleRowRequestSerializer",
            "add_id": False,
            "add_order": False,
            "read_only_fields": False,
        },
        "patch": {
            "class_name": "ExampleUpdateRowRequestSerializer",
            "add_id": False,
            "add_order": False,
            "read_only_fields": False,
        },
        "patch_batch": {
            "class_name": "ExampleBatchUpdateRowRequestSerializer",
            "add_id": True,
            "add_order": False,
            "read_only_fields": False,
        },
    }

    class_name = config[example_type]["class_name"]
    add_id = config[example_type]["add_id"]
    add_order = config[example_type]["add_order"]
    add_readonly_fields = config[example_type]["read_only_fields"]
    is_response_example = add_readonly_fields

    if not hasattr(get_example_row_serializer_class, "cache"):
        get_example_row_serializer_class.cache = {}

    if user_field_names:
        class_name += "WithUserFieldNames"

    if class_name in get_example_row_serializer_class.cache:
        return get_example_row_serializer_class.cache[class_name]

    fields = {}

    if add_id:
        fields["id"] = serializers.IntegerField(
            read_only=False, help_text="The unique identifier of the row in the table."
        )

    if add_order:
        fields["order"] = serializers.DecimalField(
            max_digits=40,
            decimal_places=20,
            required=False,
            help_text="Indicates the position of the row, lowest first and highest "
            "last.",
        )

    field_types = field_type_registry.registry.values()

    if len(field_types) == 0:
        logger.warning(
            "The field types appear to be empty. This module is probably "
            "imported before the fields have been registered."
        )

    optional_user_field_names_info = ""
    if user_field_names:
        optional_user_field_names_info = (
            " If the GET parameter user_field_names is provided and its value is "
            "one of the following: `y`, `yes`, `true`, `t`, `on`, `1`, or empty, "
            "then the key will instead be the actual name of the field."
        )

    for i, field_type in enumerate(field_types):
        if field_type.read_only and not add_readonly_fields:
            continue
        instance = field_type.model_class()
        kwargs = {
            "help_text": f"This field represents the `{field_type.type}` field. The "
            f"number in field_{i + 1} is in a normal request or response "
            f"the id of the field.{optional_user_field_names_info} "
            f"{field_type.get_serializer_help_text(instance)}"
        }
        get_field_method = (
            "get_response_serializer_field"
            if is_response_example
            else "get_serializer_field"
        )
        serializer_field = getattr(field_type, get_field_method)(instance, **kwargs)
        fields[f"field_{i + 1}"] = serializer_field

    class_object = type(class_name, (serializers.Serializer,), fields)
    get_example_row_serializer_class.cache[class_name] = class_object

    return class_object


def get_example_row_metadata_field_serializer():
    """
    Generates a serializer containing a field for each row metadata type which
    represents the metadata for a single row.
    It is only used for example purposes in the openapi documentation.

    :return: Generated serializer for a single rows metadata
    :rtype: Serializer
    """

    metadata_types = row_metadata_registry.get_all()

    if len(metadata_types) == 0:
        return None

    fields = {}
    for metadata_type in metadata_types:
        fields[metadata_type.type] = metadata_type.get_example_serializer_field()

    per_row_serializer = type(
        "RowMetadataSerializer", (serializers.Serializer,), fields
    )()
    return serializers.DictField(
        child=per_row_serializer,
        required=False,
        help_text="An object keyed by row id with a value being an object containing "
        "additional metadata about that row. A row might not have metadata and will "
        "not be present as a key if so.",
    )


def remap_serialized_rows_to_user_field_names(
    serialized_rows: List[Dict], model: ModelBase
) -> List[Dict]:
    """
    Remap the values of rows from field ids to the user defined field names.

    :param serialized_rows: The rows whose fields to remap.
    :param model: The model for which to generate a serializer.
    """

    return [
        remap_serialized_row_to_user_field_names(row, model) for row in serialized_rows
    ]


def remap_serialized_row_to_user_field_names(
    serialized_row: Dict, model: ModelBase
) -> Dict:
    """
    Remap the values of a row from field ids to the user defined field names.

    :param serialized_row: The row whose fields to remap.
    :param model: The model for which to generate a serializer.
    """

    new_row = deepcopy(serialized_row)
    for field_id, field_object in model._field_objects.items():
        name = f"field_{field_id}"
        if name in new_row:
            new_name = field_object["field"].name
            new_row[new_name] = new_row.pop(name)
    return new_row


class UserFieldNamesSerializer(serializers.Serializer):
    user_field_names = UserFieldNamesField(
        required=False, default=False, allow_null=True
    )


class MoveRowQueryParamsSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(required=False)


class CreateRowQueryParamsSerializer(serializers.Serializer):
    before = serializers.IntegerField(required=False)


class BatchCreateRowsQueryParamsSerializer(serializers.Serializer):
    before = serializers.IntegerField(required=False)


class ListRowsQueryParamsSerializer(
    SearchQueryParamSerializer, UserFieldNamesSerializer
):
    order_by = serializers.CharField(required=False)
    include = serializers.CharField(required=False)
    exclude = serializers.CharField(required=False)
    filter_type = serializers.CharField(required=False, default="")
    view_id = serializers.IntegerField(required=False)


class BatchUpdateRowsSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=RowSerializer(),
        min_length=1,
        max_length=settings.BATCH_ROWS_SIZE_LIMIT,
    )


def get_example_batch_rows_serializer_class(example_type="get", user_field_names=False):
    config = {
        "get": {
            "class_name": "ExampleBatchRowsResponseSerializer",
        },
        "post": {
            "class_name": "ExampleBatchRowsRequestSerializer",
        },
        "patch_batch": {"class_name": "ExampleBatchUpdateRowsRequestSerializer"},
    }
    class_name = config[example_type]["class_name"]

    if not hasattr(get_example_batch_rows_serializer_class, "cache"):
        get_example_batch_rows_serializer_class.cache = {}

    if class_name in get_example_batch_rows_serializer_class.cache:
        return get_example_batch_rows_serializer_class.cache[class_name]

    fields = {
        "items": serializers.ListField(
            child=get_example_row_serializer_class(
                example_type=example_type, user_field_names=user_field_names
            )(),
            min_length=1,
            max_length=settings.BATCH_ROWS_SIZE_LIMIT,
        )
    }
    class_object = type(class_name, (serializers.Serializer,), fields)
    get_example_batch_rows_serializer_class.cache[class_name] = class_object
    return class_object


class GetRowAdjacentSerializer(
    SearchQueryParamSerializer, UserFieldNamesSerializer, serializers.Serializer
):
    previous = serializers.BooleanField(required=False, default=False)
    view_id = serializers.IntegerField(required=False)


class RowHistoryUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        source="user_id",
        help_text="The id of the user.",
    )
    name = serializers.CharField(
        source="user_name",
        help_text="The first name of the user.",
    )


class RowHistorySerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(
        source="action_timestamp",
        help_text="The timestamp of the action that was performed.",
    )
    user = RowHistoryUserSerializer(
        source="*", help_text="The user that performed the action."
    )
    before = serializers.JSONField(
        source="before_values",
        help_text="The mapping between field_ids and values for the row before the action was performed.",
    )
    after = serializers.JSONField(
        source="after_values",
        help_text="The mapping between field_ids and values for the row after the action was performed.",
    )

    class Meta:
        model = RowHistory
        fields = [
            "id",
            "action_type",
            "user",
            "timestamp",
            "before",
            "after",
            "fields_metadata",
        ]
