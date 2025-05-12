import requests

# Replace with the correct landlord JWT token
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsYW5kbG9yZEBleGFtcGxlLmNvbSIsImlkIjoiNDEyNGZjOTAtMzRmZS00MGQzLTkyYmYtNzhlMmQxOGEyNTBjIiwicm9sZSI6ImxhbmRsb3JkIiwiY29tbXVuaXR5X2lkIjoiMDAwMDEiLCJleHAiOjE3NDcwMjg2ODN9.svpmvLIWL5oynfmlenicmwPNewpfGvZBZydsLs3lDL4"
}

# Test data for inviting a tenant
data = {
    "email": "tenant_test@example.com"
}

# Make the POST request
response = requests.post("http://localhost:8000/invite-tenant", json=data, headers=headers)

# Print the status and response
print("📨 Invite Tenant Response:")
print(response.status_code)
try:
    print(response.json())
except Exception as e:
    print(response.text)


