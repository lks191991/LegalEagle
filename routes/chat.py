from fastapi import APIRouter, Request, Form, Cookie, Query
from fastapi.responses import HTMLResponse, JSONResponse
from template_config import templates
from typing import Optional
from services.rag import query_rag
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
    """Get available document collections for the current user with filtering and pagination"""
    
    # DIRECT FIX: Extract search from request query params
    actual_search = request.query_params.get('search')
    
    print(f"=== API CALLED ===")
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
        
        from services.vector_store import VectorStore
        vector_store = VectorStore(user_id=int(user_data['user_id']))
        
        print(f"=== CALLING VECTOR STORE ===")
        print(f"Passing to vector store: search='{search}' (type: {type(search)})")
        
        documents, total = vector_store.get_available_documents(
            limit=limit, 
            offset=offset, 
            search=search, 
            sort_by=sort_by
        )
        print(f"DEBUG: Found {len(documents)}/{total} documents for user {user_data['user_id']} with search='{search}'")
        if search:
            print(f"DEBUG: Returned documents when searching for '{search}':")
            for doc in documents:
                print(f"  - {doc.get('document_name', 'Unknown')}")
        
        return JSONResponse({
            "documents": documents,
            "total": total,
            "has_more": offset + len(documents) < total,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        print(f"DEBUG: Error getting documents: {str(e)}")
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

        # Use RAG pipeline to get answer with document filter and user_id
        doc_filter = selected_document if selected_document else None
        print(f"DEBUG: Chat request - message: {message}, selected_document: {selected_document}, user_id: {user_data['user_id']}")
        result = query_rag(message, doc_filter, user_id=int(user_data['user_id']))
        
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