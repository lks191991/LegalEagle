from database import get_db_connection

class ChatHistoryOperations:
    @staticmethod
    def get_admin_chat_history(page=1, per_page=20, user_id=None, search=None, date_from=None, date_to=None):
        """Get chat history for admin panel"""
        connection = get_db_connection()
        if not connection:
            return {"chat_history": [], "total": 0, "pages": 0}
        
        cursor = connection.cursor(dictionary=True)
        offset = (page - 1) * per_page
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("ch.user_id = %s")
            params.append(user_id)
        
        if search:
            where_conditions.append("(ch.user_query LIKE %s OR ch.ai_response LIKE %s OR u.name LIKE %s OR u.email LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if date_from:
            where_conditions.append("DATE(ch.created_at) >= %s")
            params.append(date_from)
        
        if date_to:
            where_conditions.append("DATE(ch.created_at) <= %s")
            params.append(date_to)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        cursor.execute(f"""
            SELECT COUNT(*) as total 
            FROM chat_history ch 
            LEFT JOIN users u ON ch.user_id = u.id 
            {where_clause}
        """, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results with user info
        cursor.execute(f"""
            SELECT ch.*, u.name as user_name, u.email as user_email
            FROM chat_history ch 
            LEFT JOIN users u ON ch.user_id = u.id 
            {where_clause}
            ORDER BY ch.created_at DESC 
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        chat_history = cursor.fetchall()
        
        # Convert Decimal objects to float for JSON serialization
        for chat in chat_history:
            if chat.get('response_time'):
                chat['response_time'] = float(chat['response_time'])
        
        cursor.close()
        connection.close()
        
        return {
            "chat_history": chat_history,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
            "current_page": page
        }
    
    @staticmethod
    def delete_chat_history(chat_id):
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
    def get_chat_usage_stats():
        """Get chat usage statistics"""
        connection = get_db_connection()
        if not connection:
            return {}
        
        cursor = connection.cursor(dictionary=True)
        
        # Total chats
        cursor.execute("SELECT COUNT(*) as total_chats FROM chat_history")
        total_chats = cursor.fetchone()['total_chats']
        
        # Chats today
        cursor.execute("SELECT COUNT(*) as today_chats FROM chat_history WHERE DATE(created_at) = CURDATE()")
        today_chats = cursor.fetchone()['today_chats']
        
        # Average response time
        cursor.execute("SELECT AVG(response_time) as avg_response_time FROM chat_history WHERE response_time IS NOT NULL")
        avg_response_time = cursor.fetchone()['avg_response_time'] or 0
        
        # Most active users
        cursor.execute("""
            SELECT u.name, u.email, COUNT(*) as chat_count 
            FROM chat_history ch 
            LEFT JOIN users u ON ch.user_id = u.id 
            GROUP BY ch.user_id 
            ORDER BY chat_count DESC 
            LIMIT 5
        """)
        top_users = cursor.fetchall()
        
        # Popular documents
        cursor.execute("""
            SELECT document_filter, COUNT(*) as usage_count 
            FROM chat_history 
            WHERE document_filter IS NOT NULL 
            GROUP BY document_filter 
            ORDER BY usage_count DESC 
            LIMIT 5
        """)
        popular_docs = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return {
            "total_chats": total_chats,
            "today_chats": today_chats,
            "avg_response_time": round(float(avg_response_time), 2) if avg_response_time else 0,
            "top_users": top_users,
            "popular_documents": popular_docs
        }