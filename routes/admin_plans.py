from fastapi import APIRouter, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
from db_operations import DatabaseOperations
from template_config import templates

router = APIRouter()

def verify_admin_session(admin_session: Optional[str] = Cookie(None)):
    """Verify admin session cookie"""
    if not admin_session:
        return None
    
    try:
        parts = admin_session.split(',')
        user_data = {}
        for part in parts:
            key, value = part.split(':')
            user_data[key] = value
        
        if user_data.get('role') != 'admin':
            return None
        
        return user_data
    except:
        return None

@router.get("/plans", response_class=HTMLResponse)
def admin_plans(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Admin plans management page"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    plans = DatabaseOperations.get_all_plans()
    return templates.TemplateResponse("admin_plans.html", {"request": request, "plans": plans, "current_page": "plans"})

@router.post("/plans")
def create_plan(
    name: str = Form(...), 
    subtitle: str = Form(""),
    price: float = Form(...), 
    features: str = Form(...),
    max_documents: int = Form(10),
    max_chat_prompts: int = Form(100),
    most_popular: bool = Form(False),
    admin_session: Optional[str] = Cookie(None)
):
    """Create new plan"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    success = DatabaseOperations.create_plan(name, subtitle, price, features, max_documents, max_chat_prompts, most_popular)
    return JSONResponse({"success": success, "message": "Plan created successfully" if success else "Error creating plan"})

@router.post("/plans/{plan_id}/edit")
def edit_plan(
    plan_id: int, 
    name: str = Form(...),
    subtitle: str = Form(""), 
    price: float = Form(...), 
    features: str = Form(...),
    max_documents: int = Form(10),
    max_chat_prompts: int = Form(100),
    most_popular: bool = Form(False),
    admin_session: Optional[str] = Cookie(None)
):
    """Edit plan"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    success = DatabaseOperations.update_plan(plan_id, name, subtitle, price, features, max_documents, max_chat_prompts, most_popular)
    return JSONResponse({"success": success, "message": "Plan updated successfully" if success else "Error updating plan"})

@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, admin_session: Optional[str] = Cookie(None)):
    """Delete plan"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    success = DatabaseOperations.delete_plan(plan_id)
    return JSONResponse({"success": success, "message": "Plan deleted successfully" if success else "Error deleting plan"})