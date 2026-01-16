"""
Management command to check telehealth database table structure.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Check telehealth_session table structure and connection'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'telehealth_session'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.stdout.write(self.style.ERROR('❌ Table telehealth_session does not exist!'))
                return
            
            self.stdout.write(self.style.SUCCESS('✅ Table telehealth_session exists'))
            
            # Get all columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'telehealth_session'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            self.stdout.write(self.style.SUCCESS(f'\nTable has {len(columns)} columns:'))
            
            for col_name, data_type, nullable, default in columns:
                nullable_text = 'NULL' if nullable == 'YES' else 'NOT NULL'
                default_text = f'DEFAULT {default}' if default else ''
                self.stdout.write(f'  - {col_name}: {data_type} {nullable_text} {default_text}')
            
            # Check for foreign keys
            cursor.execute("""
                SELECT 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name='telehealth_session';
            """)
            
            fks = cursor.fetchall()
            if fks:
                self.stdout.write(self.style.SUCCESS(f'\nForeign keys:'))
                for col, ftable, fcol in fks:
                    self.stdout.write(f'  - {col} -> {ftable}.{fcol}')
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM telehealth_session;")
            count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'\nTotal sessions: {count}'))
