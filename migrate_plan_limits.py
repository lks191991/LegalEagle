#!/usr/bin/env python3
"""
Migration script to add document upload and chat prompt limits to subscription_plans table
"""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def add_plan_limit_fields():
    """Add limit fields to subscription_plans table"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'legaleagle')
        )
        
        cursor = connection.cursor()
        
        # Add new limit fields to subscription_plans table
        limit_fields = [
            "ADD COLUMN max_documents INT DEFAULT 10 COMMENT 'Maximum documents user can upload'",
            "ADD COLUMN max_chat_prompts INT DEFAULT 100 COMMENT 'Maximum chat prompts per month'"
        ]
        
        for field in limit_fields:
            try:
                cursor.execute(f"ALTER TABLE subscription_plans {field}")
                print(f"Added field: {field}")
            except mysql.connector.Error as e:
                if "Duplicate column name" in str(e):
                    print(f"Field already exists: {field}")
                else:
                    print(f"Error adding field {field}: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Plan limit fields migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    add_plan_limit_fields()