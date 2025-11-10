from fastapi import APIRouter, Request, Form, Cookie, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import hashlib
import uuid
from pathlib import Path
from db_operations import DatabaseOperations

router = APIRouter()
templates = Jinja2Templates(directory="templates")



router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/change-password")
def change_admin_password(current_password: str = Form(...), new_password: str = Form(...), admin_session: Optional[str] = Cookie(None)):
    """Change admin password only"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})

    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})

    user_id = int(user_data.get('user_id'))
    user = DatabaseOperations.get_user_by_id(user_id)
    if not user:
        return JSONResponse({"success": False, "message": "User not found"})

    # Verify current password
    if not verify_password(current_password, user["password"]):
        return JSONResponse({"success": False, "message": "Current password is incorrect"})

    # Update password only
    success = DatabaseOperations.update_user_profile(user_id, user["name"], user["email"], user.get("mobile_number"), new_password, None)
    return JSONResponse({"success": success, "message": "Password changed successfully" if success else "Error updating password"})

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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

@router.get("/profile", response_class=HTMLResponse)
def admin_profile(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Admin profile page"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_id = user_data.get('user_id')
    user = DatabaseOperations.get_user_by_id(int(user_id))
    return templates.TemplateResponse("admin_profile.html", {"request": request, "user": user, "current_page": "profile"})


@router.post("/profile")
def update_admin_profile(
    name: str = Form(...),
    email: str = Form(...),
    mobile_number: str = Form(...),
    profile_photo: Optional[UploadFile] = File(None),
    admin_session: Optional[str] = Cookie(None)
):
    """Update admin profile (name, email, mobile, image)"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})

    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})

    user_id = int(user_data.get('user_id'))

    # Handle profile photo upload
    photo_filename = None
    if profile_photo and profile_photo.filename:
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if profile_photo.content_type not in allowed_types:
            return JSONResponse({"success": False, "message": "Invalid file type. Only JPG, PNG, GIF allowed."})
        file_extension = profile_photo.filename.split('.')[-1]
        photo_filename = f"{uuid.uuid4()}.{file_extension}"
        upload_dir = Path("static/uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / photo_filename
        with open(file_path, "wb") as buffer:
            content = profile_photo.file.read()
            if len(content) > 2 * 1024 * 1024:
                return JSONResponse({"success": False, "message": "File too large. Maximum 2MB allowed."})
            buffer.write(content)
        user = DatabaseOperations.get_user_by_id(user_id)
        if user and user.get('profile_photo'):
            old_file_path = Path("static/uploads") / user['profile_photo']
            if old_file_path.exists():
                old_file_path.unlink()

    # Update profile (no password change here)
    success = DatabaseOperations.update_user_profile(user_id, name, email, mobile_number, None, photo_filename)
    return JSONResponse({"success": success, "message": "Profile updated successfully" if success else "Error updating profile"})

@router.get("/settings", response_class=HTMLResponse)
def admin_settings(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Admin settings page"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    settings = DatabaseOperations.get_all_settings()
    return templates.TemplateResponse("admin_settings.html", {"request": request, "settings": settings, "current_page": "settings"})

@router.post("/settings")
async def update_settings(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Update general settings"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    # Get form data
    form_data = await request.form()
    
    # Update each setting
    for key, value in form_data.items():
        DatabaseOperations.update_setting(key, value)
    
    return JSONResponse({"success": True, "message": "Settings updated successfully"})