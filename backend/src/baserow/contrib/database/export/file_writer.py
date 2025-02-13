import abc
import time
from typing import Any, Callable

from django.core.paginator import Paginator
from django.db.models import QuerySet

import unicodecsv as csv

from baserow.contrib.database.export.exceptions import ExportJobCanceledException
from baserow.contrib.database.table.models import FieldObject
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import view_type_registry


class FileWriter(abc.ABC):
    """
    A simple file wrapping abstract class which expects it's users to not interact
    with the file but instead write to it via the provided methods. Crucially any
    querysets to be written to the file must be done so via the write_rows method
    as FileWriter implementations perform optimizations when writing querysets in bulk.
    """

    def __init__(self, file):
        self._file = file

    @abc.abstractmethod
    def write_bytes(self, value: bytes):
        """
        Writes the provided bytes straight to the file.

        :param value: The bytes value to write to the file.
        """

    @abc.abstractmethod
    def write(self, value: str, encoding="utf-8"):
        """
        Writes the provided string to the file in the provided encoding.

        :param value: The string to write.
        :param encoding: The encoding to convert the string to before writing.
        """

    @abc.abstractmethod
    def write_rows(
        self,
        queryset: QuerySet,
        write_row: Callable[[Any, bool], None],
    ):
        """
        A specialized method which knows how to write an entire queryset to the file
        in an optimal way.
        :param queryset: The queryset to write to the file.
        :param write_row: A callable function which takes each row from the queryset in
            turn and writes to the file.
        """

    def get_csv_dict_writer(self, headers, **kwargs):
        return csv.DictWriter(self._file, headers, **kwargs)


class PaginatedExportJobFileWriter(FileWriter):
    """
    Uses Django's built-in paginator to write querysets to files in a memory efficient
    manner. Also updates the provided job as it progresses through any queryset writes
    every EXPORT_JOB_UPDATE_FREQUENCY_SECONDS.
    """

    EXPORT_JOB_UPDATE_FREQUENCY_SECONDS = 1

    def __init__(self, file, job):
        super().__init__(file)
        self.job = job
        self.last_check = None

    def write_bytes(self, value: bytes):
        self._file.write(value)

    def write(self, value: str, encoding="utf-8"):
        self._file.write(value.encode(encoding))

    def write_rows(self, queryset, write_row):
        """
        Writes the queryset to the file using the provided write_row callback.
        Every EXPORT_JOB_UPDATE_FREQUENCY_SECONDS will check if the job has been
        cancelled and if so stop writing to the file and will raise a
        ExportJobCanceledException. Finally will also update job.progress_percentage
        every EXPORT_JOB_UPDATE_FREQUENCY_SECONDS as it progresses through writing
        the queryset.

        :param queryset: The queryset to write to the file.
        :param write_row: A callable function which takes each row from the queryset in
            turn and writes to the file.
        """

        self.last_check = time.perf_counter()
        paginator = Paginator(queryset.all(), 2000)
        i = 0
        for page in paginator.page_range:
            for row in paginator.page(page).object_list:
                i = i + 1
                is_last_row = i == paginator.count
                write_row(row, is_last_row)
                self._check_and_update_job(i, paginator.count)

    def _check_and_update_job(self, current_row, total_rows):
        """
        Checks if enough time has passed and if so checks the state of the job and
        updates its progress percentage.
        Will raise a ExportJobCanceledException exception if when a check occurs
        the job has been cancelled.

        :param current_row: An int indicating the current row this export job has
            exported upto
        :param total_rows: An int of the total number of rows this job is exporting.
        """

        current_time = time.perf_counter()
        # We check only every so often as we don't need per row granular updates as the
        # client is only polling every X seconds also.
        enough_time_has_passed = (
            current_time - self.last_check > self.EXPORT_JOB_UPDATE_FREQUENCY_SECONDS
        )
        is_last_row = current_row == total_rows
        if enough_time_has_passed or is_last_row:
            self.last_check = time.perf_counter()
            self.job.refresh_from_db()
            if self.job.is_cancelled_or_expired():
                raise ExportJobCanceledException()
            else:
                self.job.progress_percentage = current_row / total_rows * 100
                self.job.save()


class QuerysetSerializer(abc.ABC):
    """
    A class knows how to serialize a given queryset and the fields of said queryset to
    a file.
    """

    can_handle_rich_value = False

    def __init__(self, queryset, ordered_field_objects):
        self.queryset = queryset
        self.field_serializers = [lambda row: ("id", "id", row.id)]

        for field_object in ordered_field_objects:
            self.field_serializers.append(self._get_field_serializer(field_object))

    @abc.abstractmethod
    def write_to_file(self, file_writer: FileWriter, **kwargs):
        """
        Writes the queryset to the provided file_writer.

        :param file_writer: The file_writer used write the queryset to.
        :param kwargs: Any kwargs will be passed onto the real non-abstract class.
        """

    @classmethod
    def for_table(cls, table) -> "QuerysetSerializer":
        """
        Generates a queryset serializer for the provided table.
        :param table: The table to serialize.
        :return: A QuerysetSerializer ready to serialize the table.
        """

        model = table.get_model()
        qs = model.objects.all().enhance_by_fields()
        ordered_field_objects = model._field_objects.values()
        return cls(qs, ordered_field_objects)

    @classmethod
    def for_view(cls, view) -> "QuerysetSerializer":
        """
        Generates a queryset serializer for the provided view according to it's view
        type and any relevant view settings it might have (filters, sorts,
        hidden columns etc).

        :param view: The view to serialize.
        :return: A QuerysetSerializer ready to serialize the table.
        """

        view_type = view_type_registry.get_by_model(view.specific_class)
        fields, model = view_type.get_visible_fields_and_model(view)
        qs = ViewHandler().get_queryset(view, model=model)
        return cls(qs, fields)

    def _get_field_serializer(self, field_object: FieldObject) -> Callable[[Any], Any]:
        """
        An internal standard method which generates a serializer function for a given
        field_object. It will delegate to the field_types get_export_value on
        how to convert a given field to a python value to be then written to the file.

        :param field_object: The field object to generate a serializer for.
        :return: A callable function which when given a row will return a tuple of the
            fields database column name, the fields human readable name and finally
            the value of the field in the provided converted to a python value ready
            for export.
        """

        def serializer_func(row):
            value = getattr(row, field_object["name"])

            if value is None:
                result = ""
            else:
                result = field_object["type"].get_export_value(
                    value, field_object, rich_value=self.can_handle_rich_value
                )

            return (
                field_object["name"],
                field_object["field"].name,
                result,
            )

        return serializer_func
