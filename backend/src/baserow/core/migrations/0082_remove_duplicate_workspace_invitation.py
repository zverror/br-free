# Generated by Django 4.1.13 on 2024-03-12 10:03


from django.db import connection, migrations


def forward(apps, schema_editor):
    """
    Delete all the duplicate workspace invitations to the same email address and
    workspace. Keep the one with the highest id.
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """
        DELETE FROM core_workspaceinvitation
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY email, workspace_id
                    ORDER BY id DESC
                ) AS r
                FROM core_workspaceinvitation
            ) t
            WHERE t.r > 1
        )
        """
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0081_usersource_uid"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
