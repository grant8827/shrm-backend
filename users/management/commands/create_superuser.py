# backend/users/management/commands/create_superuser.py
"""
Django management command to create a superuser for TheraCare EHR System.
"""

from django.core.management.base import BaseCommand
from django.core.management import CommandError
from users.models import User
import getpass
import sys


class Command(BaseCommand):
    help = 'Create a superuser for TheraCare EHR system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            help='Email address for the superuser (this is the login field)',
        )
        parser.add_argument(
            '--password',
            help='Password for the superuser (not recommended for production)',
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            default=True,
            help='Prompt for username/email/password (default)',
        )
        parser.add_argument(
            '--noinput',
            action='store_false',
            dest='interactive',
            help='Do not prompt for input (requires --email and --password)',
        )
    
    def handle(self, *args, **options):
        """Create a superuser."""
        
        email = options.get('email')
        password = options.get('password')
        interactive = options.get('interactive', True)
        
        # Check if running interactively
        if interactive:
            try:
                # Get email (this is the login field)
                while not email:
                    email = input('Email address (login field): ')
                    if User.objects.filter(email=email).exists():
                        self.stdout.write(
                            self.style.ERROR(f'User with email "{email}" already exists.')
                        )
                        email = None
                
                # Get password
                while not password:
                    password = getpass.getpass('Password: ')
                    password_confirm = getpass.getpass('Password (again): ')
                    
                    if password != password_confirm:
                        self.stdout.write(
                            self.style.ERROR('Passwords do not match. Please try again.')
                        )
                        password = None
                    elif len(password) < 8:
                        self.stdout.write(
                            self.style.ERROR('Password must be at least 8 characters long.')
                        )
                        password = None
                
            except KeyboardInterrupt:
                self.stdout.write('\nOperation cancelled.')
                sys.exit(1)
        
        else:
            # Non-interactive mode - validate required arguments
            if not email or not password:
                raise CommandError(
                    'In non-interactive mode, you must specify --email and --password'
                )
            
            if User.objects.filter(email=email).exists():
                raise CommandError(f'User with email "{email}" already exists.')
        
        try:
            # Create the superuser
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name='Super',
                last_name='User',
                role='admin',
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Superuser "{email}" created successfully!'
                )
            )
            
            self.stdout.write(
                self.style.WARNING(
                    '\n📋 Login Information:'
                    f'\n   Email (Login): {email}'
                    f'\n   Role: Administrator'
                    '\n   Access: Full system access'
                    '\n\n📧 NOTE: Use EMAIL ADDRESS to login, not username!'
                    '\n⚠️  Keep these credentials secure!'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Error creating superuser: {str(e)}')