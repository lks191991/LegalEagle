import requests

# Test API directly
try:
    response = requests.get("http://localhost:8005/admin/api/chat-history")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")