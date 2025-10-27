#!/usr/bin/env python3
"""
Migration script to create user_plans table for tracking user subscription limits
"""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def create_user_plans_table():
    """Create user_plans table and set default free plans"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'legaleagle')
        )
        
        cursor = connection.cursor()
        
        # Create user_plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                plan_id INT DEFAULT NULL,
                plan_type ENUM('free', 'paid') DEFAULT 'free',
                max_documents INT DEFAULT 5,
                max_prompts INT DEFAULT 50,
                used_documents INT DEFAULT 0,
                used_prompts INT DEFAULT 0,
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME DEFAULT NULL,
                status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
            )
        """)
        print("✅ Created user_plans table")
        
        # Create a default free plan in subscription_plans
        cursor.execute("""
            INSERT INTO subscription_plans (name, price, max_documents, max_chat_prompts, features, validity_days, status) 
            VALUES ('Free Plan', 0.00, 5, 50, '<ul><li>5 Document uploads</li><li>50 Chat prompts per month</li><li>Basic legal AI assistance</li></ul>', 30, 'active')
            ON DUPLICATE KEY UPDATE name=name
        """)
        
        # Get the free plan ID
        cursor.execute("SELECT id FROM subscription_plans WHERE name = 'Free Plan' AND price = 0")
        free_plan = cursor.fetchone()
        free_plan_id = free_plan[0] if free_plan else None
        
        print(f"✅ Free Plan ID: {free_plan_id}")
        
        # Set all existing users to free plan
        if free_plan_id:
            cursor.execute("""
                INSERT INTO user_plans (user_id, plan_id, plan_type, max_documents, max_prompts)
                SELECT id, %s, 'free', 5, 50 FROM users 
                WHERE id NOT IN (SELECT DISTINCT user_id FROM user_plans)
            """, (free_plan_id,))
            print("✅ Assigned free plans to existing users")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("User plans system migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    create_user_plans_table()