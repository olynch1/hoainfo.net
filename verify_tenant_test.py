import requests

# ✅ Valid landlord token (matching the correct landlord_id in DB)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsYW5kbG9yZEBleGFtcGxlLmNvbSIsImlkIjoiNDEyNGZjOTAtMzRmZS00MGQzLTkyYmYtNzhlMmQxOGEyNTBjIiwiZW1haWwiOiJsYW5kbG9yZEBleGFtcGxlLmNvbSIsInJvbGUiOiJsYW5kbG9yZCIsImNvbW11bml0eV9pZCI6IjAwMDAxIiwiZXhwIjoxNzQ3MDgxMjg5fQ.jVWjO-URzpnnbOFH_gx6MOdTNxdUKcjZOYiLYsM8sM8"

headers = {
    "Authorization": f"Bearer {token}"
}

data = {
    "email": "tenant_test@example.com"  # Make sure this email matches an existing pending invite
}

response = requests.post("http://localhost:8000/verify-tenant", json=data, headers=headers)

print("✅ Verify Tenant Response:")
print(response.status_code)
try:
    print(response.json())
except Exception as e:
    print(f"❌ Failed to decode response JSON: {e}")
    print(response.text)

