# backend/users/management/commands/create_test_users.py
"""
Django management command to create test users for TheraCare EHR System.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User
from patients.models import Patient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create test users for TheraCare EHR system development'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Skip creation if users already exist',
        )
    
    def handle(self, *args, **options):
        """Create test users with different roles."""
        
        # Check if users already exist
        if User.objects.exists() and options['skip_if_exists']:
            self.stdout.write(
                self.style.WARNING('Users already exist. Skipping creation.')
            )
            return
        
        try:
            with transaction.atomic():
                # Create admin user
                admin_user, created = User.objects.get_or_create(
                    email='admin@theracare.local',
                    defaults={
                        'first_name': 'System',
                        'last_name': 'Administrator',
                        'role': 'admin',
                        'is_active': True,
                        'is_staff': True,
                        'is_superuser': True,
                    }
                )
                if created:
                    admin_user.set_password('AdminPass123!')
                    admin_user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created admin user: {admin_user.email}')
                    )
                
                # Create therapist user
                therapist_user, created = User.objects.get_or_create(
                    email='dr.smith@theracare.local',
                    defaults={
                        'first_name': 'Jane',
                        'last_name': 'Smith',
                        'role': 'therapist',
                        'phone': '(555) 123-4567',
                        'is_active': True,
                    }
                )
                if created:
                    therapist_user.set_password('TherapistPass123!')
                    therapist_user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created therapist user: {therapist_user.email}')
                    )
                
                # Create staff user
                staff_user, created = User.objects.get_or_create(
                    email='staff@theracare.local',
                    defaults={
                        'first_name': 'Mike',
                        'last_name': 'Johnson',
                        'role': 'staff',
                        'phone': '(555) 234-5678',
                        'is_active': True,
                    }
                )
                if created:
                    staff_user.set_password('StaffPass123!')
                    staff_user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created staff user: {staff_user.email}')
                    )
                
                # Create client user
                client_user, created = User.objects.get_or_create(
                    email='john.doe@email.com',
                    defaults={
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'role': 'client',
                        'phone': '(555) 345-6789',
                        'is_active': True,
                    }
                )
                if created:
                    client_user.set_password('ClientPass123!')
                    client_user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created client user: {client_user.email}')
                    )
                
                # Create a test patient for the client user
                if created:  # Only create patient if client was just created
                    patient, patient_created = Patient.objects.get_or_create(
                        user=client_user,
                        defaults={
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'email': 'john.doe@email.com',
                            'phone': '(555) 345-6789',
                            'date_of_birth': '1985-06-15',
                            'gender': 'M',
                            'street_address': '123 Main Street',
                            'city': 'Anytown',
                            'state': 'NY',
                            'zip_code': '12345',
                            'admission_date': '2024-01-15',
                            'emergency_contact_name': 'Jane Doe',
                            'emergency_contact_phone': '(555) 345-6790',
                            'emergency_contact_relationship': 'Spouse',
                        }
                    )
                    if patient_created:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Created patient record for: {client_user.email}')
                        )
                
                # Display login information
                self.stdout.write(
                    self.style.SUCCESS('\n=== Test User Login Information ===')
                )
                
                users_info = [
                    ('Admin', 'admin@theracare.local', 'AdminPass123!', 'Full system access'),
                    ('Therapist', 'dr.smith@theracare.local', 'TherapistPass123!', 'Clinical access'),
                    ('Staff', 'staff@theracare.local', 'StaffPass123!', 'Administrative access'),
                    ('Client', 'john.doe@email.com', 'ClientPass123!', 'Patient portal access'),
                ]
                
                for role, email, password, description in users_info:
                    self.stdout.write(f'\n{role} User:')
                    self.stdout.write(f'  Email: {email}')
                    self.stdout.write(f'  Password: {password}')
                    self.stdout.write(f'  Access: {description}')
                
                self.stdout.write(
                    self.style.WARNING(
                        '\n⚠️  These are test credentials for development only!'
                        '\n   Change passwords before deploying to production.'
                        '\n\n📧 NOTE: Login uses EMAIL ADDRESS, not username!'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating test users: {str(e)}')
            )
            raise