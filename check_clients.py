#!/usr/bin/env python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from users.models import User

total = User.objects.count()
clients = User.objects.filter(role="client", is_active=True).count()

print(f"Total users: {total}")
print(f"Active clients: {clients}")
print("\nAll users:")
for u in User.objects.all()[:10]:
    print(f"  - {u.username}: role={u.role}, is_active={u.is_active}, email={u.email}")

print("\nActive client users:")
for u in User.objects.filter(role="client", is_active=True)[:10]:
    print(f"  - {u.username}: {u.get_full_name()} ({u.email})")
