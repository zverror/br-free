from requests.exceptions import RequestException
from rest_framework import serializers

from baserow.api.applications.serializers import (
    PolymorphicApplicationResponseSerializer,
)
from baserow.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from baserow.contrib.database.airtable.exceptions import (
    AirtableBaseNotPublic,
    AirtableShareIsNotABase,
)
from baserow.contrib.database.airtable.models import AirtableImportJob
from baserow.contrib.database.airtable.operations import (
    RunAirtableImportJobOperationType,
)
from baserow.contrib.database.airtable.utils import extract_share_id_from_url
from baserow.contrib.database.airtable.validators import is_publicly_shared_airtable_url
from baserow.core.action.registries import action_type_registry
from baserow.core.exceptions import UserNotInWorkspace, WorkspaceDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.core.jobs.registries import JobType
from baserow.core.signals import application_created

from .actions import ImportDatabaseFromAirtableActionType


class AirtableImportJobType(JobType):
    type = "airtable"

    model_class = AirtableImportJob

    max_count = 1

    api_exceptions_map = {
        UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
    }

    job_exceptions_map = {
        RequestException: "The Airtable server could not be reached.",
        AirtableBaseNotPublic: "The Airtable base is not publicly shared.",
        AirtableShareIsNotABase: "The shared link is not a base. It's probably a "
        "view and the Airtable import tool only supports shared bases.",
    }

    request_serializer_field_names = [
        "workspace_id",
        "database_id",
        "airtable_share_url",
    ]

    request_serializer_field_overrides = {
        "workspace_id": serializers.IntegerField(
            required=False,
            help_text="The workspace ID where the Airtable base must be imported into.",
        ),
        "airtable_share_url": serializers.URLField(
            validators=[is_publicly_shared_airtable_url],
            help_text="The publicly shared URL of the Airtable base (e.g. "
            "https://airtable.com/shrxxxxxxxxxxxxxx)",
        ),
    }

    serializer_field_names = [
        "workspace_id",
        "database",
        "airtable_share_id",
    ]

    serializer_field_overrides = {
        "workspace_id": serializers.IntegerField(
            help_text="The workspace ID where the Airtable base must be imported into.",
        ),
        "airtable_share_id": serializers.URLField(
            max_length=200,
            help_text="Public ID of the shared Airtable base that must be imported.",
        ),
        "database": PolymorphicApplicationResponseSerializer(),
    }

    def prepare_values(self, values, user):
        workspace = CoreHandler().get_workspace(values.pop("workspace_id"))
        CoreHandler().check_permissions(
            user,
            RunAirtableImportJobOperationType.type,
            workspace=workspace,
            context=workspace,
        )

        airtable_share_id = extract_share_id_from_url(values["airtable_share_url"])

        return {
            "airtable_share_id": airtable_share_id,
            "workspace": workspace,
        }

    def run(self, job, progress):
        database = action_type_registry.get(
            ImportDatabaseFromAirtableActionType.type
        ).do(
            job.user,
            job.workspace,
            job.airtable_share_id,
            progress_builder=progress.create_child_builder(
                represents_progress=progress.total
            ),
        )

        application_created.send(self, application=database, user=None)

        job.database = database
        job.save(update_fields=("database",))
