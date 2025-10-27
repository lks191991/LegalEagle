#!/usr/bin/env python3
"""
Test contact submissions from database
"""

from db_operations import DatabaseOperations

def test_contact_data():
    """Test if contact data exists in database"""
    print("Testing contact submissions...")
    
    try:
        # Get all contact submissions
        submissions = DatabaseOperations.get_all_contact_submissions()
        print(f"Found {len(submissions)} contact submissions:")
        
        for i, submission in enumerate(submissions, 1):
            print(f"\n{i}. ID: {submission.get('id')}")
            print(f"   Name: {submission.get('first_name')} {submission.get('last_name')}")
            print(f"   Email: {submission.get('email')}")
            print(f"   Phone: {submission.get('phone')}")
            print(f"   Status: {submission.get('status')}")
            print(f"   Created: {submission.get('created_at')}")
            print(f"   Message: {submission.get('message')[:50]}...")
            
        return submissions
        
    except Exception as e:
        print(f"Error testing contact data: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_contact_data()