from fastapi import APIRouter, Request, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from template_config import templates
from typing import Optional
from db_operations import DatabaseOperations

router = APIRouter()

@router.get("/admin/chat-history", response_class=HTMLResponse)
def admin_chat_history(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Admin chat history page"""
    from routes.admin_auth import verify_admin_session
    admin_data = verify_admin_session(admin_session)
    if not admin_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    return templates.TemplateResponse("admin_chat_history.html", {
        "request": request,
        "admin": admin_data,
        "current_page": "chat_history"
    })

@router.get("/admin/api/chat-history")
def admin_get_chat_history(
    request: Request,
    admin_session: Optional[str] = Cookie(None),
    page: int = 1,
    per_page: int = 20,
    user_id: Optional[int] = None,
    search: Optional[str] = None
):
    """API endpoint to get chat history for admin"""
    from routes.admin_auth import verify_admin_session
    admin_data = verify_admin_session(admin_session)
    if not admin_data:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    
    try:
        chat_history = DatabaseOperations.get_admin_chat_history(
            page=page,
            per_page=per_page,
            user_id=user_id,
            search=search
        )
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
        success = DatabaseOperations.delete_chat_history(chat_id)
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
        stats = DatabaseOperations.get_chat_usage_stats()
        return JSONResponse(stats)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)