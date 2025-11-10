#!/usr/bin/env python3

import requests
import json

# Test chat history API directly
try:
    response = requests.get("http://localhost:8005/admin/api/chat-history")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Chat history count: {len(data.get('chat_history', []))}")
        print(f"Total: {data.get('total', 0)}")
        
except Exception as e:
    print(f"Error: {e}")