from database import get_db_connection
from typing import List, Dict, Optional
import hashlib

class DatabaseOperations:
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user
    
    @staticmethod
    def create_user(name: str, email: str, password: str, mobile_number: str = None) -> bool:
        """Create a new user"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (name, email, mobile_number, password) 
            VALUES (%s, %s, %s, %s)
        """, (name, email, mobile_number, hashed_password))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def update_user_profile(user_id: int, name: str, email: str, mobile_number: str = None, password: str = None, profile_photo: str = None) -> bool:
        """Update user profile"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        
        # Build dynamic query based on what fields are being updated
        update_fields = ["name = %s", "email = %s"]
        params = [name, email]
        
        if mobile_number is not None:
            update_fields.append("mobile_number = %s")
            params.append(mobile_number)
        
        if password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            update_fields.append("password = %s")
            params.append(hashed_password)
        
        if profile_photo is not None:
            update_fields.append("profile_photo = %s")
            params.append(profile_photo)
        
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def update_user_address(user_id: int, address_line1: str = None, address_line2: str = None, 
                          city: str = None, state: str = None, postal_code: str = None, country: str = None) -> bool:
        """Update user address information"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET address_line1 = %s, address_line2 = %s, city = %s, state = %s, postal_code = %s, country = %s WHERE id = %s",
            (address_line1, address_line2, city, state, postal_code, country, user_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def get_all_users(page: int = 1, per_page: int = 10, name_filter: str = None, email_filter: str = None, 
                     status_filter: str = None, role_filter: str = None, date_from: str = None, 
                     date_to: str = None, sort_by: str = None) -> Dict:
        """Get all users with pagination and search filters"""
        connection = get_db_connection()
        if not connection:
            return {"users": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 0}
        
        cursor = connection.cursor(dictionary=True)
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if name_filter:
            where_conditions.append("name LIKE %s")
            params.append(f"%{name_filter}%")
        
        if email_filter:
            where_conditions.append("email LIKE %s")
            params.append(f"%{email_filter}%")
        
        if status_filter:
            where_conditions.append("status = %s")
            params.append(status_filter)
        
        # Apply role filter if specified
        if role_filter:
            where_conditions.append("role = %s")
            params.append(role_filter)
            
        # Date range filter
        if date_from:
            where_conditions.append("DATE(created_at) >= %s")
            params.append(date_from)
            
        if date_to:
            where_conditions.append("DATE(created_at) <= %s")
            params.append(date_to)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build ORDER BY clause
        order_by = "ORDER BY id DESC"  # Default sorting
        if sort_by:
            if sort_by == "id_desc":
                order_by = "ORDER BY id DESC"
            elif sort_by == "id_asc":
                order_by = "ORDER BY id ASC"
            elif sort_by == "name_asc":
                order_by = "ORDER BY name ASC"
            elif sort_by == "name_desc":
                order_by = "ORDER BY name DESC"
            elif sort_by == "email_asc":
                order_by = "ORDER BY email ASC"
            elif sort_by == "email_desc":
                order_by = "ORDER BY email DESC"
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) as total FROM users WHERE {where_clause}", params)
        total = cursor.fetchone()["total"]
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        offset = (page - 1) * per_page
        
        # Get paginated users
        cursor.execute(
            f"SELECT id, name, email, mobile_number, profile_photo, role, status, created_at FROM users WHERE {where_clause} {order_by} LIMIT %s OFFSET %s",
            params + [per_page, offset]
        )
        users = cursor.fetchall()
        
        # Convert datetime objects to readable format strings
        for user in users:
            if user['created_at']:
                user['created_at'] = user['created_at'].strftime('%d %b %Y')
        
        cursor.close()
        connection.close()
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    
    @staticmethod
    def create_user(name: str, email: str, password: str, profile_photo: str = None, mobile_number: str = None) -> bool:
        """Create new user and assign Free Plan (one-time only)"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # Create user
            cursor.execute(
                "INSERT INTO users (name, email, password, profile_photo, mobile_number, role) VALUES (%s, %s, %s, %s, %s, 'user')",
                (name, email, hashed_password, profile_photo, mobile_number)
            )
            
            # Get the new user ID
            user_id = cursor.lastrowid
            
            # Get Free Plan ID
            cursor.execute("SELECT id FROM subscription_plans WHERE name = 'Free Plan' AND price = 0")
            free_plan = cursor.fetchone()
            
            if free_plan and user_id:
                free_plan_id = free_plan[0]
                
                # Assign Free Plan to new user (one-time assignment)
                cursor.execute(
                    """INSERT INTO user_plans (user_id, plan_id, plan_name, plan_price, 
                       max_documents, max_chat_prompts, created_at) 
                       SELECT %s, id, name, price, max_documents, max_chat_prompts, NOW() 
                       FROM subscription_plans WHERE id = %s""",
                    (user_id, free_plan_id)
                )
                print(f"✅ Assigned Free Plan to new user {user_id}")
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            connection.rollback()
            cursor.close()
            connection.close()
            return False
    
    @staticmethod
    def update_user(user_id: int, name: str, email: str, status: str, profile_photo: str = None, mobile_number: str = None) -> bool:
        """Update user"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        
        # Build dynamic query based on provided parameters
        update_fields = []
        update_values = []
        
        update_fields.extend(["name = %s", "email = %s", "status = %s"])
        update_values.extend([name, email, status])
        
        if profile_photo is not None:
            update_fields.append("profile_photo = %s")
            update_values.append(profile_photo)
        
        if mobile_number is not None:
            update_fields.append("mobile_number = %s")
            update_values.append(mobile_number)
        
        update_values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, update_values)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Delete user"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def get_all_plans() -> List[Dict]:
        """Get all subscription plans"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM subscription_plans where status = 'active' ORDER BY price ASC")
        plans = cursor.fetchall()
        cursor.close()
        connection.close()
        return plans
    
    @staticmethod
    def create_plan(name: str, subtitle: str, price: float, features: str, max_documents: int = 10, max_chat_prompts: int = 100, most_popular: bool = False) -> bool:
        """Create new plan"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        
        # If this plan is marked as most popular, unset all other plans
        if most_popular:
            cursor.execute("UPDATE subscription_plans SET most_popular = FALSE")
        
        cursor.execute(
            "INSERT INTO subscription_plans (name, subtitle, price, features, max_documents, max_chat_prompts, most_popular) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name, subtitle, price, features, max_documents, max_chat_prompts, most_popular)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def update_plan(plan_id: int, name: str, subtitle: str, price: float, features: str, max_documents: int = None, max_chat_prompts: int = None, most_popular: bool = False) -> bool:
        """Update plan"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        
        # If this plan is marked as most popular, unset all other plans
        if most_popular:
            cursor.execute("UPDATE subscription_plans SET most_popular = FALSE")
        
        if max_documents is not None and max_chat_prompts is not None:
            cursor.execute(
                "UPDATE subscription_plans SET name = %s, subtitle = %s, price = %s, features = %s, max_documents = %s, max_chat_prompts = %s, most_popular = %s WHERE id = %s",
                (name, subtitle, price, features, max_documents, max_chat_prompts, most_popular, plan_id)
            )
        else:
            cursor.execute(
                "UPDATE subscription_plans SET name = %s, subtitle = %s, price = %s, features = %s, most_popular = %s WHERE id = %s",
                (name, subtitle, price, features, most_popular, plan_id)
            )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def delete_plan(plan_id: int) -> bool:
        """Delete plan"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("DELETE FROM subscription_plans WHERE id = %s", (plan_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def get_all_subscriptions(status_filter: str = None) -> List[Dict]:
        """Get all subscriptions with user and plan details"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT us.id, u.name as user_name, u.email as user_email, sp.name as plan_name, 
                   us.status, us.start_date, us.end_date
            FROM user_subscriptions us
            JOIN users u ON us.user_id = u.id
            JOIN subscription_plans sp ON us.plan_id = sp.id
        """
        
        params = ()
        if status_filter and status_filter != 'all':
            query += " WHERE us.status = %s"
            params = (status_filter,)
            
        query += " ORDER BY us.id DESC"
        
        cursor.execute(query, params)
        subscriptions = cursor.fetchall()
        
        # Convert datetime objects to ISO format strings for JSON serialization
        for subscription in subscriptions:
            if subscription['start_date']:
                subscription['start_date'] = subscription['start_date'].isoformat()
            if subscription['end_date']:
                subscription['end_date'] = subscription['end_date'].isoformat()
        
        cursor.close()
        connection.close()
        return subscriptions

    @staticmethod
    def get_all_subscriptions_filtered(user_name_filter: Optional[str] = None, user_email_filter: Optional[str] = None,
                                     plan_name_filter: Optional[str] = None, status_filter: Optional[str] = None,
                                     date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
        """Get all subscriptions with comprehensive filters"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT us.id, u.name as user_name, u.email as user_email, sp.name as plan_name, 
                   us.status, us.start_date, us.end_date
            FROM user_subscriptions us
            JOIN users u ON us.user_id = u.id
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE 1=1
        """
        params = []
        
        # User name filter
        if user_name_filter and user_name_filter.strip():
            query += " AND u.name LIKE %s"
            params.append(f"%{user_name_filter}%")
        
        # User email filter
        if user_email_filter and user_email_filter.strip():
            query += " AND u.email LIKE %s"
            params.append(f"%{user_email_filter}%")
        
        # Plan name filter
        if plan_name_filter and plan_name_filter.strip():
            query += " AND sp.name = %s"
            params.append(plan_name_filter)
        
        # Status filter
        if status_filter and status_filter.strip() and status_filter != 'all':
            query += " AND us.status = %s"
            params.append(status_filter)
        
        # Date range filters (start_date)
        if date_from and date_from.strip():
            query += " AND DATE(us.start_date) >= %s"
            params.append(date_from)
        
        if date_to and date_to.strip():
            query += " AND DATE(us.start_date) <= %s"
            params.append(date_to)
        
        query += " ORDER BY us.id DESC"
        
        cursor.execute(query, params)
        subscriptions = cursor.fetchall()
        
        # Convert datetime objects to ISO format strings for JSON serialization
        for subscription in subscriptions:
            if subscription['start_date']:
                subscription['start_date'] = subscription['start_date'].isoformat()
            if subscription['end_date']:
                subscription['end_date'] = subscription['end_date'].isoformat()
        
        cursor.close()
        connection.close()
        return subscriptions

    @staticmethod
    def update_subscription_status(subscription_id: int, status: str) -> bool:
        """Update subscription status"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user_subscriptions SET status = %s WHERE id = %s",
            (status, subscription_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def get_all_transactions(status_filter: Optional[str] = None) -> List[Dict]:
        """Get all transactions with filters"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT t.id, u.name as user_name, sp.name as plan, 
                   t.amount, t.status, DATE(t.transaction_date) as date
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            JOIN subscription_plans sp ON t.plan_id = sp.id
        """
        
        if status_filter:
            query += " WHERE t.status = %s"
            cursor.execute(query, (status_filter,))
        else:
            cursor.execute(query)
        
        transactions = cursor.fetchall()
        
        # Convert date objects to ISO format strings for JSON serialization
        for transaction in transactions:
            if transaction['date']:
                transaction['date'] = transaction['date'].isoformat()
        
        cursor.close()
        connection.close()
        return transactions

    @staticmethod
    def get_all_transactions_filtered(user_name_filter: Optional[str] = None, user_email_filter: Optional[str] = None,
                                    status_filter: Optional[str] = None, amount_range: Optional[str] = None,
                                    date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
        """Get all transactions with comprehensive filters"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT t.id, u.name as user_name, sp.name as plan, 
                   t.amount, t.status, DATE(t.transaction_date) as date
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            JOIN subscription_plans sp ON t.plan_id = sp.id
            WHERE 1=1
        """
        params = []
        
        # User name filter
        if user_name_filter and user_name_filter.strip():
            query += " AND u.name LIKE %s"
            params.append(f"%{user_name_filter}%")
        
        # User email filter
        if user_email_filter and user_email_filter.strip():
            query += " AND u.email LIKE %s"
            params.append(f"%{user_email_filter}%")
        
        # Status filter
        if status_filter and status_filter.strip():
            query += " AND t.status = %s"
            params.append(status_filter)
        
        # Amount range filter
        if amount_range and amount_range.strip():
            if amount_range == "0-500":
                query += " AND t.amount BETWEEN 0 AND 500"
            elif amount_range == "501-1000":
                query += " AND t.amount BETWEEN 501 AND 1000"
            elif amount_range == "1001-5000":
                query += " AND t.amount BETWEEN 1001 AND 5000"
            elif amount_range == "5000+":
                query += " AND t.amount > 5000"
        
        # Date range filters
        if date_from and date_from.strip():
            query += " AND DATE(t.transaction_date) >= %s"
            params.append(date_from)
        
        if date_to and date_to.strip():
            query += " AND DATE(t.transaction_date) <= %s"
            params.append(date_to)
        
        query += " ORDER BY t.transaction_date DESC"
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        
        # Convert date objects to ISO format strings for JSON serialization
        for transaction in transactions:
            if transaction['date']:
                transaction['date'] = transaction['date'].isoformat()
        
        cursor.close()
        connection.close()
        return transactions

    @staticmethod
    def get_dashboard_stats() -> Dict:
        """Get dashboard statistics with percentage changes"""
        connection = get_db_connection()
        if not connection:
            return {
                "total_users": 0, "users_change": 0,
                "active_subscriptions": 0, "subscriptions_change": 0,
                "revenue": 0, "revenue_change": 0,
                "transactions_today": 0, "transactions_change": 0
            }
        
        cursor = connection.cursor()
        
        # Total users (current vs last month)
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user' AND created_at < DATE_SUB(NOW(), INTERVAL 1 MONTH)")
        users_last_month = cursor.fetchone()[0]
        users_change = ((total_users - users_last_month) / max(users_last_month, 1)) * 100 if users_last_month > 0 else 0
        
        # Active subscriptions (current vs last month)
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active'")
        active_subscriptions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active' AND created_at < DATE_SUB(NOW(), INTERVAL 1 MONTH)")
        subs_last_month = cursor.fetchone()[0]
        subscriptions_change = ((active_subscriptions - subs_last_month) / max(subs_last_month, 1)) * 100 if subs_last_month > 0 else 0
        
        # Revenue (current month vs last month)
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed' AND MONTH(transaction_date) = MONTH(NOW()) AND YEAR(transaction_date) = YEAR(NOW())")
        revenue_this_month = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed' AND MONTH(transaction_date) = MONTH(DATE_SUB(NOW(), INTERVAL 1 MONTH)) AND YEAR(transaction_date) = YEAR(DATE_SUB(NOW(), INTERVAL 1 MONTH))")
        revenue_last_month = cursor.fetchone()[0] or 0
        revenue_change = ((revenue_this_month - revenue_last_month) / max(revenue_last_month, 1)) * 100 if revenue_last_month > 0 else 0
        
        # Total revenue
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Transactions today vs yesterday
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE DATE(transaction_date) = CURDATE()")
        transactions_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE DATE(transaction_date) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)")
        transactions_yesterday = cursor.fetchone()[0]
        transactions_change = ((transactions_today - transactions_yesterday) / max(transactions_yesterday, 1)) * 100 if transactions_yesterday > 0 else 0
        
        cursor.close()
        connection.close()
        
        return {
            "total_users": total_users,
            "users_change": round(users_change, 1),
            "active_subscriptions": active_subscriptions,
            "subscriptions_change": round(subscriptions_change, 1),
            "revenue": float(total_revenue),
            "revenue_change": round(revenue_change, 1),
            "transactions_today": transactions_today,
            "transactions_change": round(transactions_change, 1)
        }
    
    @staticmethod
    def get_recent_transactions(limit: int = 5) -> List[Dict]:
        """Get recent transactions for dashboard"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.name as user_name, sp.name as plan_name, 
                   t.amount, t.status, DATE(t.transaction_date) as date
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            JOIN subscription_plans sp ON t.plan_id = sp.id
            ORDER BY t.transaction_date DESC
            LIMIT %s
        """, (limit,))
        
        transactions = cursor.fetchall()
        cursor.close()
        connection.close()
        return transactions
    
    @staticmethod
    def get_all_settings() -> List[Dict]:
        """Get all general settings"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM general_settings ORDER BY setting_key")
        settings = cursor.fetchall()
        cursor.close()
        connection.close()
        return settings
    
    @staticmethod
    def update_setting(setting_key: str, setting_value: str) -> bool:
        """Update a setting value"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE general_settings SET setting_value = %s WHERE setting_key = %s",
            (setting_value, setting_key)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def get_user_ai_settings(user_id: int) -> Optional[Dict]:
        """Get AI settings for a user"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_ai_settings WHERE user_id = %s", (user_id,))
        settings = cursor.fetchone()
        cursor.close()
        connection.close()
        return settings
    
    @staticmethod
    def create_user_ai_settings(user_id: int, openai_key: str = '', openai_model: str = 'gpt-3.5-turbo', 
                               qdrant_url: str = '', qdrant_key: str = '', qdrant_collection: str = 'user_docs') -> bool:
        """Create AI settings for a user"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO user_ai_settings (user_id, openai_api_key, openai_model, qdrant_url, qdrant_api_key, qdrant_collection) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, openai_key, openai_model, qdrant_url, qdrant_key, qdrant_collection)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def update_user_ai_settings(user_id: int, openai_key: str, openai_model: str, 
                               qdrant_url: str, qdrant_key: str, qdrant_collection: str) -> bool:
        """Update AI settings for a user"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user_ai_settings SET openai_api_key = %s, openai_model = %s, qdrant_url = %s, qdrant_api_key = %s, qdrant_collection = %s WHERE user_id = %s",
            (openai_key, openai_model, qdrant_url, qdrant_key, qdrant_collection, user_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def create_user_subscription(user_id: int, plan_id: int, start_date: str, end_date: str, 
                                stripe_session_id: str = None) -> bool:
        """Create new user subscription and cancel existing active ones"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        
        # First, cancel all existing active subscriptions for this user
        cursor.execute(
            "UPDATE user_subscriptions SET status = 'cancelled' WHERE user_id = %s AND status = 'active'",
            (user_id,)
        )
        
        # Then create the new subscription
        cursor.execute(
            "INSERT INTO user_subscriptions (user_id, plan_id, start_date, end_date, status) VALUES (%s, %s, %s, %s, 'active')",
            (user_id, plan_id, start_date, end_date)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def create_transaction(user_id: int, plan_id: int, amount: float, status: str = 'pending', 
                          stripe_session_id: str = None) -> int:
        """Create new transaction and return transaction ID"""
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO transactions (user_id, plan_id, amount, status) VALUES (%s, %s, %s, %s)",
            (user_id, plan_id, amount, status)
        )
        transaction_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        connection.close()
        return transaction_id
    
    @staticmethod
    def update_transaction_status(transaction_id: int, status: str) -> bool:
        """Update transaction status"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE transactions SET status = %s WHERE id = %s",
            (status, transaction_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def get_user_active_subscription(user_id: int) -> Optional[Dict]:
        """Get user's active subscription"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT us.*, sp.name as plan_name, sp.price 
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.user_id = %s AND us.status = 'active'
            ORDER BY us.created_at DESC LIMIT 1
        """, (user_id,))
        subscription = cursor.fetchone()
        cursor.close()
        connection.close()
        return subscription
    
    @staticmethod
    def get_user_plan(user_id: int) -> Optional[Dict]:
        """Get user's current plan with limits"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT up.*, sp.name as plan_name, sp.price as plan_price
            FROM user_plans up
            LEFT JOIN subscription_plans sp ON up.plan_id = sp.id
            WHERE up.user_id = %s AND up.status = 'active'
            ORDER BY up.created_at DESC LIMIT 1
        """, (user_id,))
        plan = cursor.fetchone()
        cursor.close()
        connection.close()
        return plan
    
    @staticmethod
    def create_user_plan(user_id: int, plan_id: int, plan_type: str = 'paid') -> bool:
        """Create/Update user plan when they purchase a subscription"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor(dictionary=True)
        
        # Get plan limits from subscription_plans
        cursor.execute("SELECT max_documents, max_chat_prompts FROM subscription_plans WHERE id = %s", (plan_id,))
        plan_limits = cursor.fetchone()
        
        if not plan_limits:
            cursor.close()
            connection.close()
            return False
        
        # Deactivate existing plans
        cursor.execute("UPDATE user_plans SET status = 'cancelled' WHERE user_id = %s AND status = 'active'", (user_id,))
        
        # Create new plan
        from datetime import datetime, timedelta
        end_date = datetime.now() + timedelta(days=30) if plan_type == 'paid' else None
        
        cursor.execute("""
            INSERT INTO user_plans (user_id, plan_id, plan_type, max_documents, max_prompts, end_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, plan_id, plan_type, plan_limits['max_documents'], plan_limits['max_chat_prompts'], end_date))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def check_document_limit(user_id: int) -> Dict:
        """Check if user can upload more documents"""
        plan = DatabaseOperations.get_user_plan(user_id)
        if not plan:
            return {"can_upload": False, "message": "No active plan found"}
        
        can_upload = plan['used_documents'] < plan['max_documents']
        return {
            "can_upload": can_upload,
            "used": plan['used_documents'],
            "max": plan['max_documents'],
            "remaining": plan['max_documents'] - plan['used_documents'],
            "plan_name": plan['plan_name'],
            "plan_type": plan['plan_type']
        }
    
    @staticmethod
    def check_prompt_limit(user_id: int) -> Dict:
        """Check if user can make more chat prompts"""
        plan = DatabaseOperations.get_user_plan(user_id)
        if not plan:
            return {"can_prompt": False, "message": "No active plan found"}
        
        can_prompt = plan['used_prompts'] < plan['max_prompts']
        return {
            "can_prompt": can_prompt,
            "used": plan['used_prompts'],
            "max": plan['max_prompts'],
            "remaining": plan['max_prompts'] - plan['used_prompts'],
            "plan_name": plan['plan_name'],
            "plan_type": plan['plan_type']
        }
    
    @staticmethod
    def increment_document_usage(user_id: int) -> bool:
        """Increment user's document usage count"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE user_plans 
            SET used_documents = used_documents + 1 
            WHERE user_id = %s AND status = 'active'
        """, (user_id,))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def decrement_document_usage(user_id: int) -> bool:
        """Decrement user's document usage count when document is deleted"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE user_plans 
            SET used_documents = GREATEST(used_documents - 1, 0)
            WHERE user_id = %s AND status = 'active'
        """, (user_id,))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def increment_prompt_usage(user_id: int) -> bool:
        """Increment user's prompt usage count"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE user_plans 
            SET used_prompts = used_prompts + 1 
            WHERE user_id = %s AND status = 'active'
        """, (user_id,))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def reset_monthly_usage(user_id: int) -> bool:
        """Reset monthly usage counters (to be called monthly)"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE user_plans 
            SET used_prompts = 0 
            WHERE user_id = %s AND status = 'active'
        """, (user_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    # User Document Management Methods
    @staticmethod
    def save_user_document(user_id: int, filename: str, original_filename: str, document_name: str,
                          file_size: int, file_type: str, collection_name: str, tags: str = "",
                          document_date: str = None, created_date: str = None, chunk_count: int = 0) -> int:
        """Save user document record to database"""
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO user_documents 
            (user_id, filename, original_filename, document_name, file_size, file_type, 
             collection_name, tags, document_date, created_date, chunk_count, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed')
        """, (user_id, filename, original_filename, document_name, file_size, file_type,
              collection_name, tags, document_date, created_date, chunk_count))
        
        doc_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        connection.close()
        return doc_id
    
    @staticmethod
    def get_user_documents(user_id: int) -> List[Dict]:
        """Get all documents uploaded by a user"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, filename, original_filename, document_name, file_size, file_type,
                   collection_name, tags, document_date, created_date, upload_date, 
                   chunk_count, status
            FROM user_documents 
            WHERE user_id = %s 
            ORDER BY upload_date DESC
        """, (user_id,))
        
        documents = cursor.fetchall()
        cursor.close()
        connection.close()
        return documents
    
    @staticmethod
    def get_user_document_by_id(user_id: int, doc_id: int) -> Optional[Dict]:
        """Get a specific document by ID, ensuring it belongs to the user"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM user_documents 
            WHERE id = %s AND user_id = %s
        """, (doc_id, user_id))
        
        document = cursor.fetchone()
        cursor.close()
        connection.close()
        return document
    
    @staticmethod
    def delete_user_document(user_id: int, doc_id: int) -> bool:
        """Delete a user's document record"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM user_documents 
            WHERE id = %s AND user_id = %s
        """, (doc_id, user_id))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def save_user_collection(user_id: int, collection_name: str, document_name: str) -> bool:
        """Map collection to user for vector DB separation"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT IGNORE INTO user_collections (user_id, collection_name, document_name)
            VALUES (%s, %s, %s)
        """, (user_id, collection_name, document_name))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    
    @staticmethod
    def get_user_collections(user_id: int) -> List[Dict]:
        """Get all collections belonging to a user"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT collection_name, document_name, created_at
            FROM user_collections 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        collections = cursor.fetchall()
        cursor.close()
        connection.close()
        return collections
    
    @staticmethod
    def delete_user_collection(user_id: int, collection_name: str) -> bool:
        """Delete user's collection mapping"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM user_collections 
            WHERE user_id = %s AND collection_name = %s
        """, (user_id, collection_name))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    # Chat History Management Methods
    @staticmethod
    def save_chat_history(user_id: int, session_id: str, user_query: str, ai_response: str,
                         document_filter: str = None, sources: List[Dict] = None, response_time: float = 0) -> int:
        """Save user chat interaction to history"""
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        import json
        sources_json = json.dumps(sources) if sources else None
        
        cursor.execute("""
            INSERT INTO chat_history 
            (user_id, session_id, user_query, ai_response, document_filter, sources, response_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, session_id, user_query, ai_response, document_filter, sources_json, response_time))
        
        chat_id = cursor.lastrowid
        connection.commit()
        cursor.close()
        connection.close()
        return chat_id
    
    @staticmethod
    def get_user_chat_history(user_id: int, session_id: str = None, limit: int = 50) -> List[Dict]:
        """Get user's chat history, optionally filtered by session"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        if session_id:
            cursor.execute("""
                SELECT id, session_id, user_query, ai_response, document_filter, 
                       sources, response_time, created_at
                FROM chat_history 
                WHERE user_id = %s AND session_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, session_id, limit))
        else:
            cursor.execute("""
                SELECT id, session_id, user_query, ai_response, document_filter, 
                       sources, response_time, created_at
                FROM chat_history 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
        
        history = cursor.fetchall()
        
        # Parse JSON sources and convert datetime to string
        import json
        for item in history:
            if item['sources']:
                try:
                    item['sources'] = json.loads(item['sources'])
                except:
                    item['sources'] = []
            
            # Convert datetime objects to ISO format strings for JSON serialization
            if item['created_at']:
                item['created_at'] = item['created_at'].isoformat()

        cursor.close()
        connection.close()
        return history    @staticmethod
    def delete_user_chat_session(user_id: int, session_id: str) -> bool:
        """Delete all chat history for a specific session"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM chat_history 
            WHERE user_id = %s AND session_id = %s
        """, (user_id, session_id))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def get_user_chat_sessions(user_id: int) -> List[Dict]:
        """Get list of user's chat sessions"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT session_id, 
                   COUNT(*) as message_count,
                   MIN(created_at) as started_at,
                   MAX(created_at) as last_activity
            FROM chat_history 
            WHERE user_id = %s 
            GROUP BY session_id 
            ORDER BY last_activity DESC
        """, (user_id,))
        
        sessions = cursor.fetchall()
        
        # Convert datetime objects to ISO format strings for JSON serialization
        for session in sessions:
            if session['started_at']:
                session['started_at'] = session['started_at'].isoformat()
            if session['last_activity']:
                session['last_activity'] = session['last_activity'].isoformat()
        
        cursor.close()
        connection.close()
        return sessions
    
    @staticmethod
    def get_user_documents_count(user_id: int) -> int:
        """Get count of user's uploaded documents"""
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM user_documents WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result[0] if result else 0
    
    @staticmethod
    def get_user_current_plan(user_id: int) -> Dict:
        """Get user's current active plan details"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT up.*, sp.name as plan_name, sp.price, sp.max_documents, sp.max_chat_prompts
            FROM user_plans up
            JOIN subscription_plans sp ON up.plan_id = sp.id
            WHERE up.user_id = %s AND up.status = 'active'
            ORDER BY up.created_at DESC
            LIMIT 1
        """, (user_id,))
        
        plan = cursor.fetchone()
        cursor.close()
        connection.close()
        return plan
    
    @staticmethod
    def get_user_subscriptions(user_id: int) -> List[Dict]:
        """Get user's subscription history"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT us.*, sp.name as plan_name, sp.price
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.user_id = %s
            ORDER BY us.created_at DESC
        """, (user_id,))
        
        subscriptions = cursor.fetchall()
        cursor.close()
        connection.close()
        return subscriptions
    
    @staticmethod
    def get_user_recent_chats(user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recent chat messages"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_query, ai_response, created_at, session_id
            FROM chat_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        
        chats = cursor.fetchall()
        cursor.close()
        connection.close()
        return chats
    
    @staticmethod
    def get_user_usage_stats(user_id: int) -> Dict:
        """Get user's usage statistics"""
        connection = get_db_connection()
        if not connection:
            return {}
        
        cursor = connection.cursor(dictionary=True)
        
        # Get chat count
        cursor.execute("SELECT COUNT(*) as chat_count FROM chat_history WHERE user_id = %s", (user_id,))
        chat_result = cursor.fetchone()
        
        # Get documents count
        cursor.execute("SELECT COUNT(*) as doc_count FROM user_documents WHERE user_id = %s", (user_id,))
        doc_result = cursor.fetchone()
        
        # Get current plan limits
        cursor.execute("""
            SELECT up.max_documents, up.max_prompts, up.used_documents, up.used_prompts
            FROM user_plans up
            WHERE up.user_id = %s AND up.status = 'active'
            ORDER BY up.created_at DESC
            LIMIT 1
        """, (user_id,))
        plan_result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return {
            'total_chats': chat_result['chat_count'] if chat_result else 0,
            'total_documents': doc_result['doc_count'] if doc_result else 0,
            'max_documents': plan_result['max_documents'] if plan_result else 0,
            'max_prompts': plan_result['max_prompts'] if plan_result else 0,
            'documents_used': plan_result['used_documents'] if plan_result else 0,
            'prompts_used': plan_result['used_prompts'] if plan_result else 0
        }
    
    @staticmethod
    def get_user_transactions(user_id: int) -> List[Dict]:
        """Get user's transaction history"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, sp.name as plan_name
            FROM transactions t
            LEFT JOIN subscription_plans sp ON t.plan_id = sp.id
            WHERE t.user_id = %s
            ORDER BY t.transaction_date DESC
        """, (user_id,))
        
        transactions = cursor.fetchall()
        
        # Convert datetime objects to ISO format strings for JSON serialization
        for transaction in transactions:
            if transaction['transaction_date']:
                transaction['transaction_date'] = transaction['transaction_date'].isoformat()
        
        cursor.close()
        connection.close()
        return transactions
    
    @staticmethod
    def get_active_faqs(category=None, limit=None):
        """Get active FAQs for display to users"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM faqs WHERE is_active = TRUE"
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        query += " ORDER BY sort_order ASC, created_at DESC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cursor.execute(query, params)
        faqs = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return faqs
    
    @staticmethod
    def get_faq_categories():
        """Get all FAQ categories"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor()
        
        query = "SELECT DISTINCT category FROM faqs WHERE is_active = TRUE ORDER BY category"
        cursor.execute(query)
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return categories
    
    @staticmethod
    def get_user_recent_transactions(user_id: int, limit: int = 5) -> List[Dict]:
        """Get user's recent transactions with limit"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, sp.name as plan_name
            FROM transactions t
            LEFT JOIN subscription_plans sp ON t.plan_id = sp.id
            WHERE t.user_id = %s
            ORDER BY t.transaction_date DESC
            LIMIT %s
        """, (user_id, limit))
        
        transactions = cursor.fetchall()
        cursor.close()
        connection.close()
        return transactions
    
    @staticmethod
    def get_user_transactions_filtered(user_id: int, status: str = None, amount_range: str = None, 
                                     date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get user's transactions with filters"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # Build query with filters
        query = """
            SELECT t.*, sp.name as plan_name
            FROM transactions t
            LEFT JOIN subscription_plans sp ON t.plan_id = sp.id
            WHERE t.user_id = %s
        """
        params = [user_id]
        
        if status and status.strip():
            query += " AND t.status = %s"
            params.append(status)
        
        if amount_range and amount_range.strip():
            if amount_range == "0-50":
                query += " AND t.amount BETWEEN 0 AND 50"
            elif amount_range == "51-100":
                query += " AND t.amount BETWEEN 51 AND 100"
            elif amount_range == "101-500":
                query += " AND t.amount BETWEEN 101 AND 500"
            elif amount_range == "500+":
                query += " AND t.amount > 500"
        
        if date_from and date_from.strip():
            query += " AND DATE(t.transaction_date) >= %s"
            params.append(date_from)
        
        if date_to and date_to.strip():
            query += " AND DATE(t.transaction_date) <= %s"
            params.append(date_to)
        
        query += " ORDER BY t.transaction_date DESC"
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        
        # Convert datetime objects to ISO format strings for JSON serialization
        for transaction in transactions:
            if transaction['transaction_date']:
                transaction['transaction_date'] = transaction['transaction_date'].isoformat()
        
        cursor.close()
        connection.close()
        return transactions

    @staticmethod
    def get_plan_by_id(plan_id: int) -> Optional[Dict]:
        """Get plan by ID"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM subscription_plans WHERE id = %s", (plan_id,))
        plan = cursor.fetchone()
        cursor.close()
        connection.close()
        return plan
    
    @staticmethod
    def admin_assign_plan_to_user(user_id: int, plan_id: int, admin_id: int, payment_method: str, amount: float) -> bool:
        """Admin assigns a plan to user with transaction creation"""
        connection = get_db_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Start transaction
            connection.start_transaction()
            
            # 1. Deactivate any existing active plans for the user
            cursor.execute("""
                UPDATE user_plans 
                SET status = 'expired' 
                WHERE user_id = %s AND status = 'active'
            """, (user_id,))
            
            # 2. Create new user plan
            cursor.execute("""
                INSERT INTO user_plans (user_id, plan_id, status, plan_type, created_at)
                VALUES (%s, %s, 'active', 'paid', NOW())
            """, (user_id, plan_id))
            
            # 3. Create transaction record
            cursor.execute("""
                INSERT INTO transactions (user_id, plan_id, amount, status, payment_method, transaction_date)
                VALUES (%s, %s, %s, 'completed', %s, NOW())
            """, (user_id, plan_id, amount, payment_method))
            
            # 4. Create/Update user subscription
            cursor.execute("""
                INSERT INTO user_subscriptions (user_id, plan_id, start_date, end_date, status, created_at)
                VALUES (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 1 MONTH), 'active', NOW())
            """, (user_id, plan_id))
            
            # Commit transaction
            connection.commit()
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            # Rollback on error
            print(f"Error in admin_assign_plan_to_user: {str(e)}")
            connection.rollback()
            cursor.close()
            connection.close()
            return False

    @staticmethod
    def get_all_settings() -> List[Dict]:
        """Get all settings from the database"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM settings ORDER BY category, setting_key")
        settings = cursor.fetchall()
        
        cursor.close()
        connection.close()
        return settings
    
    @staticmethod
    def get_settings_by_category(category: str) -> List[Dict]:
        """Get settings by category"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM settings WHERE category = %s ORDER BY setting_key", (category,))
        settings = cursor.fetchall()
        
        cursor.close()
        connection.close()
        return settings
    
    @staticmethod
    def get_settings_dict() -> Dict[str, str]:
        """Get all settings as a key-value dictionary"""
        settings = DatabaseOperations.get_all_settings()
        return {setting['setting_key']: setting['setting_value'] for setting in settings}
    
    @staticmethod
    def update_setting(setting_key: str, setting_value: str) -> bool:
        """Update a specific setting"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE settings 
            SET setting_value = %s, updated_at = NOW() 
            WHERE setting_key = %s
        """, (setting_value, setting_key))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def save_contact_submission(name: str, email: str, phone: str, message: str) -> bool:
        """Save contact form submission to database"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO contact_us (name, email, phone, message) 
            VALUES (%s, %s, %s, %s)
        """, (name, email, phone, message))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success
    
    @staticmethod
    def get_all_contact_submissions() -> List[Dict]:
        """Get all contact form submissions"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM contact_us 
            ORDER BY created_at DESC
        """)
        submissions = cursor.fetchall()
        
        cursor.close()
        connection.close()
        return submissions
    
    @staticmethod
    def get_filtered_contact_submissions(status: str = None, search: str = None, date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get filtered contact form submissions"""
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # Build WHERE clause dynamically
        where_conditions = []
        params = []
        
        if status and status != 'all':
            where_conditions.append("status = %s")
            params.append(status)
        
        if search:
            where_conditions.append("(first_name LIKE %s OR last_name LIKE %s OR email LIKE %s OR message LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if date_from:
            where_conditions.append("DATE(created_at) >= %s")
            params.append(date_from)
        
        if date_to:
            where_conditions.append("DATE(created_at) <= %s")
            params.append(date_to)
        
        # Construct the query
        query = "SELECT * FROM contact_us"
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        submissions = cursor.fetchall()
        
        cursor.close()
        connection.close()
        return submissions
    
    @staticmethod
    def get_contact_submission_by_id(contact_id: int) -> Optional[Dict]:
        """Get contact submission by ID"""
        connection = get_db_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM contact_us WHERE id = %s", (contact_id,))
        submission = cursor.fetchone()
        
        cursor.close()
        connection.close()
        return submission
    
    @staticmethod
    def update_contact_status(contact_id: int, status: str) -> bool:
        """Update contact submission status"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE contact_us 
            SET status = %s, updated_at = NOW() 
            WHERE id = %s
        """, (status, contact_id))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success

    @staticmethod
    def get_admin_chat_history(page: int = 1, per_page: int = 20, user_id: int = None, search: str = None) -> Dict:
        """Get chat history for admin with pagination and filtering"""
        connection = get_db_connection()
        if not connection:
            return {"chat_history": [], "total": 0, "page": page, "per_page": per_page}
        
        cursor = connection.cursor(dictionary=True)
        
        # Check if plans table exists
        cursor.execute("SHOW TABLES LIKE 'plans'")
        plans_exists = cursor.fetchone() is not None
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("ch.user_id = %s")
            params.append(user_id)
            
        if search:
            where_conditions.append("(u.name LIKE %s OR u.email LIKE %s OR ch.user_query LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM chat_history ch
            LEFT JOIN users u ON ch.user_id = u.id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        offset = (page - 1) * per_page
        
        if plans_exists:
            data_query = f"""
                SELECT 
                    ch.id,
                    ch.user_id,
                    u.name as user_name,
                    u.email as user_email,
                    ch.session_id,
                    ch.user_query,
                    ch.ai_response,
                    ch.document_filter,
                    ch.sources,
                    ch.response_time,
                    ch.created_at,
                    COALESCE(p.name, 'No Plan') as plan_name,
                    u.current_prompt_usage,
                    COALESCE(p.max_chat_prompts, 0) as max_chat_prompts
                FROM chat_history ch
                LEFT JOIN users u ON ch.user_id = u.id
                LEFT JOIN plans p ON u.current_plan_id = p.id
                {where_clause}
                ORDER BY ch.created_at DESC
                LIMIT %s OFFSET %s
            """
        else:
            data_query = f"""
                SELECT 
                    ch.id,
                    ch.user_id,
                    u.name as user_name,
                    u.email as user_email,
                    ch.session_id,
                    ch.user_query,
                    ch.ai_response,
                    ch.document_filter,
                    ch.sources,
                    ch.response_time,
                    ch.created_at,
                    'No Plan' as plan_name,
                    u.current_prompt_usage,
                    0 as max_chat_prompts
                FROM chat_history ch
                LEFT JOIN users u ON ch.user_id = u.id
                {where_clause}
                ORDER BY ch.created_at DESC
                LIMIT %s OFFSET %s
            """
        
        params.extend([per_page, offset])
        cursor.execute(data_query, params)
        chat_history = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return {
            "chat_history": chat_history,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    @staticmethod
    def delete_chat_history(chat_id: int) -> bool:
        """Delete a chat history record"""
        connection = get_db_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("DELETE FROM chat_history WHERE id = %s", (chat_id,))
        
        success = cursor.rowcount > 0
        connection.commit()
        cursor.close()
        connection.close()
        return success

    @staticmethod
    def get_chat_usage_stats() -> Dict:
        """Get chat usage statistics for admin dashboard"""
        connection = get_db_connection()
        if not connection:
            return {}
        
        cursor = connection.cursor(dictionary=True)
        
        # Check if plans table exists
        cursor.execute("SHOW TABLES LIKE 'plans'")
        plans_exists = cursor.fetchone() is not None
        
        # Get total chats today, this week, this month
        cursor.execute("""
            SELECT 
                COUNT(*) as total_chats,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(CASE WHEN DATE(created_at) = CURDATE() THEN 1 END) as chats_today,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as chats_this_week,
                COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as chats_this_month,
                AVG(response_time) as avg_response_time
            FROM chat_history
        """)
        
        general_stats = cursor.fetchone()
        
        # Get top users by chat count
        if plans_exists:
            cursor.execute("""
                SELECT 
                    u.name,
                    u.email,
                    COUNT(ch.id) as chat_count,
                    u.current_prompt_usage,
                    COALESCE(p.max_chat_prompts, 0) as max_chat_prompts,
                    COALESCE(p.name, 'No Plan') as plan_name
                FROM chat_history ch
                LEFT JOIN users u ON ch.user_id = u.id
                LEFT JOIN plans p ON u.current_plan_id = p.id
                GROUP BY ch.user_id
                ORDER BY chat_count DESC
                LIMIT 10
            """)
        else:
            cursor.execute("""
                SELECT 
                    u.name,
                    u.email,
                    COUNT(ch.id) as chat_count,
                    u.current_prompt_usage,
                    0 as max_chat_prompts,
                    'No Plan' as plan_name
                FROM chat_history ch
                LEFT JOIN users u ON ch.user_id = u.id
                GROUP BY ch.user_id
                ORDER BY chat_count DESC
                LIMIT 10
            """)
        
        top_users = cursor.fetchall()
        
        # Get chat activity by hour
        cursor.execute("""
            SELECT 
                HOUR(created_at) as hour,
                COUNT(*) as chat_count
            FROM chat_history
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY HOUR(created_at)
            ORDER BY hour
        """)
        
        hourly_activity = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return {
            "general_stats": general_stats,
            "top_users": top_users,
            "hourly_activity": hourly_activity
        }