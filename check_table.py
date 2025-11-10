#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

def check_user_plans_table():
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return
    
    cursor = connection.cursor()
    
    # Check if table exists
    cursor.execute("SHOW TABLES LIKE 'user_plans'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("user_plans table exists")
        # Show table structure
        cursor.execute("DESCRIBE user_plans")
        columns = cursor.fetchall()
        print("Table structure:")
        for col in columns:
            print(f"  {col}")
    else:
        print("user_plans table does not exist")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    check_user_plans_table()