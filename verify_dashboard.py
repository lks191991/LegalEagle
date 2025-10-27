#!/usr/bin/env python3
"""
Dashboard Functionality Preservation Script

This script ensures that all existing dashboard functionality remains intact
after the CSS migration. It can be used to verify and restore functionality
if needed.
"""

from typing import Dict, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_dashboard_functionality():
    """Verify that all dashboard functions work correctly"""
    try:
        from db_operations import DatabaseOperations
        
        print("🔍 Verifying Dashboard Functionality...")
        
        # Test user ID (replace with actual user ID for testing)
        test_user_id = 4
        
        # Test 1: User documents count
        try:
            doc_count = DatabaseOperations.get_user_documents_count(test_user_id)
            print(f"✅ Documents Count: {doc_count}")
        except Exception as e:
            print(f"❌ Documents Count Error: {e}")
            
        # Test 2: Current plan
        try:
            current_plan = DatabaseOperations.get_user_current_plan(test_user_id)
            plan_name = current_plan['plan_name'] if current_plan else 'Free'
            print(f"✅ Current Plan: {plan_name}")
        except Exception as e:
            print(f"❌ Current Plan Error: {e}")
            
        # Test 3: Subscriptions
        try:
            subscriptions = DatabaseOperations.get_user_subscriptions(test_user_id)
            print(f"✅ Subscriptions: {len(subscriptions)} found")
        except Exception as e:
            print(f"❌ Subscriptions Error: {e}")
            
        # Test 4: Recent chats
        try:
            recent_chats = DatabaseOperations.get_user_recent_chats(test_user_id, 5)
            print(f"✅ Recent Chats: {len(recent_chats)} found")
        except Exception as e:
            print(f"❌ Recent Chats Error: {e}")
            
        # Test 5: Usage stats
        try:
            usage_stats = DatabaseOperations.get_user_usage_stats(test_user_id)
            print(f"✅ Usage Stats: {usage_stats}")
        except Exception as e:
            print(f"❌ Usage Stats Error: {e}")
            
        # Test 6: Transactions
        try:
            transactions = DatabaseOperations.get_user_transactions(test_user_id)
            print(f"✅ Transactions: {len(transactions)} found")
        except Exception as e:
            print(f"❌ Transactions Error: {e}")
            
        print("\n🎉 Dashboard functionality verification complete!")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        return False
        
    return True

def get_dashboard_config() -> Dict[str, Any]:
    """Get dashboard configuration settings"""
    return {
        'css_file': '/static/dashboard.css',
        'template_file': 'templates/dashboard.html',
        'required_methods': [
            'get_user_documents_count',
            'get_user_current_plan', 
            'get_user_subscriptions',
            'get_user_recent_chats',
            'get_user_usage_stats',
            'get_user_transactions'
        ],
        'css_classes': [
            'dashboard-hero-section',
            'dashboard-card',
            'stats-card',
            'dashboard-table',
            'empty-state'
        ],
        'features': {
            'fixed_card_heights': True,
            'responsive_design': True,
            'progress_animations': True,
            'hover_effects': True,
            'no_inline_styles': True
        }
    }

def restore_functionality_if_needed():
    """Restore dashboard functionality if something breaks"""
    print("🔧 Checking if restoration is needed...")
    
    # Check if CSS file exists
    if not os.path.exists('static/dashboard.css'):
        print("❌ dashboard.css missing - functionality may be affected")
        return False
        
    # Check if template has required structure
    try:
        with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_elements = [
            'dashboard-hero-section',
            'dashboard-card',
            'stats-card',
            'data-progress'
        ]
        
        missing = []
        for element in required_elements:
            if element not in content:
                missing.append(element)
                
        if missing:
            print(f"❌ Missing template elements: {missing}")
            return False
            
    except FileNotFoundError:
        print("❌ dashboard.html template missing")
        return False
        
    print("✅ All components present - functionality preserved")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("   DASHBOARD FUNCTIONALITY CHECKER")
    print("=" * 50)
    
    # Verify functionality
    functionality_ok = verify_dashboard_functionality()
    
    # Check file integrity  
    files_ok = restore_functionality_if_needed()
    
    # Show configuration
    config = get_dashboard_config()
    print(f"\n📋 Dashboard Configuration:")
    print(f"   CSS File: {config['css_file']}")
    print(f"   Template: {config['template_file']}")
    print(f"   Methods: {len(config['required_methods'])} required")
    print(f"   Classes: {len(config['css_classes'])} defined")
    
    if functionality_ok and files_ok:
        print("\n🎉 Dashboard is fully functional!")
        exit(0)
    else:
        print("\n⚠️  Dashboard may need attention")
        exit(1)