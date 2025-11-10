#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection

def seed_user_plans():
    print("Seeding user_plans table...")
    
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return
    
    cursor = connection.cursor()
    
    # Insert sample user plans
    cursor.execute("""
        INSERT IGNORE INTO user_plans (user_id, plan_id, plan_name, plan_price, max_documents, max_chat_prompts, status) VALUES 
        (2, 1, 'Solo Lawyer', 99.00, 1000, 5000, 'active'),
        (3, 2, 'Law Firm', 79.00, 999999, 999999, 'active')
    """)
    
    connection.commit()
    cursor.close()
    connection.close()
    print("User plans seeded successfully!")

if __name__ == "__main__":
    seed_user_plans()