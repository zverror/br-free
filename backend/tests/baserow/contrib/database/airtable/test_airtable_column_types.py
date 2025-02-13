import pytest
import responses

from baserow.contrib.database.airtable.airtable_column_types import (
    CheckboxAirtableColumnType,
    CountAirtableColumnType,
    DateAirtableColumnType,
    ForeignKeyAirtableColumnType,
    FormulaAirtableColumnType,
    MultilineTextAirtableColumnType,
    MultipleAttachmentAirtableColumnType,
    MultiSelectAirtableColumnType,
    NumberAirtableColumnType,
    PhoneAirtableColumnType,
    RatingAirtableColumnType,
    RichTextTextAirtableColumnType,
    SelectAirtableColumnType,
    TextAirtableColumnType,
)
from baserow.contrib.database.airtable.registry import airtable_column_type_registry
from baserow.contrib.database.fields.models import (
    BooleanField,
    CountField,
    CreatedOnField,
    DateField,
    EmailField,
    FileField,
    LastModifiedField,
    LinkRowField,
    LongTextField,
    MultipleSelectField,
    NumberField,
    PhoneNumberField,
    RatingField,
    SingleSelectField,
    TextField,
    URLField,
)


@pytest.mark.django_db
@responses.activate
def test_unknown_column_type():
    airtable_field = {"id": "fldTn59fpliSFcwpFA9", "name": "Unknown", "type": "unknown"}
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert baserow_field is None
    assert baserow_field is None

    airtable_field = {
        "id": "fldTn59fpliSFcwpFA9",
        "name": "Unknown",
        "type": "formula",
        "typeOptions": {"displayType": "unknown"},
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert baserow_field is None
    assert baserow_field is None


@pytest.mark.django_db
@responses.activate
def test_airtable_import_text_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldwSc9PqedIhTSqhi5",
        "name": "Single line text",
        "type": "text",
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, TextField)
    assert isinstance(airtable_column_type, TextAirtableColumnType)


@pytest.mark.django_db
@responses.activate
def test_airtable_import_checkbox_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldTn59fpliSFcwpFA9",
        "name": "Checkbox",
        "type": "checkbox",
        "typeOptions": {"color": "green", "icon": "check"},
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, BooleanField)
    assert isinstance(airtable_column_type, CheckboxAirtableColumnType)


@pytest.mark.django_db
@responses.activate
def test_airtable_import_created_on_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldcTpJuoUVpsDNoszO",
        "name": "Created",
        "type": "formula",
        "typeOptions": {
            "isDateTime": False,
            "dateFormat": "Local",
            "displayType": "createdTime",
            "timeZone": "client",
            "formulaTextParsed": "CREATED_TIME()",
            "dependencies": {"referencedColumnIdsForValue": []},
            "resultType": "date",
            "resultIsArray": False,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, CreatedOnField)
    assert isinstance(airtable_column_type, FormulaAirtableColumnType)
    assert baserow_field.date_format == "ISO"
    assert baserow_field.date_include_time is False
    assert baserow_field.date_time_format == "24"
    assert baserow_field.date_force_timezone is None

    airtable_field = {
        "id": "fldcTpJuoUVpsDNoszO",
        "name": "Created",
        "type": "formula",
        "typeOptions": {
            "isDateTime": True,
            "dateFormat": "European",
            "displayType": "createdTime",
            "timeZone": "Europe/Amsterdam",
            "formulaTextParsed": "CREATED_TIME()",
            "dependencies": {"referencedColumnIdsForValue": []},
            "resultType": "date",
            "resultIsArray": False,
            "timeFormat": "12hour",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, CreatedOnField)
    assert isinstance(airtable_column_type, FormulaAirtableColumnType)
    assert baserow_field.date_format == "EU"
    assert baserow_field.date_include_time is True
    assert baserow_field.date_time_format == "12"
    assert baserow_field.date_force_timezone == "Europe/Amsterdam"

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2022-01-03T14:51:00.000Z", {}
        )
        is None
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_date_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldyAXIzheHfugGhuFD",
        "name": "ISO DATE",
        "type": "date",
        "typeOptions": {"isDateTime": False, "dateFormat": "US"},
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, DateField)
    assert isinstance(airtable_column_type, DateAirtableColumnType)
    assert baserow_field.date_format == "US"
    assert baserow_field.date_include_time is False
    assert baserow_field.date_time_format == "24"

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2022-01-03T14:51:00.000Z", {}
        )
        == "2022-01-03"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "0999-02-04T14:51:00.000Z", {}
        )
        == "0999-02-04"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, None, {}
        )
        is None
    )


