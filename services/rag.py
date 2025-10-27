import os
from services.vector_store import VectorStore

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not installed. Install with: pip install openai")


def query_rag(query, doc_filter=None, user_id=None):
    """
    RAG Pipeline: User Question → Vector Search → Context Retrieval → AI Processing → Intelligent Answer
    """
    print(f"🔍 Step 1: Processing user question: {query}")
    
    # Validate user_id is provided
    if not user_id:
        return {
            "answer": "❌ User authentication required for document access.",
            "sources": []
        }
    
    # Step 2: Vector Search (MANDATORY document selection)
    if not doc_filter:
        return {
            "answer": "❌ Please select a document first. Document selection is mandatory.",
            "sources": []
        }
    
    try:
        print(f"🔍 Step 2: Vector search in user's selected document: {doc_filter}")
        vector_store = VectorStore(user_id=user_id)
        
        # Primary search with original query - get more chunks for consistency
        raw_results = vector_store.search(query, limit=10, document_name=doc_filter)
        print(f"📊 Raw search found {len(raw_results)} chunks")
        
        # Use all results from vector store (it already filtered by document)
        search_results = raw_results
        print(f"✅ Using {len(search_results)} results from vector store")
        for i, result in enumerate(search_results):
            score = result.get('score', 0)
            print(f"Result {i+1} (score: {score:.3f}) from {result.get('filename', 'Unknown')}: {result['text'][:100]}...")
        
        # If no valid results, try multiple search strategies
        if not search_results:
            print(f"🔍 No results found, trying multiple search strategies...")
            
            # Strategy 1: Individual key terms
            key_terms = ["constitutional", "labour", "provisions", "dignity", "fundamental", "directive", "parliament"]
            for term in key_terms:
                print(f"🔍 Strategy 1 - Searching: '{term}'")
                term_raw = vector_store.search(term, limit=5, document_name=doc_filter)
                # Use all results from term search
                search_results.extend(term_raw)
                if term_raw:
                    print(f"✅ Found {len(term_raw)} results with '{term}'")
                if len(search_results) >= 3:
                    break
            
            # Strategy 2: Try partial phrases
            if not search_results:
                phrases = ["constitutional provisions", "labour laws", "human labour", "fundamental rights"]
                for phrase in phrases:
                    print(f"🔍 Strategy 2 - Searching phrase: '{phrase}'")
                    phrase_raw = vector_store.search(phrase, limit=3, document_name=doc_filter)
                    # Use all results from phrase search
                    search_results.extend(phrase_raw)
                    if phrase_raw:
                        print(f"✅ Found {len(phrase_raw)} results with phrase '{phrase}'")
                    if search_results:
                        break
            
            # Strategy 3: Get any content from the document to verify it exists
            if not search_results:
                print(f"🔍 Strategy 3 - Getting any content from document to verify it exists")
                any_content = vector_store.search("the", limit=10, document_name=doc_filter)
                print(f"📊 Document '{doc_filter}' has {len(any_content)} total chunks")
                
                if any_content:
                    # Look for constitutional content in any chunks
                    for result in any_content:
                        text_lower = result['text'].lower()
                        if "constitutional" in text_lower or "labour" in text_lower or "provision" in text_lower:
                            search_results.append(result)
                            print(f"✅ Found relevant content: {result['text'][:150]}...")
                    
                    # If still no results, show sample content
                    if not search_results:
                        print(f"📊 Sample content from document:")
                        for i, result in enumerate(any_content[:3]):
                            print(f"  Chunk {i+1}: {result['text'][:100]}...")
        
        print(f"✅ Final validated results: {len(search_results)} chunks from correct document")
            
    except Exception as e:
        print(f"❌ Vector search failed: {str(e)}")
        return {
            "answer": f"Vector database error: {str(e)}",
            "sources": []
        }
    
    if not search_results:
        return {
            "answer": f"❌ No content found for '{query}' in document '{doc_filter}'. Please check if you have selected the correct document or try different search terms.",
            "sources": []
        }
    
    # Step 3: Context Retrieval
    print(f"🔍 Step 3: Retrieving context from {len(search_results)} chunks")
    
    # Use all search results (vector store already filtered by document)
    for i, result in enumerate(search_results):
        print(f"📄 Using chunk {i+1} from {result.get('filename', 'Unknown')}: {result['text'][:150]}...")
    
    # Sort results by score to ensure consistent ordering
    search_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    context = "\n\n".join([
        f"Document: {result.get('filename', 'Document')}, Page: {result.get('page', 'N/A')}\n{result['text']}"
        for result in search_results
    ])
    print(f"✅ Context prepared from {len(search_results)} chunks ({len(context)} characters)")
    
    # Step 4: AI Processing
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if OPENAI_AVAILABLE and openai_api_key:
        try:
            print(f"🤖 Step 4: AI processing with OpenAI")
            client = OpenAI(api_key=openai_api_key)
            
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are LegalEagle. Answer STRICTLY based on the document context provided. Be comprehensive and include ALL relevant information from the context. Never use general knowledge."
                    },
                    {
                        "role": "user",
                        "content": f"Context from document:\n{context}\n\nQuestion: {query}\n\nProvide a complete answer using ALL relevant information from the context above. Include all Articles, Chapters, and provisions mentioned."
                    }
                ],
                max_tokens=500,
                temperature=0.0
            )
            
            answer = response.choices[0].message.content
            
            # Prepare sources
            sources = []
            for result in search_results:
                source = result['filename']
                if result.get('page'):
                    source += f" (Page {result['page']})"
                sources.append(source)
            
            # Check if OpenAI says not found but we have search results
            if "information not found" in answer.lower() or "not found in document" in answer.lower():
                print(f"⚠️ OpenAI says not found, but we have {len(search_results)} chunks. Falling back to similarity check.")
                # Fall through to document content mode
            else:
                # Step 5: Intelligent Answer
                print(f"✅ Step 5: Generated intelligent answer")
                return {
                    "answer": f"🦅 {answer}",
                    "sources": sources
                }
            
        except Exception as e:
            print(f"❌ AI processing failed: {str(e)}")
            # Continue to fallback
    
    # Fallback: Document content mode
    print(f"🔍 Step 4-5: Fallback to document content mode")
    try:
        best_result = search_results[0]
        best_score = best_result.get('score', 0)
        doc_name = best_result.get('document_name', 'Unknown')
        doc_title = best_result.get('document_name', doc_name)  # <-- use document_name if present
        print(f"📄 Best result: score={best_score}, filename={doc_name}, title={doc_title}")
        
        # Check if the similarity score is too low (content not relevant)
        print(f"🔍 Checking similarity threshold: best_score={best_score}, threshold=0.3")
        if best_score < 0.3:  # Low similarity threshold
            print(f"❌ Score {best_score} is below threshold 0.3 - query not relevant to document")
            return {
                "answer": f"❌ The query '{query}' is not relevant to the content in '{doc_title}'. This document appears to be about different topics. Please select a more appropriate document or try different search terms.",
                "sources": []
            }
        else:
            print(f"✅ Score {best_score} is above threshold 0.3 - showing document content")
        
        # Show the most relevant result
        best_text = best_result['text']
        page_info = f" (Page {best_result.get('page', 'N/A')})" if best_result.get('page') else ""
        answer = f"📄 Found in {doc_name}{page_info}:\n\n{best_text[:700]}..."
        
        sources = []
        for result in search_results[:2]:
            source = result.get('filename', 'Unknown Document')
            if result.get('page'):
                source += f" (Page {result['page']})"
            sources.append(source)
        
        return {
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        print(f"❌ Document processing error: {str(e)}")
        return {
            "answer": f"Error: {str(e)}",
            "sources": []
        }

# The query_rag function already implements:
# 1. User Question → 2. Vector Search → 3. Context Retrieval → 4. AI Processing → 5. Intelligent Answer