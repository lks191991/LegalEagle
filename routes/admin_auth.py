from fastapi import APIRouter, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import hashlib
from db_operations import DatabaseOperations

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_user_by_email(email: str):
    return DatabaseOperations.get_user_by_email(email)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Admin login authentication"""
    
    # Get user from database
    user = get_user_by_email(email)
    
    if not user:
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "Invalid email or password"
        })
    
    # Verify password
    if not verify_password(password, user["password"]):
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "Invalid email or password"
        })
    
    # Check if user is admin
    if user["role"] != "admin":
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "Access denied. Admin privileges required."
        })
    
    # Create redirect response
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    
    # Set session cookie
    response.set_cookie(
        key="admin_session",
        value=f"user_id:{user['id']},role:{user['role']}",
        httponly=True,
        max_age=3600 * 24  # 24 hours
    )
    
    return response

@router.get("/logout")
def admin_logout():
    """Admin logout"""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response

def verify_admin_session(admin_session: Optional[str] = Cookie(None)):
    """Verify admin session and return admin data"""
    if not admin_session:
        return None
    
    try:
        # Get admin user by session (assuming session stores user email)
        # In a real app, you'd validate the session token
        admin_data = get_user_by_email(admin_session)
        
        if admin_data and admin_data.get('is_admin'):
            return admin_data
        else:
            return None
            
    except Exception as e:
        print(f"Admin session verification error: {e}")
        return None