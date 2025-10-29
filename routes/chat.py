from fastapi import APIRouter, Request, Form, Cookie, Query
from fastapi.responses import HTMLResponse, JSONResponse
from template_config import templates
from typing import Optional
from services.rag import query_rag, query_rag_with_collection
from db_operations import DatabaseOperations

router = APIRouter()

@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request, user_session: Optional[str] = Cookie(None)):
    """Chat interface page"""
    from routes.auth import verify_user_session
    from db_operations import DatabaseOperations
    user_data = verify_user_session(user_session)
    if not user_data:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)
    user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
    if not user_plan:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/plan", status_code=302)
    return templates.TemplateResponse("chat.html", {
        "request": request, 
        "user": user_data,
        "user_plan": user_plan,
        "current_page": "chat"
    })



@router.get("/get-documents")
def get_documents(
    request: Request,
    user_session: Optional[str] = Cookie(None),
    limit: int = 5,
    offset: int = 0,
    search: Optional[str] = Query(None),
    sort_by: str = "recent"
):
    """Get available documents from MySQL database for the current user with filtering and pagination"""
    
    # Extract search from request query params
    actual_search = request.query_params.get('search')
    
    print(f"=== MYSQL DOCUMENTS API CALLED ===")
    print(f"Original search parameter: '{search}' (type: {type(search)})")
    print(f"Request query params: {dict(request.query_params)}")
    print(f"Direct extracted search: '{actual_search}' (type: {type(actual_search)})")
    
    # Use the directly extracted search parameter
    search = actual_search
    try:
        # Check user authentication
        from routes.auth import verify_user_session
        user_data = verify_user_session(user_session)
        if not user_data:
            return JSONResponse({"error": "Authentication required", "documents": [], "total": 0}, status_code=401)
        
        # Get documents from MySQL database instead of vector store
        print(f"=== CALLING MYSQL DATABASE ===")
        print(f"Getting documents for user {user_data['user_id']} with search='{search}'")
        
        documents, total = DatabaseOperations.get_user_documents_for_chat(
            user_id=int(user_data['user_id']),
            limit=limit, 
            offset=offset, 
            search=search, 
            sort_by=sort_by
        )
        
        print(f"DEBUG: Found {len(documents)}/{total} documents from MySQL for user {user_data['user_id']} with search='{search}'")
        if search:
            print(f"DEBUG: MySQL search '{search}' returned documents:")
            for doc in documents:
                print(f"  - {doc.get('document_name', 'Unknown')} (Collection: {doc.get('collection_name', 'Unknown')})")
        
        return JSONResponse({
            "documents": documents,
            "total": total,
            "has_more": offset + len(documents) < total,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        print(f"DEBUG: Error getting documents from MySQL: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return JSONResponse({"error": str(e), "documents": [], "total": 0})



@router.post("/chat")
async def chat_api(request: Request, user_session: Optional[str] = Cookie(None)):
    """Chat API endpoint with RAG functionality"""
    try:
        # Check user authentication
        from routes.auth import verify_user_session
        user_data = verify_user_session(user_session)
        if not user_data:
            return JSONResponse({
                "role": "assistant",
                "success": False,
                "answer": "Please login to use chat functionality",
                "sources": [],
                "error": True
            }, status_code=401)
        
        # Check prompt limit
        limit_check = DatabaseOperations.check_prompt_limit(int(user_data['user_id']))
        if not limit_check['can_prompt']:
            if 'message' in limit_check and 'No active plan' in limit_check['message']:
                error_message = "Please purchase a plan to use chat functionality. You don't have any active subscription plan."
            else:
                error_message = f"Chat prompt limit exceeded! You have used {limit_check['used']}/{limit_check['max']} prompts this month. Please upgrade your plan to continue chatting."
            
            return JSONResponse({
                "role": "assistant",
                "success": False,
                "answer": error_message,
                "sources": [],
                "error": True,
                "limit_exceeded": True,
                "limit_info": limit_check
            }, status_code=403)
        
        form_data = await request.form()
        message = form_data.get("message", "")
        selected_document = form_data.get("selected_document", "")
        
        print(f"DEBUG: Received form data: message='{message}', selected_document='{selected_document}'")
        
        if not message.strip():
            print("DEBUG: No message provided")
            return JSONResponse({
                "role": "assistant",
                "success": False,
                "answer": "Please provide a question.",
                "sources": [],
                "error": True
            }, status_code=400)

        # Get collection name from MySQL for the selected document
        doc_filter = None
        collection_name = None
        if selected_document and selected_document.strip():
            try:
                # Get document info from MySQL database
                user_docs = DatabaseOperations.get_user_documents(int(user_data['user_id']))
                found_doc = None
                
                # Try to match by document name first, then by collection name
                for doc in user_docs:
                    if doc['document_name'] == selected_document or doc['collection_name'] == selected_document:
                        found_doc = doc
                        collection_name = doc['collection_name']
                        doc_filter = doc['document_name']  # Use document name for search
                        print(f"DEBUG: Found document '{doc['document_name']}' (selected: '{selected_document}') with collection '{collection_name}'")
                        break
                
                if not found_doc:
                    print(f"DEBUG: Document '{selected_document}' not found in MySQL database")
                    print(f"DEBUG: Available documents: {[doc['document_name'] + ' (' + doc['collection_name'] + ')' for doc in user_docs]}")
                    return JSONResponse({
                        "role": "assistant",
                        "success": False,
                        "answer": f"Selected document '{selected_document}' not found in your document library.",
                        "sources": [],
                        "error": True
                    }, status_code=400)
                    
            except Exception as e:
                print(f"DEBUG: Error getting collection name: {str(e)}")
                return JSONResponse({
                    "role": "assistant",
                    "success": False,
                    "answer": f"Error accessing document information: {str(e)}",
                    "sources": [],
                    "error": True
                }, status_code=500)
        
        print(f"DEBUG: Chat request - message: {message}, selected_document: {selected_document}, collection_name: {collection_name}, user_id: {user_data['user_id']}")
        
        # Use RAG pipeline with collection name for vector search
        result = query_rag_with_collection(message, doc_filter, collection_name, user_id=int(user_data['user_id']))
        
        print(f"DEBUG: RAG result: {result}")
        
        # Save chat history
        import uuid
        session_id = form_data.get("session_id", str(uuid.uuid4()))
        print(f"DEBUG: Saving chat history for user {user_data['user_id']}, session {session_id}")
        
        try:
            chat_id = DatabaseOperations.save_chat_history(
                user_id=int(user_data['user_id']),
                session_id=session_id,
                user_query=message,
                ai_response=result["answer"],
                document_filter=doc_filter,
                sources=result.get("sources", [])
            )
            print(f"DEBUG: Chat history saved with ID: {chat_id}")
        except Exception as e:
            print(f"ERROR: Failed to save chat history: {e}")

        # Increment user's prompt usage count
        try:
            increment_success = DatabaseOperations.increment_prompt_usage(int(user_data['user_id']))
            print(f"DEBUG: Prompt usage increment success: {increment_success}")
        except Exception as e:
            print(f"ERROR: Failed to increment prompt usage: {e}")

        return JSONResponse({
            "role": "assistant",
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"] if result["sources"] else [],
            "error": False
        })

    except Exception as e:
        return JSONResponse({
            "role": "assistant",
            "success": False,
            "answer": f"Error processing your question: {str(e)}",
            "sources": [],
            "error": True
        }, status_code=500)