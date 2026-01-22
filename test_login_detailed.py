#!/usr/bin/env python3
"""
Test login with detailed debugging
"""
import requests
import json

backend_url = "https://shrm-backend-production.up.railway.app"

print("=" * 80)
print("DETAILED LOGIN TEST")
print("=" * 80)

# Test different credential formats
test_cases = [
    {"username": "grant8827", "password": "AdminPass123!"},
    {"email": "grant88271@gmail.com", "password": "AdminPass123!"},
]

for i, credentials in enumerate(test_cases, 1):
    print(f"\n--- Test Case {i} ---")
    print(f"Credentials: {json.dumps(credentials, indent=2)}")
    
    try:
        response = requests.post(
            f"{backend_url}/api/auth/login/",
            json=credentials,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ SUCCESS!")
            data = response.json()
            print(f"User: {data['user']['username']} ({data['user']['email']})")
            print(f"Role: {data['user']['role']}")
        else:
            print(f"✗ FAILED")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ ERROR: {e}")

print("\n" + "=" * 80)
print("TROUBLESHOOTING")
print("=" * 80)
print("\nIf login works here but not in browser:")
print("1. Clear browser cache and cookies")
print("2. Try incognito/private mode")
print("3. Check browser console for errors (F12)")
print("4. Verify frontend is calling correct API URL")
print("5. Check CORS errors in browser console")
