#!/usr/bin/env python3
"""
Add mobile_number column to existing users table
"""

from database import get_db_connection

def add_mobile_column():
    """Add mobile_number column to users table"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return False
    
    cursor = connection.cursor()
    
    try:
        # Check if mobile_number column already exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'mobile_number'
            AND TABLE_SCHEMA = DATABASE()
        """)
        
        if cursor.fetchone():
            print("mobile_number column already exists")
            return True
        
        # Add mobile_number column after email
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN mobile_number VARCHAR(20) DEFAULT NULL 
            AFTER email
        """)
        
        connection.commit()
        print("mobile_number column added successfully!")
        return True
        
    except Exception as e:
        print(f"Error adding mobile_number column: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    add_mobile_column()