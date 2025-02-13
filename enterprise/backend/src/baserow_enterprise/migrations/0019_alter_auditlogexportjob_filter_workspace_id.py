# Generated by Django 3.2.13 on 2023-02-23 09:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "baserow_enterprise",
            "0018_rename_filter_group_id_auditlogexportjob_filter_workspace_id",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlogexportjob",
            name="filter_workspace_id",
            field=models.PositiveIntegerField(
                help_text="Optional: The workspace to filter the audit log by.",
                null=True,
            ),
        ),
    ]
