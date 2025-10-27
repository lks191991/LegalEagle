from fastapi import APIRouter, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
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

@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Admin dashboard page with statistics"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    stats = DatabaseOperations.get_dashboard_stats()
    recent_transactions = DatabaseOperations.get_recent_transactions(5)
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_transactions": recent_transactions,
        "user_name": "Admin User",
        "current_page": "dashboard"
    })

@router.get("/contacts", response_class=HTMLResponse)
def admin_contact_submissions(
    request: Request, 
    admin_session: Optional[str] = Cookie(None),
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Admin contact submissions page with filtering"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Get filtered contact submissions
    if status or search or date_from or date_to:
        contact_submissions = DatabaseOperations.get_filtered_contact_submissions(
            status=status, search=search, date_from=date_from, date_to=date_to
        )
    else:
        contact_submissions = DatabaseOperations.get_all_contact_submissions()
    
    # Debug: Print submission count
    print(f"DEBUG: Found {len(contact_submissions)} contact submissions for admin page")
    for i, sub in enumerate(contact_submissions):
        print(f"DEBUG: Submission {i+1}: ID={sub.get('id')}, Name={sub.get('first_name')} {sub.get('last_name')}")
    
    return templates.TemplateResponse("admin_contacts.html", {
        "request": request,
        "contact_submissions": contact_submissions,
        "user_name": "Admin User",
        "current_page": "contacts",
        "filters": {
            "status": status or "all",
            "search": search or "",
            "date_from": date_from or "",
            "date_to": date_to or ""
        }
    })

@router.get("/contacts-debug", response_class=HTMLResponse)
def admin_contact_debug(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Debug contact submissions page"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    contact_submissions = DatabaseOperations.get_all_contact_submissions()
    print(f"DEBUG ROUTE: Found {len(contact_submissions)} submissions")
    
    return templates.TemplateResponse("debug_contacts.html", {
        "request": request,
        "contact_submissions": contact_submissions,
        "user_name": "Admin User",
        "current_page": "contacts",
        "filters": {
            "status": "all",
            "search": "",
            "date_from": "",
            "date_to": ""
        }
    })

@router.post("/contacts/{contact_id}/status")
async def update_contact_status_route(contact_id: int, request: Request, admin_session: Optional[str] = Cookie(None)):
    """Update contact submission status"""
    from fastapi.responses import JSONResponse
    
    if not admin_session:
        return JSONResponse({"success": False, "error": "Authentication required"}, status_code=401)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "error": "Authentication required"}, status_code=401)
    
    try:
        # Get status from request body
        body = await request.json()
        new_status = body.get('status', 'new')
        
        if new_status not in ['new', 'replied', 'closed']:
            return JSONResponse({"success": False, "error": "Invalid status"}, status_code=400)
        
        # Update the contact status
        success = DatabaseOperations.update_contact_status(contact_id, new_status)
        
        if success:
            return JSONResponse({"success": True, "message": f"Contact status updated to {new_status}"})
        else:
            return JSONResponse({"success": False, "error": "Failed to update contact status"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)