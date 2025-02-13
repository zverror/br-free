# Generated by Django 3.2.13 on 2022-07-13 08:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0028_action_action_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="DuplicateApplicationJob",
            fields=[
                (
                    "job_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.job",
                    ),
                ),
                (
                    "user_session_id",
                    models.CharField(
                        help_text="The user session uuid needed for undo/redo functionality.",
                        max_length=36,
                        null=True,
                    ),
                ),
                (
                    "user_websocket_id",
                    models.CharField(
                        help_text="The user websocket uuid needed to manage signals sent correctly.",
                        max_length=36,
                        null=True,
                    ),
                ),
                (
                    "duplicated_application",
                    models.OneToOneField(
                        help_text="The duplicated Baserow application.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="duplicated_from_jobs",
                        to="core.application",
                    ),
                ),
                (
                    "original_application",
                    models.ForeignKey(
                        help_text="The Baserow application to duplicate.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="duplicated_by_jobs",
                        to="core.application",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("core.job", models.Model),
        ),
    ]
