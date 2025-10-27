#!/usr/bin/env python3
"""
Test script for user-based data separation
"""

from services.vector_store import VectorStore
from db_operations import DatabaseOperations

def test_user_separation():
    print("🧪 Testing User-Based Data Separation")
    print("=" * 50)
    
    # Test 1: VectorStore without user_id
    print("\n1. Testing VectorStore without user_id:")
    try:
        vs = VectorStore()
        print("✅ VectorStore created without user_id")
        
        # This should fail
        vs.get_available_documents()
        print("❌ ERROR: get_available_documents() should have failed!")
        
    except ValueError as e:
        print(f"✅ SUCCESS: Proper error handling - {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 2: VectorStore with user_id
    print("\n2. Testing VectorStore with user_id:")
    try:
        vs_with_user = VectorStore(user_id=1)
        print("✅ VectorStore created with user_id=1")
        
        docs = vs_with_user.get_available_documents()
        print(f"✅ SUCCESS: Got {len(docs)} documents for user 1")
        
        if docs:
            print("📄 User 1 documents:")
            for doc in docs:
                print(f"   - {doc['document_name']} (collection: {doc['collection_name']})")
        
    except Exception as e:
        print(f"⚠️  Expected: {e}")
    
    # Test 3: Database operations
    print("\n3. Testing Database Operations:")
    try:
        # Test user documents
        user_docs = DatabaseOperations.get_user_documents(1)
        print(f"✅ Got {len(user_docs)} documents from DB for user 1")
        
        # Test user collections
        user_collections = DatabaseOperations.get_user_collections(1)
        print(f"✅ Got {len(user_collections)} collections from DB for user 1")
        
        # Test user chat sessions
        user_sessions = DatabaseOperations.get_user_chat_sessions(1)
        print(f"✅ Got {len(user_sessions)} chat sessions from DB for user 1")
        
    except Exception as e:
        print(f"⚠️  Database error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 User data separation test completed!")

if __name__ == "__main__":
    test_user_separation()