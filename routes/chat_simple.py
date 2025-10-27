from fastapi import APIRouter, Request, Cookie, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from template_config import templates
from typing import Optional
from routes.auth import verify_user_session
from db_operations import DatabaseOperations

router = APIRouter()

@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request, user_session: Optional[str] = Cookie(None)):
    """Chat interface page"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
    if not user_plan:
        return RedirectResponse(url="/plan?message=chat_access&feature=Chat with AI", status_code=302)
    return templates.TemplateResponse("chat.html", {
        "request": request, 
        "user": user_data,
        "user_plan": user_plan,
        "current_page": "chat"
    })

@router.post("/chat")
async def chat_submit(
    request: Request,
    question: str = Form(...),
    document_name: str = Form(None),
    user_session: Optional[str] = Cookie(None)
):
    """Handle chat submissions"""
    try:
        # Check user authentication
        user_data = verify_user_session(user_session)
        if not user_data:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        # Check user plan
        user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
        if not user_plan:
            return JSONResponse({"error": "Please subscribe to a plan to use chat feature"}, status_code=403)
        
        # Use RAG system to get actual data from vector DB
        from services.rag import query_rag
        
        try:
            user_id = user_data.get('user_id')
            
            # Call RAG system
            rag_result = query_rag(
                query=question,
                doc_filter=document_name,
                user_id=user_id
            )
            
            raw_answer = rag_result.get('answer', 'No response generated')
            sources = rag_result.get('sources', [])
            
            # Format response with structure
            if "summary" in question.lower():
                response_text = f"📋 **Document Summary:**\n\n{raw_answer}\n\n💡 **Key Points:** Review main sections and consult legal counsel"
            elif "clause" in question.lower():
                response_text = f"📜 **Legal Analysis:**\n\n{raw_answer}\n\n⚖️ **Recommendation:** Review with legal counsel for interpretation"
            elif "date" in question.lower():
                response_text = f"📅 **Date Analysis:**\n\n{raw_answer}\n\n⏰ **Action:** Mark important dates in calendar"
            elif "payment" in question.lower():
                response_text = f"💰 **Payment Analysis:**\n\n{raw_answer}\n\n💳 **Planning:** Budget for all obligations"
            else:
                response_text = f"🔍 **Document Analysis:**\n\n{raw_answer}"
            
            # Sources hidden as requested
            # if sources:
            #     response_text += f"\n\n📚 **Sources:** {', '.join(sources)}"
                
        except Exception as e:
            response_text = f"❌ **Error:** Unable to access document data: {str(e)}\n\n🔧 **Solution:** Ensure documents are uploaded and try again"
        
        return JSONResponse({
            "success": True,
            "response": response_text,
            "question": question,
            "document_name": document_name
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/suggestions")
def get_suggestions(q: str, doc: str = None, user_session: Optional[str] = Cookie(None)):
    """Get chat suggestions based on query"""
    try:
        # Check user authentication
        user_data = verify_user_session(user_session)
        if not user_data:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        # Basic suggestions based on query
        suggestions = []
        if len(q) >= 2:  # Only suggest for 2+ characters
            base_suggestions = [
                "What are the key points in this document?",
                "Can you summarize the main clauses?",
                "What are the legal implications?",
                "Are there any important dates mentioned?",
                "What are the parties' obligations?",
                "What are the termination conditions?",
                "Can you explain the payment terms?",
                "What are the dispute resolution mechanisms?"
            ]
            
            # Filter suggestions that contain the query
            query_lower = q.lower()
            suggestions = [s for s in base_suggestions if query_lower in s.lower()][:5]
        
        return JSONResponse({"suggestions": suggestions})
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/get-documents")
def get_documents(user_session: Optional[str] = Cookie(None)):
    """Get available documents for the user"""
    try:
        # Check user authentication
        user_data = verify_user_session(user_session)
        if not user_data:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        # Get user's documents from vector store
        from services.vector_store import VectorStore
        user_id = user_data.get('user_id')
        
        vector_store = VectorStore(user_id=user_id)
        documents, total = vector_store.get_available_documents(limit=50)  # Get more for simple chat
        
        return JSONResponse({"documents": documents})
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)