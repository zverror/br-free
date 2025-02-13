from django.db import models

from baserow.contrib.database.models import Database
from baserow.core.jobs.mixins import JobWithUserIpAddress
from baserow.core.jobs.models import Job
from baserow.core.models import Workspace


class AirtableImportJob(JobWithUserIpAddress, Job):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        help_text="The workspace where the Airtable base must be imported into.",
    )
    airtable_share_id = models.CharField(
        max_length=200,
        help_text="Public ID of the shared Airtable base that must be imported.",
    )
    database = models.ForeignKey(
        Database,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The imported Baserow database.",
    )