@pytest.mark.django_db
def test_airtable_import_european_date_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldyAXIzheHfugGhuFD",
        "name": "EUROPE",
        "type": "date",
        "typeOptions": {
            "isDateTime": False,
            "dateFormat": "European",
            "timeFormat": "12hour",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, DateField)
    assert isinstance(airtable_column_type, DateAirtableColumnType)
    assert baserow_field.date_format == "EU"
    assert baserow_field.date_include_time is False
    assert baserow_field.date_time_format == "12"

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2022-01-03T14:51:00.000Z", {}
        )
        == "2022-01-03"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2020-08-27T21:10:24.828Z", {}
        )
        == "2020-08-27"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, None, {}
        )
        is None
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_datetime_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldEB5dp0mNjVZu0VJI",
        "name": "Date",
        "type": "date",
        "typeOptions": {
            "isDateTime": True,
            "dateFormat": "Local",
            "timeFormat": "24hour",
            "timeZone": "client",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, DateField)
    assert isinstance(airtable_column_type, DateAirtableColumnType)
    assert baserow_field.date_format == "ISO"
    assert baserow_field.date_include_time is True
    assert baserow_field.date_time_format == "24"

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2022-01-03T14:51:00.000Z", {}
        )
        == "2022-01-03T14:51:00+00:00"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2020-08-27T21:10:24.828Z", {}
        )
        == "2020-08-27T21:10:24.828000+00:00"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, None, {}
        )
        is None
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_datetime_with_default_timezone_column(
    data_fixture, api_client
):
    airtable_field = {
        "id": "fldEB5dp0mNjVZu0VJI",
        "name": "Date",
        "type": "date",
        "typeOptions": {
            "isDateTime": True,
            "dateFormat": "Local",
            "timeFormat": "24hour",
            "timeZone": "client",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, DateField)
    assert isinstance(airtable_column_type, DateAirtableColumnType)
    assert baserow_field.date_format == "ISO"
    assert baserow_field.date_include_time is True
    assert baserow_field.date_time_format == "24"
    assert baserow_field.date_force_timezone is None

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2022-01-03T23:51:00.000Z", {}
        )
        == "2022-01-03T23:51:00+00:00"
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_datetime_with_different_default_timezone_column(
    data_fixture, api_client
):
    airtable_field = {
        "id": "fldEB5dp0mNjVZu0VJI",
        "name": "Date",
        "type": "date",
        "typeOptions": {
            "isDateTime": True,
            "dateFormat": "Local",
            "timeFormat": "24hour",
            "timeZone": "Europe/Amsterdam",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, DateField)
    assert isinstance(airtable_column_type, DateAirtableColumnType)
    assert baserow_field.date_format == "ISO"
    assert baserow_field.date_include_time is True
    assert baserow_field.date_time_format == "24"
    assert baserow_field.date_force_timezone == "Europe/Amsterdam"

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2022-01-03T23:51:00.000Z", {}
        )
        == "2022-01-03T23:51:00+00:00"
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_datetime_edge_case_1(data_fixture, api_client):
    airtable_field = {
        "id": "fldEB5dp0mNjVZu0VJI",
        "name": "Date",
        "type": "date",
        "typeOptions": {
            "isDateTime": True,
            "dateFormat": "Local",
            "timeFormat": "24hour",
            "timeZone": "client",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, DateField)
    assert isinstance(airtable_column_type, DateAirtableColumnType)
    assert baserow_field.date_format == "ISO"
    assert baserow_field.date_include_time is True
    assert baserow_field.date_time_format == "24"

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "+020222-03-28T00:00:00.000Z", {}
        )
        is None
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_email_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldNdoAZRim39AxR9Eg",
        "name": "Email",
        "type": "text",
        "typeOptions": {"validatorName": "email"},
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, EmailField)
    assert isinstance(airtable_column_type, TextAirtableColumnType)

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "NOT_EMAIL", {}
        )
        == ""
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "test@test.nl", {}
        )
        == "test@test.nl"
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_multiple_attachment_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldwdy4qWUvC5PmW5yd",
        "name": "Attachment",
        "type": "multipleAttachment",
        "typeOptions": {"unreversed": True},
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, FileField)
    assert isinstance(airtable_column_type, MultipleAttachmentAirtableColumnType)

    files_to_download = {}
    assert airtable_column_type.to_baserow_export_serialized_value(
        {},
        airtable_field,
        baserow_field,
        [
            {
                "id": "attecVDNr3x7oE8Bj",
                "url": "https://dl.airtable.com/.attachments/70e50b90fb83997d25e64937979b6b5b/f3f62d23/file-sample.txt",
                "filename": "file-sample.txt",
                "uploadsDmzS3Key": "YbuBlXi8SP2cMzT8F3Yo_file-sample.txt",
                "servingS3Key": ".attachments/70e50b90fb83997d25e64937979b6b5b/f3f62d23/file-sample.txt",
                "type": "application/pdf",
                "size": 142786,
                "smallThumbUrl": "https://dl.airtable.com/.attachmentThumbnails/1af3d5cef7ef07f39ec87eb18cbcf343/dbc2b9ab",
                "smallThumbWidth": 25,
                "smallThumbHeight": 36,
                "largeThumbUrl": "https://dl.airtable.com/.attachmentThumbnails/ff0f3e6624ec60eb0c22b82fec23ee9a/9bf8fc2b",
                "largeThumbWidth": 362,
                "largeThumbHeight": 512,
            },
            {
                "id": "attFE9KxOeLxbFn58",
                "url": "https://dl.airtable.com/.attachments/e93dc201ce27080d9ad9df5775527d09/93e85b28/file-sample_500kB.doc",
                "filename": "file-sample_500kB.doc",
                "type": "application/msword",
                "size": 503296,
            },
        ],
        files_to_download,
    ) == [
        {
            "name": "70e50b90fb83997d25e64937979b6b5b_f3f62d23_file-sample.txt",
            "visible_name": "file-sample.txt",
            "original_name": "file-sample.txt",
        },
        {
            "name": "e93dc201ce27080d9ad9df5775527d09_93e85b28_file-sample_500kB.doc",
            "visible_name": "file-sample_500kB.doc",
            "original_name": "file-sample_500kB.doc",
        },
    ]
    assert files_to_download == {
        "70e50b90fb83997d25e64937979b6b5b_f3f62d23_file-sample.txt": "https://dl.airtable.com/.attachments/70e50b90fb83997d25e64937979b6b5b/f3f62d23/file-sample.txt",
        "e93dc201ce27080d9ad9df5775527d09_93e85b28_file-sample_500kB.doc": "https://dl.airtable.com/.attachments/e93dc201ce27080d9ad9df5775527d09/93e85b28/file-sample_500kB.doc",
    }


