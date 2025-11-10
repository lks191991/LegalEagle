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
        # Parse the session cookie: 'user_id:1,role:admin'
        parts = admin_session.split(',')
        session_data = {}
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                session_data[key.strip()] = value.strip()
        user_id = session_data.get('user_id')
        role = session_data.get('role')
        if not user_id or role != 'admin':
            return None
        # Look up user by ID
        user = DatabaseOperations.get_user_by_id(int(user_id))
        if user and user.get('role') == 'admin':
            return user
        return None
    except Exception as e:
        print(f"Admin session verification error: {e}")
        return None