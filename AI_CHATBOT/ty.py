import requests
import json

url = "http://localhost:8000/"

# Test message that should trigger web search
payload = {
    "name": "interact",
    "ctx": {
        "message": "Use web search to find current vice chancellor of Kenyatta University",
        "session_id": "test_session_123"
    }
}

response = requests.post(url, json=payload)
print("Status Code:", response.status_code)
print("Response:", response.json())