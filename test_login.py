import requests
import json

LOGIN_URL = "https://user-field.aylanetworks.com/api/v1"

email = "family@seaburgfamily.com"
password = "hejWod-nekwuj-gixgu4"

login_data = {
    "user": {
        "email": email,
        "password": password,
        "application": {
            "app_id": "Shark-Home-IQ-id",
            "app_secret": "Shark-Home-IQ-db4e1b8f"
        }
    }
}

print(f"Attempting login with: {email}")
resp = requests.post(f"{LOGIN_URL}/users/sign_in.json", json=login_data)

print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
print(f"Response: {resp.text[:500]}")

try:
    print(f"JSON: {json.dumps(resp.json(), indent=2)}")
except:
    print("Response is not valid JSON")
