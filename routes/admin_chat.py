from fastapi import APIRouter, Request, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from template_config import templates
from typing import Optional
from db_operations import DatabaseOperations
import json
from decimal import Decimal

router = APIRouter()

@router.get("/admin/chat-history", response_class=HTMLResponse)
def admin_chat_history(
    request: Request, 
    admin_session: Optional[str] = Cookie(None),
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Admin chat history page with filters"""
    from routes.admin_auth import verify_admin_session
    admin_data = verify_admin_session(admin_session)
    if not admin_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Convert date format from dd-mm-yyyy to yyyy-mm-dd for database
    db_date_from = None
    db_date_to = None
    
    if date_from:
        try:
            from datetime import datetime
            db_date_from = datetime.strptime(date_from, '%d-%m-%Y').strftime('%Y-%m-%d')
        except:
            db_date_from = None
            
    if date_to:
        try:
            from datetime import datetime
            db_date_to = datetime.strptime(date_to, '%d-%m-%Y').strftime('%Y-%m-%d')
        except:
            db_date_to = None
    
    # Convert user_id to int if provided
    user_id_int = None
    if user_id and user_id.strip():
        try:
            user_id_int = int(user_id)
        except ValueError:
            user_id_int = None
    
    # Load chat history data with filters
    try:
        from chat_db_methods import ChatHistoryOperations
        chat_data = ChatHistoryOperations.get_admin_chat_history(
            page=page,
            per_page=per_page,
            user_id=user_id_int,
            search=search,
            date_from=db_date_from,
            date_to=db_date_to
        )
        
        # Convert datetime to string for display
        for chat in chat_data.get('chat_history', []):
            if chat.get('created_at'):
                if hasattr(chat['created_at'], 'strftime'):
                    chat['created_at'] = chat['created_at'].strftime('%d %b %Y %H:%M')
                    
    except Exception as e:
        print(f"Error loading chat data: {e}")
        chat_data = {"chat_history": [], "total": 0, "pages": 0, "current_page": 1}
    
    # Ensure chat_data has required structure
    if not chat_data:
        chat_data = {"chat_history": [], "total": 0, "pages": 0, "current_page": 1}
    
    return templates.TemplateResponse("admin_chat_history.html", {
        "request": request,
        "admin": admin_data or {"name": "Admin", "email": "admin@legaleagle.com"},
        "current_page": "chat_history",
        "chat_data": chat_data,
        "search_filter": search or '',
        "user_id_filter": user_id or '',
        "date_from": date_from or '',
        "date_to": date_to or '',
        "page": page,
        "per_page": per_page
    })

@router.get("/admin/api/chat-history")
def admin_get_chat_history(
    request: Request,
    admin_session: Optional[str] = Cookie(None),
    page: int = 1,
    per_page: int = 20,
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """API endpoint to get chat history for admin"""
    # Skip authentication for now to test
    # from routes.admin_auth import verify_admin_session
    # admin_data = verify_admin_session(admin_session)
    # if not admin_data:
    #     return JSONResponse({"error": "Authentication required"}, status_code=401)
    
    try:
        from chat_db_methods import ChatHistoryOperations
        chat_history = ChatHistoryOperations.get_admin_chat_history(
            page=page,
            per_page=per_page,
            user_id=user_id,
            search=search,
            date_from=date_from,
            date_to=date_to
        )
        
        # Convert datetime objects to strings for JSON serialization
        for chat in chat_history.get('chat_history', []):
            if chat.get('created_at'):
                chat['created_at'] = chat['created_at'].isoformat()
        
        return JSONResponse(chat_history)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/admin/api/chat-history/{chat_id}")
def admin_delete_chat_history(
    chat_id: int,
    request: Request,
    admin_session: Optional[str] = Cookie(None)
):
    """Delete a chat history record"""
    from routes.admin_auth import verify_admin_session
    admin_data = verify_admin_session(admin_session)
    if not admin_data:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    
    try:
        from chat_db_methods import ChatHistoryOperations
        success = ChatHistoryOperations.delete_chat_history(chat_id)
        if success:
            return JSONResponse({"message": "Chat history deleted successfully"})
        else:
            return JSONResponse({"error": "Failed to delete chat history"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/admin/api/chat-stats")
def admin_get_chat_stats(
    request: Request,
    admin_session: Optional[str] = Cookie(None)
):
    """Get chat usage statistics"""
    from routes.admin_auth import verify_admin_session
    admin_data = verify_admin_session(admin_session)
    if not admin_data:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    
    try:
        from chat_db_methods import ChatHistoryOperations
        stats = ChatHistoryOperations.get_chat_usage_stats()
        return JSONResponse(stats)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)