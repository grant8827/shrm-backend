#!/usr/bin/env python3
"""
Database cleanup script for TheraCare
Removes all test messages and demo users
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from messages.models import Message, MessageThread
from users.models import User

print('=== DATABASE CLEANUP ===\n')

# Delete all messages and threads
message_count = Message.objects.count()
thread_count = MessageThread.objects.count()

Message.objects.all().delete()
MessageThread.objects.all().delete()

print(f'✓ Deleted {message_count} messages')
print(f'✓ Deleted {thread_count} message threads')

# Delete test/demo users (keep only your real accounts)
# List users to keep - adjust this list to match your real accounts
users_to_keep = [
    'admin@theracare.local',  # Your admin account
    'grant8827@yahoo.com',     # Your account
]

# Delete all users except the ones to keep
deleted_users = []
for user in User.objects.all():
    if user.email not in users_to_keep:
        deleted_users.append(f'{user.email} ({user.role})')
        user.delete()

if deleted_users:
    print(f'\n✓ Deleted {len(deleted_users)} test users:')
    for u in deleted_users:
        print(f'  - {u}')
else:
    print('\n✓ No test users to delete')

# Show remaining users
print(f'\n=== REMAINING USERS ===')
for user in User.objects.all():
    print(f'  - {user.email} ({user.role})')

print(f'\n=== CLEANUP COMPLETE ===')
print(f'Messages: {Message.objects.count()}')
print(f'Threads: {MessageThread.objects.count()}')
print(f'Users: {User.objects.count()}')
