from fastapi import APIRouter, Request, Cookie
from . import admin_auth, admin_dashboard, admin_users, admin_plans, admin_subscriptions, admin_transactions, admin_settings, admin_faqs, admin_chat
from fastapi.responses import RedirectResponse
from typing import Optional

# Create main admin router
router = APIRouter(prefix="/admin")

# Include all admin sub-routers
router.include_router(admin_auth.router, tags=["admin-auth"])
router.include_router(admin_dashboard.router, tags=["admin-dashboard"])
router.include_router(admin_users.router, tags=["admin-users"])
router.include_router(admin_plans.router, tags=["admin-plans"])
router.include_router(admin_subscriptions.router, tags=["admin-subscriptions"])
router.include_router(admin_transactions.router, tags=["admin-transactions"])
router.include_router(admin_settings.router, tags=["admin-settings"])
router.include_router(admin_faqs.router, tags=["admin-faqs"])
router.include_router(admin_chat.router, tags=["admin-chat"])

@router.get("/", include_in_schema=False)
def admin_root(request: Request, admin_session: Optional[str] = Cookie(None)):
    """Redirect /admin to login if not logged in, else to dashboard"""
    # Try to parse session cookie
    if not admin_session:
        return RedirectResponse(url="/admin/login", status_code=302)
    try:
        parts = admin_session.split(',')
        user_data = {}
        for part in parts:
            key, value = part.split(':')
            user_data[key] = value
        if user_data.get('role') == 'admin':
            return RedirectResponse(url="/admin/dashboard", status_code=302)
        else:
            return RedirectResponse(url="/admin/login", status_code=302)
    except Exception:
        return RedirectResponse(url="/admin/login", status_code=302)