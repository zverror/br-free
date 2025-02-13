from collections.abc import Mapping

from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from baserow.api.mixins import UnknownFieldRaisesExceptionSerializerMixin
from baserow.api.user_files.serializers import UserFileField
from baserow.contrib.builder.api.validators import image_file_validation
from baserow.contrib.builder.api.workflow_actions.serializers import (
    BuilderWorkflowActionSerializer,
)
from baserow.contrib.builder.elements.models import (
    ChoiceElementOption,
    CollectionElementPropertyOptions,
    CollectionField,
    Element,
)
from baserow.contrib.builder.elements.registries import (
    collection_field_type_registry,
    element_type_registry,
)
from baserow.contrib.builder.elements.types import ElementsAndWorkflowActions
from baserow.contrib.builder.workflow_actions.registries import (
    builder_workflow_action_type_registry,
)
from baserow.core.exceptions import InstanceTypeDoesNotExist
from baserow.core.formula.serializers import FormulaSerializerField


class ElementSerializer(serializers.ModelSerializer):
    """
    Basic element serializer mostly for returned values.

    👉 Mind to update the
    baserow.contrib.builder.api.domains.serializer.PublicElementSerializer
    when you update this one.
    """

    type = serializers.SerializerMethodField(help_text="The type of the element.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return element_type_registry.get_by_model(instance.specific_class).type

    style_background_file = UserFileField(
        allow_null=True,
        help_text="The background image file",
        validators=[image_file_validation],
    )

    class Meta:
        model = Element
        fields = (
            "id",
            "page_id",
            "type",
            "order",
            "parent_element_id",
            "place_in_container",
            "visibility",
            "styles",
            "style_border_top_color",
            "style_border_top_size",
            "style_padding_top",
            "style_margin_top",
            "style_border_bottom_color",
            "style_border_bottom_size",
            "style_padding_bottom",
            "style_margin_bottom",
            "style_border_left_color",
            "style_border_left_size",
            "style_padding_left",
            "style_margin_left",
            "style_border_right_color",
            "style_border_right_size",
            "style_padding_right",
            "style_margin_right",
            "style_background",
            "style_background_color",
            "style_background_file",
            "style_background_mode",
            "style_width",
            "role_type",
            "roles",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "page_id": {"read_only": True},
            "type": {"read_only": True},
            "order": {"read_only": True, "help_text": "Lowest first."},
        }


class CreateElementSerializer(serializers.ModelSerializer):
    """
    This serializer allow to set the type of an element and the element id before which
    we want to insert the new element.
    """

    type = serializers.ChoiceField(
        choices=lazy(element_type_registry.get_types, list)(),
        required=True,
        help_text="The type of the element.",
    )
    before_id = serializers.IntegerField(
        required=False,
        help_text="If provided, creates the element before the element with the "
        "given id.",
    )
    parent_element_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text="If provided, creates the element as a child of the element with "
        "the given id.",
    )

    style_background_file = UserFileField(
        allow_null=True,
        help_text="The background image file",
        validators=[image_file_validation],
    )

    class Meta:
        model = Element
        fields = (
            "order",
            "before_id",
            "type",
            "parent_element_id",
            "place_in_container",
            "visibility",
            "styles",
            "style_border_top_color",
            "style_border_top_size",
            "style_padding_top",
            "style_margin_top",
            "style_border_bottom_color",
            "style_border_bottom_size",
            "style_padding_bottom",
            "style_margin_bottom",
            "style_border_left_color",
            "style_border_left_size",
            "style_padding_left",
            "style_margin_left",
            "style_border_right_color",
            "style_border_right_size",
            "style_padding_right",
            "style_margin_right",
            "style_background",
            "style_background_color",
            "style_background_file",
            "style_background_mode",
            "style_width",
        )
        extra_kwargs = {
            "visibility": {"default": Element.VISIBILITY_TYPES.ALL},
            "styles": {"default": dict},
        }


class UpdateElementSerializer(serializers.ModelSerializer):
    style_background_file = UserFileField(
        allow_null=True,
        help_text="The background image file",
        validators=[image_file_validation],
    )

    class Meta:
        model = Element
        fields = (
            "visibility",
            "styles",
            "style_border_top_color",
            "style_border_top_size",
            "style_padding_top",
            "style_margin_top",
            "style_border_bottom_color",
            "style_border_bottom_size",
            "style_padding_bottom",
            "style_margin_bottom",
            "style_border_left_color",
            "style_border_left_size",
            "style_padding_left",
            "style_margin_left",
            "style_border_right_color",
            "style_border_right_size",
            "style_padding_right",
            "style_margin_right",
            "style_background",
            "style_background_color",
            "style_background_file",
            "style_background_mode",
            "style_width",
            "role_type",
            "roles",
        )


class MoveElementSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text=(
            "If provided, the element is moved before the element with this Id. "
            "Otherwise the element is placed at the end of the page."
        ),
    )
    parent_element_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        default=None,
        help_text="If provided, the element is moved as a child of the element with "
        "the given id.",
    )
    place_in_container = serializers.CharField(
        required=False,
        allow_null=True,
        default=None,
        help_text="The place in the container.",
    )


class DuplicateElementSerializer(serializers.Serializer):
    elements = serializers.SerializerMethodField(help_text="The duplicated elements.")
    workflow_actions = serializers.SerializerMethodField(
        help_text="The duplicated workflow actions"
    )

    @extend_schema_field(ElementSerializer(many=True))
    def get_elements(self, obj: ElementsAndWorkflowActions):
        return [
            element_type_registry.get_serializer(element, ElementSerializer).data
            for element in obj["elements"]
        ]

    @extend_schema_field(BuilderWorkflowActionSerializer(many=True))
    def get_workflow_actions(self, obj: ElementsAndWorkflowActions):
        return [
            builder_workflow_action_type_registry.get_serializer(
                workflow_action, BuilderWorkflowActionSerializer
            ).data
            for workflow_action in obj["workflow_actions"]
        ]


class PageParameterValueSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = FormulaSerializerField(allow_blank=True)


@extend_schema_serializer(exclude_fields=("config",))
class CollectionFieldSerializer(serializers.ModelSerializer):
    """
    This serializer transform the flat properties object from/to a config dict property.
    This allows us to see the field on the frontend side as a simple polymorphic
    object.
    """

    default_allowed_fields = ["name", "type", "id", "uid", "styles"]

    config = serializers.DictField(
        required=False,
        help_text=CollectionField._meta.get_field("config").help_text,
    )

    def get_type_from_type_name(self, name):
        return collection_field_type_registry.get(name)

    def get_type_from_instance(self, instance):
        return collection_field_type_registry.get(instance.type)

    def get_type_from_mapping(self, mapping):
        return collection_field_type_registry.get(mapping["type"])

    def to_representation(self, instance):
        """
        Flatten the config dict to an object.
        """

        if isinstance(instance, Mapping):
            instance_type = self.get_type_from_mapping(instance)
        else:
            instance_type = self.get_type_from_instance(instance)

        serializer = instance_type.get_serializer(instance)

        if isinstance(instance, Mapping):
            ret = serializer.to_representation(instance["config"])
        else:
            ret = serializer.to_representation(instance.config)

        result = super().to_representation(instance)
        result.update(**ret)

        del result["config"]

        return result

    def to_internal_value(self, data):
        """
        Transform the flat object received to a proper config dict.
        """

        try:
            if self.partial and self.instance:
                instance_type = self.get_type_from_instance(self.instance)
            else:
                instance_type = self.get_type_from_mapping(data)
        except InstanceTypeDoesNotExist:
            raise ValidationError(
                "The given field type doesn't exist.", code="INVALID_FIELD_TYPE"
            )

        field_config_data = {}
        for field_name in instance_type.serializer_field_names:
            if field_name in data:
                field_config_data[field_name] = data.pop(field_name)

        # Check that we have only authorized field
        for field_name in data.keys():
            if field_name not in self.default_allowed_fields:
                raise ValidationError(
                    f"The property <{field_name}> doesn't exist for type <{instance_type.type}>",
                    code="INVALID_FIELD_PROPERTY",
                )

        ret = instance_type.get_serializer(field_config_data).to_internal_value(
            field_config_data
        )

        data["config"] = ret

        return super().to_internal_value(data)

    class Meta:
        model = CollectionField
        exclude = ("order",)


class UpdateCollectionFieldSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(collection_field_type_registry.get_types, list)(),
        required=True,
        help_text=CollectionField._meta.get_field("type").help_text,
    )

    value = FormulaSerializerField(allow_blank=True)


class ChoiceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoiceElementOption
        fields = ["id", "value", "name"]


class CollectionElementPropertyOptionsSerializer(
    UnknownFieldRaisesExceptionSerializerMixin, serializers.ModelSerializer
):
    schema_property = serializers.CharField(
        required=True,
        max_length=225,
        help_text="The name of the property in the schema this option belongs to.",
    )

    class Meta:
        model = CollectionElementPropertyOptions
        fields = ["schema_property", "filterable", "sortable", "searchable"]
