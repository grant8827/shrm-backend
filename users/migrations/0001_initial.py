# Generated migration for users app
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(blank=True, max_length=150, null=True, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.TextField(help_text='Encrypted field', max_length=500)),
                ('last_name', models.TextField(help_text='Encrypted field', max_length=500)),
                ('phone', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('role', models.CharField(choices=[('admin', 'Administrator'), ('therapist', 'Therapist'), ('staff', 'Staff Member'), ('client', 'Client/Patient')], default='client', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('suspended', 'Suspended'), ('pending', 'Pending Activation')], default='pending', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('two_factor_enabled', models.BooleanField(default=False)),
                ('failed_login_attempts', models.PositiveIntegerField(default=0)),
                ('account_locked_until', models.DateTimeField(blank=True, null=True)),
                ('password_changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('must_change_password', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('last_password_change', models.DateTimeField(default=django.utils.timezone.now)),
                ('license_number', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('license_state', models.CharField(blank=True, max_length=2)),
                ('license_expiry', models.DateField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_users', to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_address', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('city', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('state', models.CharField(blank=True, max_length=2)),
                ('zip_code', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('country', models.CharField(default='US', max_length=2)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('timezone', models.CharField(default='UTC', max_length=50)),
                ('email_notifications', models.BooleanField(default=True)),
                ('sms_notifications', models.BooleanField(default=False)),
                ('emergency_contact_name', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('emergency_contact_phone', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('emergency_contact_relationship', models.TextField(blank=True, help_text='Encrypted field', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
                'db_table': 'user_profiles',
            },
        ),
        migrations.CreateModel(
            name='RegistrationToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(db_index=True, max_length=100, unique=True)),
                ('email', models.EmailField(max_length=254)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registration_token', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'registration_tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='users_usernam_e89e0e_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_243f6e_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['role'], name='users_role_a4a6c4_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['status'], name='users_status_8af7e8_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active'], name='users_is_acti_2d7e72_idx'),
        ),
    ]
