# Generated by Django 3.2.13 on 2023-01-16 16:41

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0048_rename_workspaceuser_group"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="GroupInvitation",
            new_name="WorkspaceInvitation",
        ),
    ]
