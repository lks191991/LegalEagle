#!/usr/bin/env python3
"""
Test contact form submission
"""

import requests
import json

def test_contact_form():
    """Test the contact form submission"""
    url = "http://127.0.0.1:8004/submit-contact"
    
    # Test data
    form_data = {
        'firstName': 'John',
        'lastName': 'Doe', 
        'email': 'john.doe@example.com',
        'phone': '+1-555-123-4567',
        'message': 'This is a test message from the contact form. I am interested in learning more about LegalEagle services for my law firm.'
    }
    
    try:
        print("Testing contact form submission...")
        print(f"Submitting to: {url}")
        print(f"Data: {form_data}")
        
        response = requests.post(url, data=form_data)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Contact form submission successful!")
                print(f"Message: {result.get('message')}")
                if result.get('email_sent'):
                    print("✅ Email notification sent to admin")
                else:
                    print("⚠️ Email notification not sent (check email configuration)")
            else:
                print(f"❌ Contact form submission failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running on http://127.0.0.1:8004")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_contact_form()