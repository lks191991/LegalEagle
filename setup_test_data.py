#!/usr/bin/env python3
"""
Add sample document to test MySQL collection integration
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_operations import DatabaseOperations
from datetime import datetime

def add_sample_document():
    """Add a sample document to test the integration"""
    
    print("🔄 Adding sample document for testing...")
    
    try:
        # Sample document data
        user_id = 1
        document_name = "Sample Legal Contract"
        collection_name = f"user_{user_id}_sample_legal_contract"
        current_date = datetime.now().strftime("%d-%m-%Y")
        
        # Add sample document to database
        doc_id = DatabaseOperations.save_user_document(
            user_id=user_id,
            filename="sample_contract.pdf",
            original_filename="sample_contract.pdf", 
            document_name=document_name,
            file_size=1024000,  # 1MB
            file_type="application/pdf",
            collection_name=collection_name,
            tags="contract, legal, sample",
            document_date=current_date,
            created_date=current_date,
            chunk_count=5
        )
        
        print(f"✅ Sample document added with ID: {doc_id}")
        print(f"  - Document Name: {document_name}")
        print(f"  - Collection Name: {collection_name}")
        print(f"  - User ID: {user_id}")
        
        # Also add to user collections
        collection_saved = DatabaseOperations.save_user_collection(
            user_id=user_id,
            collection_name=collection_name,
            document_name=document_name
        )
        
        print(f"✅ Collection mapping saved: {collection_saved}")
        
        # Verify document was added
        documents = DatabaseOperations.get_user_documents(user_id)
        print(f"✅ Total documents for user {user_id}: {len(documents)}")
        
        for doc in documents:
            print(f"  - {doc['document_name']} ({doc['collection_name']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample document: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_user_exists():
    """Check if test user exists, create if not"""
    
    try:
        user = DatabaseOperations.get_user_by_id(1)
        if not user:
            print("⚠️ Test user (ID=1) does not exist. Creating...")
            
            # Create test user
            success = DatabaseOperations.create_user(
                name="Test User",
                email="test@example.com",
                password="testpassword123",
                mobile_number="1234567890"
            )
            
            if success:
                print("✅ Test user created successfully")
                return True
            else:
                print("❌ Failed to create test user")
                return False
        else:
            print(f"✅ Test user exists: {user['name']} ({user['email']})")
            return True
            
    except Exception as e:
        print(f"❌ Error checking user: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up test data for MySQL collection integration...\n")
    
    # Check/create test user
    user_ok = check_user_exists()
    if not user_ok:
        print("❌ Could not setup test user")
        exit(1)
    
    # Add sample document
    doc_added = add_sample_document()
    if doc_added:
        print(f"\n🎉 Test data setup completed successfully!")
        print(f"You can now run: python test_mysql_collection_integration.py")
    else:
        print(f"\n❌ Test data setup failed!")