from fastapi import APIRouter, Request, Form, Cookie, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from db_operations import DatabaseOperations
import os
import uuid
from pathlib import Path

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

@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request, page: int = 1, name: str = None, email: str = None, status: str = None, role: str = None, 
               date_from: str = None, date_to: str = None, sort_by: str = None, admin_session: Optional[str] = Cookie(None)):
    """Admin users management page with search filters"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Convert empty strings to None for proper filtering
    name_filter = name if name and name.strip() else None
    email_filter = email if email and email.strip() else None
    status_filter = status if status and status.strip() else None
    date_from_filter = date_from if date_from and date_from.strip() else None
    date_to_filter = date_to if date_to and date_to.strip() else None
    sort_filter = sort_by if sort_by and sort_by.strip() else 'id_desc'
    
    # Handle role filter - default to 'all' to show all users
    if role and role.strip() == 'all':
        role_filter = None
    else:
        role_filter = role if role and role.strip() else None
    
    users_data = DatabaseOperations.get_all_users(page, 10, name_filter, email_filter, status_filter, role_filter, 
                                                date_from_filter, date_to_filter, sort_filter)
    return templates.TemplateResponse("admin_users.html", {
        "request": request, 
        "current_page": "users", 
        "name_filter": name or "",
        "email_filter": email or "",
        "status_filter": status or "",
        "role_filter": role or "all",
        "date_from": date_from or "",
        "date_to": date_to or "",
        "sort_filter": sort_filter,
        **users_data
    })

@router.post("/users")
def create_user(name: str = Form(...), email: str = Form(...), password: str = Form(...), 
               mobile_number: Optional[str] = Form(None), profile_photo: Optional[UploadFile] = File(None), 
               admin_session: Optional[str] = Cookie(None)):
    """Create new user"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    # Handle profile photo upload
    photo_filename = None
    if profile_photo and profile_photo.filename:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if profile_photo.content_type not in allowed_types:
            return JSONResponse({"success": False, "message": "Invalid file type. Only JPG, PNG, GIF allowed."})
        
        # Generate unique filename
        file_extension = profile_photo.filename.split('.')[-1]
        photo_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Save file
        upload_dir = Path("static/uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / photo_filename
        
        with open(file_path, "wb") as buffer:
            content = profile_photo.file.read()
            if len(content) > 2 * 1024 * 1024:  # 2MB limit
                return JSONResponse({"success": False, "message": "File too large. Maximum 2MB allowed."})
            buffer.write(content)
    
    success = DatabaseOperations.create_user(name, email, password, photo_filename, mobile_number)
    return JSONResponse({"success": success, "message": "User created successfully" if success else "Error creating user"})

@router.post("/users/{user_id}/edit")
def edit_user(user_id: int, name: str = Form(...), email: str = Form(...), status: str = Form(...),
             mobile_number: Optional[str] = Form(None), profile_photo: Optional[UploadFile] = File(None), 
             admin_session: Optional[str] = Cookie(None)):
    """Edit user"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    # Handle profile photo upload
    photo_filename = None
    if profile_photo and profile_photo.filename:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if profile_photo.content_type not in allowed_types:
            return JSONResponse({"success": False, "message": "Invalid file type. Only JPG, PNG, GIF allowed."})
        
        # Generate unique filename
        file_extension = profile_photo.filename.split('.')[-1]
        photo_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Save file
        upload_dir = Path("static/uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / photo_filename
        
        with open(file_path, "wb") as buffer:
            content = profile_photo.file.read()
            if len(content) > 2 * 1024 * 1024:  # 2MB limit
                return JSONResponse({"success": False, "message": "File too large. Maximum 2MB allowed."})
            buffer.write(content)
        
        # Delete old photo if exists
        old_user = DatabaseOperations.get_user_by_id(user_id)
        if old_user and old_user.get('profile_photo'):
            old_file_path = Path("static/uploads") / old_user['profile_photo']
            if old_file_path.exists():
                old_file_path.unlink()
    
    success = DatabaseOperations.update_user(user_id, name, email, status, photo_filename, mobile_number)
    return JSONResponse({"success": success, "message": "User updated successfully" if success else "Error updating user"})

@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin_session: Optional[str] = Cookie(None)):
    """Delete user"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    success = DatabaseOperations.delete_user(user_id)
    return JSONResponse({"success": success, "message": "User deleted successfully" if success else "Error deleting user"})

@router.get("/users/{user_id}/ai-settings")
def get_user_ai_settings(user_id: int, admin_session: Optional[str] = Cookie(None)):
    """Get AI settings for a user"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    settings = DatabaseOperations.get_user_ai_settings(user_id)
    return JSONResponse({"success": True, "settings": settings})

@router.post("/users/{user_id}/ai-settings")
def update_user_ai_settings(user_id: int, openai_key: str = Form(...), openai_model: str = Form(...), 
                           qdrant_url: str = Form(...), qdrant_key: str = Form(...), 
                           qdrant_collection: str = Form(...), admin_session: Optional[str] = Cookie(None)):
    """Update AI settings for a user"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    # Check if settings exist, create or update
    existing_settings = DatabaseOperations.get_user_ai_settings(user_id)
    if existing_settings:
        success = DatabaseOperations.update_user_ai_settings(user_id, openai_key, openai_model, qdrant_url, qdrant_key, qdrant_collection)
    else:
        success = DatabaseOperations.create_user_ai_settings(user_id, openai_key, openai_model, qdrant_url, qdrant_key, qdrant_collection)
    
    return JSONResponse({"success": success, "message": "AI settings updated successfully" if success else "Error updating AI settings"})

@router.get("/users/{user_id}/transactions", response_class=HTMLResponse)
def view_user_transactions(request: Request, user_id: int, status: str = None, amount_range: str = None, 
                          date_from: str = None, date_to: str = None, admin_session: Optional[str] = Cookie(None)):
    """View user's transactions with filters"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Get user details
    user = DatabaseOperations.get_user_by_id(user_id)
    if not user:
        return RedirectResponse(url="/admin/users", status_code=302)
    
    # Get user's transactions with filters
    transactions = DatabaseOperations.get_user_transactions_filtered(user_id, status, amount_range, date_from, date_to)
    
    return templates.TemplateResponse("admin_user_transactions.html", {
        "request": request,
        "current_page": "users",
        "user": user,
        "transactions": transactions,
        "admin_user": user_data,
        "status_filter": status or "",
        "amount_filter": amount_range or "",
        "date_from_filter": date_from or "",
        "date_to_filter": date_to or "",
        "name_filter": user["name"],  # Show current user's name
        "email_filter": user["email"]  # Show current user's email
    })

@router.get("/users/{user_id}/plans", response_class=HTMLResponse)
def view_user_plans(request: Request, user_id: int, admin_session: Optional[str] = Cookie(None)):
    """View user's plans and subscriptions"""
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # Get user details
    user = DatabaseOperations.get_user_by_id(user_id)
    if not user:
        return RedirectResponse(url="/admin/users", status_code=302)
    
    # Get user's current plan and subscription details
    user_plan = DatabaseOperations.get_user_current_plan(user_id)
    subscription_history = DatabaseOperations.get_user_subscriptions(user_id)
    
    return templates.TemplateResponse("admin_user_plans.html", {
        "request": request,
        "current_page": "users",
        "user": user,
        "user_plan": user_plan,
        "subscription_history": subscription_history,
        "admin_user": user_data
    })

@router.get("/users/{user_id}/details")
def get_user_details(user_id: int, admin_session: Optional[str] = Cookie(None)):
    """Get user details for popup modal"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    # Get user details
    user = DatabaseOperations.get_user_by_id(user_id)
    if not user:
        return JSONResponse({"success": False, "message": "User not found"})
    
    # Get current plan
    current_plan = DatabaseOperations.get_user_current_plan(user_id)
    
    # Get recent transactions (last 5)
    recent_transactions = DatabaseOperations.get_user_recent_transactions(user_id, 5)
    
    # Get available plans for assignment
    available_plans = DatabaseOperations.get_all_plans()
    
    # Convert Decimal objects and datetime to JSON serializable format
    def convert_decimals(obj):
        import datetime
        if isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimals(item) for item in obj]
        elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Decimal':
            return float(obj)
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.strftime('%Y-%m-%d %H:%M:%S') if isinstance(obj, datetime.datetime) else obj.strftime('%Y-%m-%d')
        else:
            return obj
    
    return JSONResponse({
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "status": user["status"],
            "profile_photo": user.get("profile_photo"),
            "created_at": user.get("created_at").strftime('%d %b %Y') if user.get("created_at") else 'N/A'
        },
        "current_plan": convert_decimals(current_plan),
        "recent_transactions": convert_decimals(recent_transactions),
        "available_plans": convert_decimals(available_plans)
    })

@router.post("/users/{user_id}/assign-plan")
async def assign_plan_to_user(request: Request, user_id: int, admin_session: Optional[str] = Cookie(None)):
    """Assign a plan to user and create transaction"""
    if not admin_session:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    user_data = verify_admin_session(admin_session)
    if not user_data:
        return JSONResponse({"success": False, "message": "Not authenticated"})
    
    # Parse JSON body
    import json
    try:
        body = await request.body()
        data = json.loads(body)
        plan_id = data.get("plan_id")
        payment_method = data.get("payment_method")
    except:
        return JSONResponse({"success": False, "message": "Invalid request data"})
    
    if not plan_id or not payment_method:
        return JSONResponse({"success": False, "message": "Plan ID and payment method are required"})
    
    # Get plan details
    plan = DatabaseOperations.get_plan_by_id(plan_id)
    if not plan:
        return JSONResponse({"success": False, "message": "Plan not found"})
    
    # Get admin ID from session (use user_id key)
    admin_id = user_data.get("user_id") or user_data.get("id")
    if not admin_id:
        return JSONResponse({"success": False, "message": f"Admin ID not found in session. Available keys: {list(user_data.keys())}"})
    
    # Assign plan to user
    success = DatabaseOperations.admin_assign_plan_to_user(
        user_id=user_id, 
        plan_id=plan_id, 
        admin_id=int(admin_id),
        payment_method=payment_method,
        amount=plan["price"]
    )
    
    if success:
        return JSONResponse({"success": True, "message": "Plan assigned successfully and transaction created"})
    else:
        return JSONResponse({"success": False, "message": "Failed to assign plan"})