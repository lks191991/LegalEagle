from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from template_config import templates

router = APIRouter()

def get_template_context(request: Request, current_page: str, **kwargs):
    """Helper function to get common template context including settings"""
    from db_operations import DatabaseOperations
    
    try:
        settings = DatabaseOperations.get_settings_dict()
    except Exception as e:
        print(f"Settings error: {e}")
        settings = {}
    
    context = {
        "request": request,
        "current_page": current_page,
        "settings": settings
    }
    context.update(kwargs)
    return context

@router.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    """About page"""
    return templates.TemplateResponse("about.html", get_template_context(request, "about"))

@router.get("/contact", response_class=HTMLResponse)
def contact_page(request: Request):
    """Contact page"""
    from routes.auth import verify_user_session
    from typing import Optional
    
    # Check if user is logged in
    user_session = request.cookies.get('user_session')
    user_data = None
    if user_session:
        user_data = verify_user_session(user_session)
        if user_data:
            # Get full user details for pre-filling form
            from db_operations import DatabaseOperations
            full_user_data = DatabaseOperations.get_user_by_id(user_data['user_id'])
            if full_user_data:
                user_data = full_user_data
    
    return templates.TemplateResponse("contact.html", get_template_context(request, "contact", user=user_data))

@router.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    """FAQ page"""
    from db_operations import DatabaseOperations
    
    # Get active FAQs and categories
    try:
        faqs = DatabaseOperations.get_active_faqs()
        faq_categories = DatabaseOperations.get_faq_categories()
    except Exception as e:
        print(f"FAQ data error: {e}")
        faqs = []
        faq_categories = []
    
    return templates.TemplateResponse("faq.html", get_template_context(request, "faq", 
        faqs=faqs, faq_categories=faq_categories))

@router.get("/subscription", response_class=HTMLResponse)
def subscription_page(request: Request):
    """Subscription/Pricing page"""
    from db_operations import DatabaseOperations
    from routes.auth import verify_user_session
    
    # Get subscription plans from database
    all_plans = DatabaseOperations.get_all_plans()
    
    # Check if user is logged in
    user_session = request.cookies.get("user_session")
    user_data = verify_user_session(user_session)
    
    # Always show all plans except Free Plan
    plans = [plan for plan in all_plans if plan['name'].lower() != 'free']
    
    # Get user's current plan to determine which buttons to show
    current_user_price = 0
    if user_data:
        user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
        if user_plan:
            current_user_price = user_plan.get('plan_price', 0)
    
    # Add flag to each plan indicating if user can upgrade to it
    for plan in plans:
        plan['can_subscribe'] = plan['price'] > current_user_price
    
    return templates.TemplateResponse("subscription.html", get_template_context(request, "subscription", plans=plans, user=user_data, current_user_price=current_user_price))