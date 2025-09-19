import os
from services.vector_store import VectorStore

# Try to import OpenAI and Transformers
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not installed. Install with: pip install openai")

try:
    from transformers import pipeline
    HF_AVAILABLE = True
    print("Loading free AI model for intelligent answers...")
    # Load a free question-answering model
    qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
except ImportError:
    HF_AVAILABLE = False
    qa_pipeline = None
    print("Transformers not installed. Install with: pip install transformers torch")

def query_rag(query, doc_filter=None):
    """
    RAG pipeline: Retrieve relevant chunks and generate answer using OpenAI
    """
    try:
        print(f"Starting RAG query for: {query}")
        
        # Initialize vector store
        print("Initializing vector store...")
        vector_store = VectorStore()
        
        # Search for relevant chunks
        print("Searching for relevant chunks...")
        search_results = vector_store.search(query, limit=3)
        print(f"Found {len(search_results)} search results")
    except Exception as e:
        print(f"Vector store error: {str(e)}")
        return {
            "answer": f"Vector database error: {str(e)}",
            "sources": []
        }
    
    if not search_results:
        return {
            "answer": "I couldn't find relevant information in the uploaded documents.",
            "sources": []
        }
    
    # Prepare context from search results
    context = "\n\n".join([
        f"Document: {result['filename']}, Page: {result.get('page', 'N/A')}\n{result['text']}"
        for result in search_results
    ])
    
    # Try OpenAI first, fallback to simple search
    openai_api_key = os.getenv("OPENAI_API_KEY")
    print(f"OpenAI available: {OPENAI_AVAILABLE}")
    print(f"API key present: {'Yes' if openai_api_key else 'No'}")
    
    if OPENAI_AVAILABLE and openai_api_key:
        try:
            print("Attempting OpenAI API call...")
            # Initialize OpenAI client
            client = OpenAI(api_key=openai_api_key)
           #client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
            # Generate intelligent answer using OpenAI
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gemma:2b"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are LegalEagle, a helpful legal assistant. Answer questions based on the provided context. Be concise and helpful."
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}\n\nPlease provide a helpful answer based on the context above."
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            
            # Prepare sources
            sources = []
            for result in search_results:
                source = result['filename']
                if result.get('page'):
                    source += f" (Page {result['page']})"
                sources.append(source)
            
            return {
                "answer": f"🦅 {answer}",
                "sources": sources
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"OpenAI Error: {error_msg}")
            if "quota" in error_msg.lower() or "429" in error_msg:
                print("Quota exceeded, falling back to search mode")
                # Fallback to search-only mode
                pass
            else:
                print(f"Other OpenAI error: {error_msg}")
                return {
                    "answer": f"OpenAI Error: {error_msg}\n\nFalling back to document search...",
                    "sources": []
                }
    
    # Try free Hugging Face model as backup
    if HF_AVAILABLE and qa_pipeline:
        try:
            print("Using free AI model for intelligent answer...")
            
            # Use the most relevant chunk for AI processing
            best_result = search_results[0]
            context_text = best_result['text']
            
            print(f"Context length: {len(context_text)} characters")
            
            # Limit context length for the model
            if len(context_text) > 1500:  # Larger context for better legal document understanding
                context_text = context_text[:1500]
                print(f"Truncated context to: {len(context_text)} characters")
            
            print("Calling AI model...")
            try:
                # Get AI answer using free model with timeout handling
                ai_result = qa_pipeline(question=query, context=context_text)
                print("AI model responded successfully")
            except Exception as model_error:
                print(f"AI model call failed: {model_error}")
                raise model_error
            
            ai_answer = ai_result['answer']
            confidence = ai_result['score']
            
            print(f"AI Answer: {ai_answer}")
            print(f"AI Confidence: {confidence:.3f}")
            
            if confidence > 0.0005:  # Very low threshold for legal documents
                # Check if AI answer matches the query context
                query_lower = query.lower()
                answer_lower = ai_answer.lower()
                context_lower = best_result['text'][:200].lower()
                
                # If query has specific terms that should appear in answer
                key_terms = ['personation', 'false personation', 'suit', 'prosecution']
                query_has_terms = any(term in query_lower for term in key_terms)
                answer_has_terms = any(term in answer_lower for term in key_terms)
                context_has_terms = any(term in context_lower for term in key_terms)
                
                if query_has_terms and context_has_terms and not answer_has_terms:
                    # AI gave wrong answer, show document text instead
                    answer = f"🔍 Found relevant section:\n\n{best_result['text'][:400]}..."
                else:
                    # Format the AI answer properly
                    answer = f"🤖 {ai_answer}"
                    
                    # Add more context for better understanding
                    if len(ai_answer) < 50:
                        answer += f"\n\n📝 Complete text: {best_result['text'][:300]}..."
                
                sources = []
                for result in search_results[:2]:
                    source = result['filename']
                    if result.get('page'):
                        source += f" (Page {result['page']})"
                    sources.append(source)
                
                return {
                    "answer": answer,
                    "sources": sources
                }
            else:
                print(f"AI confidence too low ({confidence:.3f}), showing document text")
                # Show document text when confidence is low
                answer = f"🔍 Most relevant section:\n\n{best_result['text'][:400]}..."
                
                sources = []
                for result in search_results[:1]:
                    source = result['filename']
                    if result.get('page'):
                        source += f" (Page {result['page']})"
                    sources.append(source)
                
                return {
                    "answer": answer,
                    "sources": sources
                }
                
        except Exception as e:
            print(f"Free AI model error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("Using document search mode")
    
    # Fallback: Generate answer from retrieved chunks
    try:
        # Take only the most relevant result
        best_result = search_results[0]
        
        # Clean and format the text with proper paragraphs
        text = best_result['text'].strip()
        
        # Add proper paragraph breaks for better readability
        # Split by periods followed by capital letters (new sentences)
        import re
        
        # Add line breaks after section numbers and before new sections
        text = re.sub(r'(\d+\.[^\n]+?\.)—', r'\1\n\n—', text)
        
        # Add breaks after long sentences
        text = re.sub(r'(\. )([A-Z])', r'.\n\n\2', text)
        
        # Clean up multiple line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        answer = f"🔍 {text}"
        
        # Use only the best result
        search_results = [best_result]
        
        sources = []
        for result in search_results:
            source = result['filename']
            if result.get('page'):
                source += f" (Page {result['page']})"
            sources.append(source)
        
        return {
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        return {
            "answer": f"Error processing search results: {str(e)}",
            "sources": []
        }