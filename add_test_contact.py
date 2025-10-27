#!/usr/bin/env python3
"""
Add test contact submission
"""

from db_operations import DatabaseOperations

def add_test_contact():
    """Add a test contact submission"""
    success = DatabaseOperations.save_contact_submission(
        name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-0123",
        message="This is a test message to check if the contact system is working properly. I'm interested in learning more about LegalEagle's features."
    )
    
    if success:
        print("Test contact submission added successfully!")
        return True
    else:
        print("Failed to add test contact submission")
        return False

if __name__ == "__main__":
    add_test_contact()