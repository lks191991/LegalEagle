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
    
    # Convert dd-mm-yyyy to yyyy-mm-dd for backend filtering
    from datetime import datetime
    def convert_to_yyyy_mm_dd(date_str):
        if date_str and '-' in date_str:
            try:
                return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
            except Exception:
                return date_str
        return date_str

    date_from_filter = convert_to_yyyy_mm_dd(date_from) if date_from and date_from.strip() else None
    date_to_filter = convert_to_yyyy_mm_dd(date_to) if date_to and date_to.strip() else None

    transactions = DatabaseOperations.get_all_transactions_filtered(user_name, user_email, status, amount_range, date_from_filter, date_to_filter)
    total_amount = sum(t.get('amount', 0) or 0 for t in transactions)
    all_time_total = DatabaseOperations.get_total_revenue()

    # For display in filter badges, always show dd-mm-yyyy
    def convert_to_dd_mm_yyyy(date_str):
        if date_str and '-' in date_str:
            try:
                # Accept both yyyy-mm-dd and dd-mm-yyyy
                if date_str.count('-') == 2:
                    parts = date_str.split('-')
                    if len(parts[0]) == 4:
                        # yyyy-mm-dd
                        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%m-%Y')
                    elif len(parts[2]) == 4:
                        # dd-mm-yyyy
                        return date_str
            except Exception:
                return date_str
        return date_str or ''

    date_from_display = convert_to_dd_mm_yyyy(date_from) if date_from else ''
    date_to_display = convert_to_dd_mm_yyyy(date_to) if date_to else ''

    return templates.TemplateResponse("admin_transactions.html", {
        "request": request, 
        "transactions": transactions, 
        "total_amount": total_amount,
        "all_time_total": all_time_total,
        "current_page": "transactions",
        "user_name_filter": user_name,
        "user_email_filter": user_email,
        "status_filter": status,
        "amount_filter": amount_range,
        "date_from": date_from_display,
        "date_to": date_to_display
    })