#!/usr/bin/env python3
"""
Migration script to add address fields to users table
"""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def add_address_fields():
    """Add address fields to users table"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'legaleagle')
        )
        
        cursor = connection.cursor()
        
        # Add address fields to users table
        address_fields = [
            "ADD COLUMN address_line1 VARCHAR(255) DEFAULT NULL",
            "ADD COLUMN address_line2 VARCHAR(255) DEFAULT NULL", 
            "ADD COLUMN city VARCHAR(100) DEFAULT NULL",
            "ADD COLUMN state VARCHAR(100) DEFAULT NULL",
            "ADD COLUMN postal_code VARCHAR(20) DEFAULT NULL",
            "ADD COLUMN country VARCHAR(100) DEFAULT 'India'"
        ]
        
        for field in address_fields:
            try:
                cursor.execute(f"ALTER TABLE users {field}")
                print(f"Added field: {field}")
            except mysql.connector.Error as e:
                if "Duplicate column name" in str(e):
                    print(f"Field already exists: {field}")
                else:
                    print(f"Error adding field {field}: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Address fields migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    add_address_fields()