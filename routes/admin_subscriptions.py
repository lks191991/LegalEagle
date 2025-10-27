from fastapi import APIRouter, Request, Form, Cookie, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from db_operations import DatabaseOperations

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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

@router.get("/subscriptions", response_class=HTMLResponse)
def admin_subscriptions(request: Request, 
                       admin_session: Optional[str] = Cookie(None),
                       user_name: Optional[str] = Query(None),
                       user_email: Optional[str] = Query(None),
                       plan_name: Optional[str] = Query(None),
                       status: Optional[str] = Query(None), 
                       date_from: Optional[str] = Query(None),
                       date_to: Optional[str] = Query(None),
                       search: Optional[str] = Query(None)):
    """Admin subscriptions management page"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Get filtered subscriptions using the database function
    subscriptions = DatabaseOperations.get_all_subscriptions_filtered(
        user_name_filter=user_name,
        user_email_filter=user_email, 
        plan_name_filter=plan_name,
        status_filter=status,
        date_from=date_from,
        date_to=date_to
    )
    
    # Get all subscriptions for status counts (unfiltered)
    all_subscriptions = DatabaseOperations.get_all_subscriptions()
    
    # Get all available subscription plans for the filter dropdown
    all_plans = DatabaseOperations.get_all_plans()
    
    # Get counts for each status
    status_counts = {
        'all': len(all_subscriptions),
        'active': len([sub for sub in all_subscriptions if sub['status'] == 'active']),
        'cancelled': len([sub for sub in all_subscriptions if sub['status'] == 'cancelled']),
        'expired': len([sub for sub in all_subscriptions if sub['status'] == 'expired'])
    }
    
    return templates.TemplateResponse("admin_subscriptions.html", {
        "request": request, 
        "subscriptions": subscriptions, 
        "current_page": "subscriptions",
        "current_filter": status or 'all',
        "user_name_filter": user_name,
        "user_email_filter": user_email,
        "plan_filter": plan_name,
        "status_filter": status,
        "date_from": date_from,
        "date_to": date_to,
        "search_query": search or "",
        "status_counts": status_counts,
        "all_plans": all_plans
    })

@router.post("/subscriptions/{subscription_id}/status")
def change_subscription_status(subscription_id: int, status: str = Form(...), admin_session: Optional[str] = Cookie(None)):
    """Change subscription status"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    success = DatabaseOperations.update_subscription_status(subscription_id, status)
    return JSONResponse({"success": success, "message": "Subscription status updated successfully" if success else "Error updating status"})