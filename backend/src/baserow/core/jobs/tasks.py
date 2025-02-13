from datetime import timedelta

from django.conf import settings

from baserow.config.celery import app
from baserow.core.jobs.exceptions import JobCancelled
from baserow.core.jobs.registries import job_type_registry


@app.task(
    bind=True,
    queue="export",
    soft_time_limit=settings.BASEROW_JOB_SOFT_TIME_LIMIT,
)
def run_async_job(self, job_id: int):
    """Run the job task asynchronously"""

    from celery.exceptions import SoftTimeLimitExceeded

    from baserow.core.jobs.handler import JobHandler
    from baserow.core.jobs.models import Job

    job = Job.objects.get(id=job_id).specific
    if job.cancelled:
        return  # Job cancelled before it started. No need to run it.

    job_type = job_type_registry.get_by_model(job)
    job.set_state_started()
    job.save()

    try:
        with job_type.transaction_atomic_context(job):
            JobHandler.run(job)

        job.set_state_finished()
        job.save()
    except JobCancelled:
        # It shouldn't be necessary because the JobHandler shouldn't call job.save(),
        # but this guarantees that the job is in the cancelled state at the end.
        job.set_state_cancelled()
        job.save()
    except BaseException as e:
        # We also want to catch SystemExit exception here and all other possible
        # exceptions to set the job state in a failed state.
        error = f"Something went wrong during the {job_type.type} job execution."

        exception_mapping = {
            SoftTimeLimitExceeded: f"The {job_type.type} job took too long and was "
            "timed out."
        }
        exception_mapping.update(job_type.job_exceptions_map)

        for exception, error_message in exception_mapping.items():
            if isinstance(e, exception):
                error = error_message.format(e=e)
                break

        job.set_state_failed(str(e), error)
        job.save()

        raise
    finally:
        # Delete the import job cached entry because the transaction has been committed
        # and the Job entry now contains the latest data.
        job.clear_job_cache()


# noinspection PyUnusedLocal
@app.task(
    bind=True,
)
def clean_up_jobs(self):
    """
    Execute job cleanup for each job types if they need to cleanup something like files
    or old jobs.
    """

    from baserow.core.jobs.handler import JobHandler

    JobHandler().clean_up_jobs()


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=settings.BASEROW_JOB_CLEANUP_INTERVAL_MINUTES),
        clean_up_jobs.s(),
    )
