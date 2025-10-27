from fastapi import APIRouter
from . import admin_auth, admin_dashboard, admin_users, admin_plans, admin_subscriptions, admin_transactions, admin_settings, admin_faqs, admin_chat

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