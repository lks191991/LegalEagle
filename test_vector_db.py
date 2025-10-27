#!/usr/bin/env python3
"""Test script to check vector database connection and functionality"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_vector_db():
    print("🔍 Testing Vector Database Connection...")
    
    try:
        from services.vector_store import VectorStore
        
        # Test 1: Basic connection
        print("\n1. Testing basic connection...")
        vector_store = VectorStore(user_id=1)
        print("✅ VectorStore initialized successfully")
        
        # Test 2: Get available documents
        print("\n2. Testing get_available_documents...")
        documents = vector_store.get_available_documents()
        print(f"✅ Found {len(documents)} documents:")
        for doc in documents:
            print(f"   - {doc.get('document_name', 'Unknown')} ({doc.get('collection_name', 'No collection')})")
        
        # Test 3: Test search if documents exist
        if documents:
            print(f"\n3. Testing search in first document...")
            first_doc = documents[0]['collection_name']
            results = vector_store.search("test", limit=3, document_name=first_doc)
            print(f"✅ Search returned {len(results)} results")
            for i, result in enumerate(results):
                print(f"   Result {i+1}: {result['text'][:100]}...")
        else:
            print("\n3. No documents found to test search")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_system():
    print("\n🤖 Testing RAG System...")
    
    try:
        from services.rag import query_rag
        
        # Test with a simple query
        result = query_rag(
            query="What is this document about?",
            doc_filter=None,  # Will test document selection requirement
            user_id=1
        )
        
        print(f"✅ RAG system response: {result['answer'][:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ RAG Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🦅 LegalEagle Vector Database Test")
    print("=" * 50)
    
    # Test vector database
    vector_success = test_vector_db()
    
    # Test RAG system
    rag_success = test_rag_system()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Vector DB: {'✅ PASS' if vector_success else '❌ FAIL'}")
    print(f"RAG System: {'✅ PASS' if rag_success else '❌ FAIL'}")
    
    if vector_success and rag_success:
        print("\n🎉 All tests passed! Vector DB is working properly.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")