@pytest.mark.django_db
@responses.activate
def test_airtable_import_last_modified_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldws6n8xdrEJrMxJFJ",
        "name": "Last",
        "type": "formula",
        "typeOptions": {
            "isDateTime": False,
            "dateFormat": "Local",
            "displayType": "lastModifiedTime",
            "timeZone": "client",
            "formulaTextParsed": "LAST_MODIFIED_TIME()",
            "dependencies": {
                "referencedColumnIdsForValue": [],
                "dependsOnAllColumnModifications": True,
            },
            "resultType": "date",
            "resultIsArray": False,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, LastModifiedField)
    assert isinstance(airtable_column_type, FormulaAirtableColumnType)
    assert baserow_field.date_format == "ISO"
    assert baserow_field.date_include_time is False
    assert baserow_field.date_time_format == "24"
    assert baserow_field.date_force_timezone is None

    airtable_field = {
        "id": "fldws6n8xdrEJrMxJFJ",
        "name": "Last",
        "type": "formula",
        "typeOptions": {
            "isDateTime": True,
            "dateFormat": "US",
            "displayType": "lastModifiedTime",
            "timeZone": "Europe/Amsterdam",
            "formulaTextParsed": "LAST_MODIFIED_TIME()",
            "dependencies": {
                "referencedColumnIdsForValue": [],
                "dependsOnAllColumnModifications": True,
            },
            "resultType": "date",
            "resultIsArray": False,
            "timeFormat": "12hour",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, LastModifiedField)
    assert isinstance(airtable_column_type, FormulaAirtableColumnType)
    assert baserow_field.date_format == "US"
    assert baserow_field.date_include_time is True
    assert baserow_field.date_time_format == "12"
    assert baserow_field.date_force_timezone == "Europe/Amsterdam"

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "2022-01-03T14:51:00.000Z", {}
        )
        == "2022-01-03T14:51:00+00:00"
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_foreign_key_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldQcEaGEe7xuhUEuPL",
        "name": "Link to Users",
        "type": "foreignKey",
        "typeOptions": {
            "foreignTableId": "tblRpq315qnnIcg5IjI",
            "relationship": "many",
            "unreversed": True,
            "symmetricColumnId": "fldFh5wIL430N62LN6t",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {"id": "tblxxx"}, airtable_field
    )
    assert isinstance(baserow_field, LinkRowField)
    assert isinstance(airtable_column_type, ForeignKeyAirtableColumnType)
    assert baserow_field.link_row_table_id == "tblRpq315qnnIcg5IjI"
    assert baserow_field.link_row_related_field_id == "fldFh5wIL430N62LN6t"

    assert airtable_column_type.to_baserow_export_serialized_value(
        {
            "tblRpq315qnnIcg5IjI": {
                "recWkle1IOXcLmhILmO": 1,
                "rec5pdtuKyE71lfK1Ah": 2,
            }
        },
        airtable_field,
        baserow_field,
        [
            {
                "foreignRowId": "recWkle1IOXcLmhILmO",
                "foreignRowDisplayName": "Bram 1",
            },
            {
                "foreignRowId": "rec5pdtuKyE71lfK1Ah",
                "foreignRowDisplayName": "Bram 2",
            },
        ],
        {},
    ) == [1, 2]

    # link to same table row
    airtable_field = {
        "id": "fldQcEaGEe7xuhUEuPL",
        "name": "Link to Users",
        "type": "foreignKey",
        "typeOptions": {
            "foreignTableId": "tblRpq315qnnIcg5IjI",
            "relationship": "many",
            "unreversed": True,
            "symmetricColumnId": "fldQcEaGEe7xuhUEuPL",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {"id": "tblRpq315qnnIcg5IjI"}, airtable_field
    )
    assert isinstance(baserow_field, LinkRowField)
    assert isinstance(airtable_column_type, ForeignKeyAirtableColumnType)
    assert baserow_field.link_row_table_id == "tblRpq315qnnIcg5IjI"
    assert baserow_field.link_row_related_field_id == "fldQcEaGEe7xuhUEuPL"


@pytest.mark.django_db
@responses.activate
def test_airtable_import_multiline_text_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Name",
        "type": "multilineText",
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, LongTextField)
    assert isinstance(airtable_column_type, MultilineTextAirtableColumnType)

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "test", {}
        )
        == "test"
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_rich_text_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Name",
        "type": "richText",
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, LongTextField)
    assert isinstance(airtable_column_type, RichTextTextAirtableColumnType)

    content = {
        "otDocumentId": "otdHtbNg2tJKWj62WMn",
        "revision": 4,
        "documentValue": [
            {"insert": "Vestibulum", "attributes": {"bold": True}},
            {"insert": " ante ipsum primis in faucibus orci luctus et ultrices "},
            {"insert": "posuere", "attributes": {"italic": True}},
            {"insert": " cubilia curae; Class aptent taciti sociosqu ad litora."},
        ],
    }
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, content, {}
        )
        == "Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere "
        "cubilia curae; Class aptent taciti sociosqu ad litora."
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_rich_text_column_with_mention(data_fixture, api_client):
    airtable_field = {
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Name",
        "type": "richText",
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, LongTextField)
    assert isinstance(airtable_column_type, RichTextTextAirtableColumnType)

    content = {
        "otDocumentId": "otdHtbNg2tJKWj62WMn",
        "revision": 4,
        "documentValue": [
            {"insert": "Vestibulum", "attributes": {"bold": True}},
            {"insert": " ante ipsum primis in faucibus orci luctus et ultrices "},
            {
                "insert": {
                    "mention": {
                        "mentionId": "menvWlZAaLd2v052j",
                        "userId": "usrr5CVJ5Lz8ErVZS",
                    }
                }
            },
            {"insert": " cubilia curae; Class aptent taciti sociosqu ad litora."},
        ],
    }
    assert airtable_column_type.to_baserow_export_serialized_value(
        {}, airtable_field, baserow_field, content, {}
    ) == (
        "Vestibulum ante ipsum primis in faucibus orci luctus et ultrices "
        "@usrr5CVJ5Lz8ErVZS cubilia curae; Class aptent taciti sociosqu ad litora."
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_multi_select_column(
    data_fixture, api_client, django_assert_num_queries
):
    table = data_fixture.create_database_table()
    airtable_field = {
        "id": "fldURNo0cvi6YWYcYj1",
        "name": "Multiple select",
        "type": "multiSelect",
        "typeOptions": {
            "choiceOrder": ["sel5ekvuoNVvl03olMO", "selEOJmenvqEd6pndFQ"],
            "choices": {
                "selEOJmenvqEd6pndFQ": {
                    "id": "selEOJmenvqEd6pndFQ",
                    "color": "blue",
                    "name": "Option 1",
                },
                "sel5ekvuoNVvl03olMO": {
                    "id": "sel5ekvuoNVvl03olMO",
                    "color": "cyan",
                    "name": "Option 2",
                },
            },
            "disableColors": False,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, MultipleSelectField)
    assert isinstance(airtable_column_type, MultiSelectAirtableColumnType)

    baserow_field.table_id = table.id
    baserow_field.order = 999
    baserow_field.save()

    with django_assert_num_queries(0):
        select_options = list(baserow_field.select_options.all())

    assert len(select_options) == 2
    assert select_options[0].id == "fldURNo0cvi6YWYcYj1_selEOJmenvqEd6pndFQ"
    assert select_options[0].value == "Option 1"
    assert select_options[0].color == "blue"
    assert select_options[0].order == 1
    assert select_options[1].id == "fldURNo0cvi6YWYcYj1_sel5ekvuoNVvl03olMO"
    assert select_options[1].value == "Option 2"
    assert select_options[1].color == "light-blue"
    assert select_options[1].order == 0


@pytest.mark.django_db
@responses.activate
def test_airtable_import_number_integer_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldZBmr4L45mhjILhlA",
        "name": "Number",
        "type": "number",
        "typeOptions": {
            "format": "integer",
            "negative": False,
            "validatorName": "positive",
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, NumberField)
    assert isinstance(airtable_column_type, NumberAirtableColumnType)
    assert baserow_field.number_decimal_places == 0
    assert baserow_field.number_negative is False

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "10", {}
        )
        == "10"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, 10, {}
        )
        == "10"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "-10", {}
        )
        is None
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, -10, {}
        )
        is None
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, None, {}
        )
        is None
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_number_decimal_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldZBmr4L45mhjILhlA",
        "name": "Decimal",
        "type": "number",
        "typeOptions": {
            "format": "decimal",
            "precision": 0,
            "negative": False,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, NumberField)
    assert isinstance(airtable_column_type, NumberAirtableColumnType)
    assert baserow_field.number_decimal_places == 1
    assert baserow_field.number_negative is False

    airtable_field = {
        "id": "fldZBmr4L45mhjILhlA",
        "name": "Decimal",
        "type": "number",
        "typeOptions": {
            "format": "decimal",
            "precision": 2,
            "negative": True,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, NumberField)
    assert isinstance(airtable_column_type, NumberAirtableColumnType)
    assert baserow_field.number_decimal_places == 2
    assert baserow_field.number_negative is True

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "10.22", {}
        )
        == "10.22"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, 10, {}
        )
        == "10"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "-10.555", {}
        )
        == "-10.555"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, -10, {}
        )
        == "-10"
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, None, {}
        )
        is None
    )

    airtable_field = {
        "id": "fldZBmr4L45mhjILhlA",
        "name": "Decimal",
        "type": "number",
        "typeOptions": {
            "format": "decimal",
            "precision": 11,
            "negative": True,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, NumberField)
    assert isinstance(airtable_column_type, NumberAirtableColumnType)
    assert baserow_field.number_decimal_places == 10
    assert baserow_field.number_negative is True


@pytest.mark.django_db
@responses.activate
def test_airtable_import_phone_column(data_fixture, api_client):
    airtable_field = {"id": "fldkrPuYJTqq7vSJ7Oh", "name": "Phone", "type": "phone"}
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, PhoneNumberField)
    assert isinstance(airtable_column_type, PhoneAirtableColumnType)

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "NOT_PHONE", {}
        )
        == ""
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "1234", {}
        )
        == "1234"
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_rating_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldp1IFu0zdgRy70RoX",
        "name": "Rating",
        "type": "rating",
        "typeOptions": {"color": "yellow", "icon": "star", "max": 5},
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, RatingField)
    assert isinstance(airtable_column_type, RatingAirtableColumnType)
    assert baserow_field.max_value == 5
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, 5, {}
        )
        == 5
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_select_column(
    data_fixture, api_client, django_assert_num_queries
):
    table = data_fixture.create_database_table()
    airtable_field = {
        "id": "fldRd2Vkzgsf6X4z6B4",
        "name": "Single select",
        "type": "select",
        "typeOptions": {
            "choiceOrder": ["selbh6rEWaaiyQvWyfg", "selvZgpWhbkeRVphROT"],
            "choices": {
                "selbh6rEWaaiyQvWyfg": {
                    "id": "selbh6rEWaaiyQvWyfg",
                    "color": "blue",
                    "name": "Option A",
                },
                "selvZgpWhbkeRVphROT": {
                    "id": "selvZgpWhbkeRVphROT",
                    "color": "cyan",
                    "name": "Option B",
                },
            },
            "disableColors": False,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, SingleSelectField)
    assert isinstance(airtable_column_type, SelectAirtableColumnType)

    baserow_field.table_id = table.id
    baserow_field.order = 999
    baserow_field.save()

    with django_assert_num_queries(0):
        select_options = list(baserow_field.select_options.all())

    assert len(select_options) == 2
    assert select_options[0].id == "fldRd2Vkzgsf6X4z6B4_selbh6rEWaaiyQvWyfg"
    assert select_options[0].value == "Option A"
    assert select_options[0].color == "blue"
    assert select_options[0].order == 0
    assert select_options[1].id == "fldRd2Vkzgsf6X4z6B4_selvZgpWhbkeRVphROT"
    assert select_options[1].value == "Option B"
    assert select_options[1].color == "light-blue"
    assert select_options[1].order == 1


@pytest.mark.django_db
@responses.activate
def test_airtable_import_url_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Name",
        "type": "text",
        "typeOptions": {"validatorName": "url"},
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, URLField)
    assert isinstance(airtable_column_type, TextAirtableColumnType)

    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "NOT_URL", {}
        )
        == ""
    )
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "https://test.nl", {}
        )
        == "https://test.nl"
    )


@pytest.mark.django_db
@responses.activate
def test_airtable_import_count_column(data_fixture, api_client):
    airtable_field = {
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Count",
        "type": "count",
        "typeOptions": {
            "relationColumnId": "fldABC88Zw7q7u4Z7i4",
            "dependencies": [],
            "resultType": "number",
            "resultIsArray": False,
        },
    }
    (
        baserow_field,
        airtable_column_type,
    ) = airtable_column_type_registry.from_airtable_column_to_serialized(
        {}, airtable_field
    )
    assert isinstance(baserow_field, CountField)
    assert isinstance(airtable_column_type, CountAirtableColumnType)

    assert baserow_field.through_field_id == "fldABC88Zw7q7u4Z7i4"
    assert (
        airtable_column_type.to_baserow_export_serialized_value(
            {}, airtable_field, baserow_field, "1", {}
        )
        is None
    )
