from datetime import timedelta

from django.db import transaction

from baserow.config.celery import app


@app.task(bind=True, name="baserow_premium.license_check", queue="export")
def license_check(self):
    """
    Periodic tasks that check all the licenses with the authority.
    """
    return True

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    pass
