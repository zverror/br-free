# Generated by Django 3.2.12 on 2022-05-10 14:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0021_settings_allow_reset_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="to_be_deleted",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "True if the user is pending deletion. An automatic task will "
                    "delete the user after a grace delay."
                ),
            ),
        ),
    ]
