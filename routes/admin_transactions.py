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

@router.get("/transactions", response_class=HTMLResponse)
def admin_transactions(request: Request, 
                      user_name: Optional[str] = None,
                      user_email: Optional[str] = None,
                      status: Optional[str] = None,
                      amount_range: Optional[str] = None,
                      date_from: Optional[str] = None,
                      date_to: Optional[str] = None,
                      admin_session: Optional[str] = Cookie(None)):
    """Admin transactions page with filters"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    transactions = DatabaseOperations.get_all_transactions_filtered(user_name, user_email, status, amount_range, date_from, date_to)
    
    return templates.TemplateResponse("admin_transactions.html", {
        "request": request, 
        "transactions": transactions, 
        "current_page": "transactions",
        "user_name_filter": user_name,
        "user_email_filter": user_email,
        "status_filter": status,
        "amount_filter": amount_range,
        "date_from": date_from,
        "date_to": date_to
    })