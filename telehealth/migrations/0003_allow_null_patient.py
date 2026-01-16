# Generated migration to allow NULL patient for external sessions

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('telehealth', '0002_add_missing_columns'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telehealthsession',
            name='patient',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='patient_sessions',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
