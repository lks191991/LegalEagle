#!/usr/bin/env python3
"""
Create contact_us table
"""

from database import get_db_connection

def create_contact_table():
    """Create contact_us table"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return False
    
    cursor = connection.cursor()
    
    # Create contact_us table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_us (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            status ENUM('new', 'replied', 'closed') DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    connection.commit()
    cursor.close()
    connection.close()
    return True

if __name__ == "__main__":
    if create_contact_table():
        print("Contact table created successfully!")
    else:
        print("Failed to create contact table")