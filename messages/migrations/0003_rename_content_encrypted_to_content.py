# Generated manually on 2026-02-11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("theracare_messages", "0002_alter_messagethread_options"),
    ]

    operations = [
        migrations.RenameField(
            model_name="message",
            old_name="content_encrypted",
            new_name="content",
        ),
    ]
