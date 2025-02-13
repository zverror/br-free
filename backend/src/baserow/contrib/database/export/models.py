from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import JSONField, Q

from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.models import View

User = get_user_model()

EXPORT_JOB_EXPORTING_STATUS = "exporting"
EXPORT_JOB_FAILED_STATUS = "failed"
EXPORT_JOB_CANCELLED_STATUS = "cancelled"
EXPORT_JOB_PENDING_STATUS = "pending"
EXPORT_JOB_EXPIRED_STATUS = "expired"
EXPORT_JOB_FINISHED_STATUS = "finished"
EXPORT_JOB_STATUS_CHOICES = [
    (EXPORT_JOB_PENDING_STATUS, EXPORT_JOB_PENDING_STATUS),
    (EXPORT_JOB_EXPORTING_STATUS, EXPORT_JOB_EXPORTING_STATUS),
    (EXPORT_JOB_CANCELLED_STATUS, EXPORT_JOB_CANCELLED_STATUS),
    (EXPORT_JOB_FINISHED_STATUS, EXPORT_JOB_FINISHED_STATUS),
    (EXPORT_JOB_FAILED_STATUS, EXPORT_JOB_FAILED_STATUS),
    (EXPORT_JOB_EXPIRED_STATUS, EXPORT_JOB_EXPIRED_STATUS),
]
EXPORT_JOB_RUNNING_STATUSES = [EXPORT_JOB_PENDING_STATUS, EXPORT_JOB_EXPORTING_STATUS]


class ExportJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)
    # An export job might be for just a table and not a particular view of that table
    # , in that situation the view will be None.
    view = models.ForeignKey(View, on_delete=models.SET_NULL, null=True, blank=True)
    # New exporter types might be registered dynamically by plugins hence we can't
    # restrict this field to a particular choice of options as we don't know them.
    exporter_type = models.TextField()
    state = models.TextField(choices=EXPORT_JOB_STATUS_CHOICES)
    exported_file_name = models.TextField(
        null=True,
        blank=True,
    )
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # A float going from 0.0 to 100.0 indicating how much progress has been made on the
    # export.
    progress_percentage = models.FloatField(default=0.0)
    export_options = JSONField()

    def is_cancelled_or_expired(self):
        return self.state in [EXPORT_JOB_CANCELLED_STATUS, EXPORT_JOB_EXPIRED_STATUS]

    @staticmethod
    def unfinished_jobs(user):
        return ExportJob.objects.filter(user=user).filter(
            state__in=EXPORT_JOB_RUNNING_STATUSES
        )

    @property
    def workspace_id(self):
        # FIXME: Temporarily setting the current workspace ID for URL generation in
        # storage backends, enabling permission checks at download time.
        return self.table.database.workspace_id

    @staticmethod
    def jobs_requiring_cleanup(current_time):
        """
        Returns jobs which were created more than settings.EXPORT_FILE_EXPIRE_MINUTES
        ago. A job requires cleanup if it either has an exported_file_name and hence
        we want to delete that file OR if the job is still has a running status.

        :param current_time: The current time used to check if a job has expired or
            not.
        :return: A queryset of export jobs that require clean up.
        """

        expired_job_time = current_time - timedelta(
            minutes=settings.EXPORT_FILE_EXPIRE_MINUTES
        )
        return ExportJob.objects.filter(created_at__lte=expired_job_time).filter(
            Q(exported_file_name__isnull=False)
            | Q(state__in=EXPORT_JOB_RUNNING_STATUSES)
        )

    class Meta:
        indexes = [
            models.Index(fields=["created_at", "user", "state"]),
        ]
