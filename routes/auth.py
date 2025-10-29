from fastapi import APIRouter, Request, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
import hashlib
from db_operations import DatabaseOperations
from template_config import templates

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def user_login_page(request: Request):
    """User login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None,
        "email": "",
        "current_page": "login"
    })

@router.post("/login")
async def user_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Process user login"""
    
    # Get user from database
    user = DatabaseOperations.get_user_by_email(email)
    
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password",
            "email": email
        })
    
    # Check password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if user['password'] != hashed_password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password",
            "email": email
        })
    
    # Check if user is active
    if user['status'] != 'active':
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Account is inactive. Please contact support.",
            "email": email
        })
    
    # Create session cookie
    session_data = f"user_id:{user['id']},email:{user['email']},name:{user['name']},role:{user['role']}"
    
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="user_session",
        value=session_data,
        max_age=86400,  # 24 hours
        httponly=True,
        secure=False  # Set to True in production with HTTPS
    )
    
    return response

@router.get("/signup", response_class=HTMLResponse)
def user_signup_page(request: Request):
    """User signup page"""
    return templates.TemplateResponse("signup.html", {
        "request": request, 
        "current_page": "signup",
        "form_data": {"name": "", "email": ""}
    })

@router.post("/signup")
async def user_signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    mobile_number: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Process user signup"""
    
    # Clean mobile number (empty string if not provided)
    mobile_number = mobile_number.strip() if mobile_number else None
    
    # Validate password confirmation
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match",
            "form_data": {"name": name, "email": email, "mobile_number": mobile_number}
        })
    
    # Check if user already exists
    existing_user = DatabaseOperations.get_user_by_email(email)
    if existing_user:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Email already registered. Please use a different email.",
            "form_data": {"name": name, "email": email, "mobile_number": mobile_number}
        })
    
    # Create user with default role 'user'
    try:
        success = DatabaseOperations.create_user(name, email, password, mobile_number)
        if success:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "success": "Account created successfully! You can now login.",
                "form_data": {"name": "", "email": "", "mobile_number": ""}
            })
        else:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "error": "Failed to create account. Please try again.",
                "form_data": {"name": name, "email": email, "mobile_number": mobile_number}
            })
    except Exception as e:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "An error occurred. Please try again.",
            "form_data": {"name": name, "email": email, "mobile_number": mobile_number}
        })

@router.get("/logout")
def user_logout():
    """User logout"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("user_session")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request, user_session: Optional[str] = Cookie(None)):
    """User dashboard - protected route"""
    if not user_session:
        return RedirectResponse(url="/login", status_code=302)
    
    # Parse session data
    try:
        parts = user_session.split(',')
        user_data = {}
        for part in parts:
            key, value = part.split(':')
            user_data[key] = value
        
        # Only allow regular users (not admin)
        if user_data.get('role') == 'admin':
            return RedirectResponse(url="/admin/dashboard", status_code=302)
        
        # Get user's dashboard data
        from db_operations import DatabaseOperations
        user_id = int(user_data['user_id'])
        
        try:
            # Get user's complete profile data
            complete_user = DatabaseOperations.get_user_by_id(user_id) or user_data
            
            # Get user's current plan using the existing method
            current_plan = DatabaseOperations.get_user_plan(user_id)
            
            # Get user's subscription history
            try:
                subscriptions = DatabaseOperations.get_user_active_subscription(user_id)
                if subscriptions:
                    subscriptions = [subscriptions]  # Convert single item to list for template
                else:
                    subscriptions = []
            except:
                subscriptions = []
            
            # Get user's transactions
            try:
                transactions = DatabaseOperations.get_user_transactions(user_id)
                print(f"DEBUG: Found {len(transactions)} transactions for user {user_id}")
            except Exception as e:
                print(f"Transaction fetch error: {e}")
                transactions = []
            
            # Get actual usage statistics from database
            documents_count = 0
            chat_count = 0
            recent_chats = []
            
            # Get actual document count from database
            try:
                documents_count = DatabaseOperations.get_user_documents_count(user_id)
                print(f"DEBUG: User {user_id} has {documents_count} documents")
            except Exception as e:
                print(f"ERROR getting documents count: {e}")
                documents_count = 0
            
            # Get actual chat count from database
            try:
                chat_count = DatabaseOperations.get_user_chat_count(user_id)
                print(f"DEBUG: User {user_id} has {chat_count} chat messages")
            except Exception as e:
                print(f"ERROR getting chat count: {e}")
                chat_count = 0
            
            # Build usage stats with real database numbers and plan limits
            max_documents = 25  # Default limit for display
            max_prompts = 250   # Default limit for display
            
            # Get plan limits from database if user has a plan
            if current_plan:
                max_documents = current_plan.get('max_documents', 25)
                max_prompts = current_plan.get('max_chat_prompts', 250)
                print(f"DEBUG: Plan limits - Documents: {max_documents}, Prompts: {max_prompts}")
            else:
                print(f"DEBUG: Using default limits - Documents: {max_documents}, Prompts: {max_prompts}")
            
            usage_stats = {
                'documents_used': documents_count,  # Actual count from DB
                'prompts_used': chat_count,  # Actual count from DB  
                'documents_limit': max_documents,
                'prompts_limit': max_prompts,
                'total_documents': documents_count,  # Same as documents_used
                'total_chats': chat_count  # Add total chats for dashboard display
            }
            
            print(f"DEBUG: Final usage stats for user {user_id}: {usage_stats}")
            
        except Exception as e:
            print(f"Dashboard data error: {e}")
            # Fallback to basic data if there are errors
            complete_user = user_data
            documents_count = 0
            current_plan = None
            subscriptions = []
            recent_chats = []
            usage_stats = {
                'documents_used': 0,
                'prompts_used': 0,
                'documents_limit': 0,
                'prompts_limit': 0,
                'total_documents': 0
            }
            transactions = []
        
        # Get FAQ data
        try:
            faqs = DatabaseOperations.get_active_faqs(limit=10)
            faq_categories = DatabaseOperations.get_faq_categories()
        except Exception as e:
            print(f"FAQ data error: {e}")
            faqs = []
            faq_categories = []
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": complete_user,
            "documents_count": documents_count,
            "current_plan": current_plan,
            "subscriptions": subscriptions,
            "recent_chats": recent_chats,
            "usage_stats": usage_stats,
            "transactions": transactions,
            "faqs": faqs,
            "faq_categories": faq_categories,
            "current_page": "dashboard"
        })
    except Exception as e:
        print(f"Dashboard error: {e}")
        response = RedirectResponse(url="/login", status_code=302)
        response.delete_cookie("user_session")
        return response

def verify_user_session(user_session: Optional[str] = Cookie(None)):
    """Verify user session and return user data"""
    if not user_session:
        return None
    
    try:
        parts = user_session.split(',')
        user_data = {}
        for part in parts:
            key, value = part.split(':')
            user_data[key] = value
        
        # Don't allow admin sessions
        if user_data.get('role') == 'admin':
            return None
            
        return user_data
    except:
        return None