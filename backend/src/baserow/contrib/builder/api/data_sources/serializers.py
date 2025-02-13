from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from baserow.api.serializers import CommaSeparatedIntegerValuesField
from baserow.api.services.serializers import (
    CreateServiceSerializer,
    ServiceSerializer,
    UpdateServiceSerializer,
)
from baserow.contrib.builder.data_sources.models import DataSource
from baserow.contrib.builder.elements.models import Element
from baserow.core.services.registries import service_type_registry


class DataSourceSerializer(ServiceSerializer):
    """
    Basic data_source serializer mostly for returned values. This serializer flatten the
    service properties so that from an API POV the data_source object only exists.
    """

    id = serializers.SerializerMethodField(help_text="Data source id.")
    name = serializers.SerializerMethodField(
        help_text=DataSource._meta.get_field("name").help_text
    )
    page_id = serializers.SerializerMethodField(
        help_text=DataSource._meta.get_field("page").help_text
    )
    order = serializers.SerializerMethodField(
        help_text=DataSource._meta.get_field("order").help_text
    )
    type = serializers.SerializerMethodField(help_text="The type of the data source.")

    def _get_service_instance(self, instance):
        # We generate the service schema using a `Service` instance.
        # If the `instance` is a `DataSource` instance, traverse its
        # 1-1 relation to `Service` and serialize it.
        return instance.service if isinstance(instance, DataSource) else instance

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        service_instance = self._get_service_instance(instance)
        if service_instance:
            return super().get_type(service_instance)
        else:
            return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_id(self, instance):
        return self.context["data_source"].id

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, instance):
        return self.context["data_source"].name

    @extend_schema_field(OpenApiTypes.INT)
    def get_page_id(self, instance):
        return self.context["data_source"].page_id

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_order(self, instance):
        return self.context["data_source"].order

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_schema(self, instance):
        service_instance = self._get_service_instance(instance)
        if service_instance:
            return super().get_schema(service_instance)
        return None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_context_data(self, instance):
        service_instance = self._get_service_instance(instance)
        if service_instance:
            return super().get_context_data(service_instance)
        else:
            return {}

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_context_data_schema(self, instance):
        service_instance = self._get_service_instance(instance)
        if service_instance:
            return super().get_context_data_schema(service_instance)
        else:
            return None

    class Meta(ServiceSerializer.Meta):
        fields = ServiceSerializer.Meta.fields + ("name", "page_id", "order")
        extra_kwargs = {
            **ServiceSerializer.Meta.extra_kwargs,
            "name": {"read_only": True},
            "page_id": {"read_only": True},
            "order": {"read_only": True, "help_text": "Lowest first."},
        }


class CreateDataSourceSerializer(CreateServiceSerializer):
    """
    This serializer allow to set the type of a data_source and the data_source id
    before which we want to insert the new data_source.
    """

    name = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=DataSource._meta.get_field("name").help_text,
    )
    page_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text=DataSource._meta.get_field("page").help_text,
    )
    before_id = serializers.IntegerField(
        required=False,
        help_text="If provided, creates the data_source before the data_source with the "
        "given id.",
    )
    type = serializers.ChoiceField(
        choices=lazy(service_type_registry.get_types, list)(),
        required=False,
        help_text="The type of the service.",
    )

    class Meta(ServiceSerializer.Meta):
        fields = CreateServiceSerializer.Meta.fields + (
            "name",
            "page_id",
            "before_id",
        )


class BaseUpdateDataSourceSerializer(serializers.ModelSerializer):
    class Meta(ServiceSerializer.Meta):
        model = DataSource
        fields = ("name",)
        extra_kwargs = {
            "name": {"required": False},
        }


class UpdateDataSourceSerializer(UpdateServiceSerializer):
    name = serializers.CharField(required=False)

    class Meta(ServiceSerializer.Meta):
        fields = UpdateServiceSerializer.Meta.fields + ("name",)


class MoveDataSourceSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text=(
            "If provided, the data_source is moved before the data_source with this Id. "
            "Otherwise the data_source is placed  last for this page."
        ),
    )


class GetRecordIdsSerializer(serializers.Serializer):
    record_ids = CommaSeparatedIntegerValuesField()


class DispatchDataSourceDataSourceContextSerializer(serializers.Serializer):
    element = serializers.PrimaryKeyRelatedField(
        required=False,
        default=None,
        allow_null=True,
        queryset=Element.objects.select_related("page__builder").all(),
        help_text="Optionally provide an `element` to the data source. Currently only "
        "used in element-level filtering, sorting and searching if the "
        "element is a collection element.",
    )


class DispatchDataSourceRequestSerializer(serializers.Serializer):
    data_source = DispatchDataSourceDataSourceContextSerializer(
        required=False,
        default={},
        help_text="The data source dispatch context data.",
    )

    def is_valid(self, *args, **kwargs):
        """
        Responsible for validating the data source dispatch request. Ensures that
        the dispatched element belongs to the same page as the data source.
        """

        super().is_valid(*args, **kwargs)

        data_source = self.context.get("data_source")
        element = self.validated_data.get("data_source").get("element")
        if element:
            if (
                element.page_id != data_source.page_id
                and element.page.builder.shared_page.id != data_source.page_id
            ):
                raise ValidationError(
                    "The data source is not available for the dispatched element.",
                    code="PAGE_MISMATCH",
                )
