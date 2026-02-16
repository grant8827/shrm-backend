from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telehealth', '0005_alter_telehealthsession_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TelehealthTranscript',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transcript', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telehealth_transcripts_created', to='users.user')),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='telehealth_transcripts_as_patient', to='users.user')),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='transcript_record', to='telehealth.telehealthsession')),
                ('therapist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telehealth_transcripts_as_therapist', to='users.user')),
            ],
            options={
                'db_table': 'telehealth_transcript',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='telehealthtranscript',
            index=models.Index(fields=['therapist', 'created_at'], name='telehealth__therapi_13c90f_idx'),
        ),
        migrations.AddIndex(
            model_name='telehealthtranscript',
            index=models.Index(fields=['patient', 'created_at'], name='telehealth__patient_aa7b63_idx'),
        ),
    ]
