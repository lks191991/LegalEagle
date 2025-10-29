#!/usr/bin/env python3
"""
Test script to verify MySQL collection name integration with vector database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_operations import DatabaseOperations
from services.vector_store import VectorStore
from dotenv import load_dotenv

load_dotenv()

def test_mysql_documents_integration():
    """Test MySQL documents integration for chat functionality"""
    
    print("🔄 Testing MySQL Collection Integration...")
    
    # Test user ID (you may need to adjust this)
    test_user_id = 1
    
    try:
        # 1. Test getting user documents from MySQL
        print(f"\n1. Testing MySQL document retrieval for user {test_user_id}...")
        documents = DatabaseOperations.get_user_documents(test_user_id)
        print(f"✅ Found {len(documents)} documents in MySQL database")
        
        if not documents:
            print("⚠️ No documents found. Please upload a document first.")
            return False
        
        # Display documents
        for i, doc in enumerate(documents[:3]):
            print(f"  Document {i+1}:")
            print(f"    - Name: {doc['document_name']}")
            print(f"    - Collection: {doc['collection_name']}")
            print(f"    - Upload Date: {doc['upload_date']}")
            print(f"    - Chunks: {doc['chunk_count']}")
        
        # 2. Test formatted documents for chat
        print(f"\n2. Testing formatted documents for chat interface...")
        formatted_docs, total = DatabaseOperations.get_user_documents_for_chat(
            user_id=test_user_id, 
            limit=5, 
            offset=0, 
            search=None, 
            sort_by="recent"
        )
        print(f"✅ Formatted {len(formatted_docs)}/{total} documents for chat")
        
        # 3. Test search functionality
        if formatted_docs:
            print(f"\n3. Testing document search...")
            search_docs, search_total = DatabaseOperations.get_user_documents_for_chat(
                user_id=test_user_id,
                limit=5,
                offset=0,
                search="contract",  # Change this to match your documents
                sort_by="recent"
            )
            print(f"✅ Search for 'contract' found {len(search_docs)}/{search_total} documents")
        
        # 4. Test collection name retrieval for vector search
        print(f"\n4. Testing collection name resolution...")
        test_doc = documents[0]  # Use first document
        doc_name = test_doc['document_name']
        collection_name = test_doc['collection_name']
        
        print(f"  - Document Name: {doc_name}")
        print(f"  - Collection Name: {collection_name}")
        
        # 5. Test vector store with collection name
        print(f"\n5. Testing vector store with collection name...")
        vector_store = VectorStore(user_id=test_user_id)
        
        # Test if collection exists in Qdrant
        collections = vector_store.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name in collection_names:
            print(f"✅ Collection '{collection_name}' exists in Qdrant")
            
            # Test search in collection
            results = vector_store.search_in_collection("test query", collection_name, limit=2)
            print(f"✅ Search in collection returned {len(results)} results")
            
            if results:
                print(f"  - First result: {results[0]['text'][:100]}...")
        else:
            print(f"❌ Collection '{collection_name}' not found in Qdrant")
            print(f"Available collections: {collection_names}")
        
        print(f"\n🎉 MySQL Collection Integration Test Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_chat_workflow():
    """Test complete chat workflow with MySQL integration"""
    
    print(f"\n🔄 Testing Complete Chat Workflow...")
    
    test_user_id = 1
    
    try:
        # Get user documents
        documents = DatabaseOperations.get_user_documents(test_user_id)
        if not documents:
            print("❌ No documents available for testing")
            return False
        
        # Simulate chat request
        test_doc = documents[0]
        doc_name = test_doc['document_name'] 
        collection_name = test_doc['collection_name']
        
        print(f"Testing chat with document: {doc_name}")
        print(f"Using collection: {collection_name}")
        
        # Import RAG function
        from services.rag import query_rag_with_collection
        
        # Test query
        test_query = "What is this document about?"
        
        result = query_rag_with_collection(
            query=test_query,
            doc_filter=doc_name,
            collection_name=collection_name,
            user_id=test_user_id
        )
        
        print(f"✅ Chat response generated:")
        print(f"  - Answer length: {len(result['answer'])} characters")
        print(f"  - Sources: {len(result['sources'])} sources")
        print(f"  - Answer preview: {result['answer'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Chat workflow test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Starting MySQL Collection Integration Tests...\n")
    
    # Test 1: MySQL integration
    test1_passed = test_mysql_documents_integration()
    
    # Test 2: Chat workflow  
    test2_passed = test_chat_workflow()
    
    print(f"\n📊 Test Results:")
    print(f"  - MySQL Integration: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  - Chat Workflow: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 All tests passed! MySQL collection integration is working correctly.")
    else:
        print(f"\n⚠️ Some tests failed. Please check the errors above.")