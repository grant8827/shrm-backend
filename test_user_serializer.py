#!/usr/bin/env python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from users.models import User
from users.serializers import UserListSerializer

# Get all users
users = User.objects.all().order_by("-date_joined")
print(f"Total users in DB: {users.count()}")

# Serialize them
serializer = UserListSerializer(users, many=True)
print(f"\nSerialized data:")
import json

print(json.dumps(serializer.data, indent=2, default=str))

# Check active clients specifically
active_clients = User.objects.filter(role="client", is_active=True)
print(f"\n\nActive clients: {active_clients.count()}")
client_serializer = UserListSerializer(active_clients, many=True)
print("Serialized client data:")
print(json.dumps(client_serializer.data, indent=2, default=str))
