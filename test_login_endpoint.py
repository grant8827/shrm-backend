#!/usr/bin/env python3
"""
Test the login endpoint directly
"""
import requests
import json

# Test against Railway production
backend_url = "https://shrm-backend-production.up.railway.app"

print("=" * 80)
print("TESTING LOGIN ENDPOINT")
print("=" * 80)

# Login credentials
credentials = {
    "username": "grant8827",
    "password": "AdminPass123!"
}

print(f"\nBackend URL: {backend_url}")
print(f"Credentials: {json.dumps(credentials, indent=2)}")

try:
    # Test login
    response = requests.post(
        f"{backend_url}/api/auth/login/",
        json=credentials,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"\nResponse Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("\n✓ LOGIN SUCCESSFUL!")
        data = response.json()
        print(f"\nResponse Data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"\n✗ LOGIN FAILED!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
