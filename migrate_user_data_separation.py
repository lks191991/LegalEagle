#!/usr/bin/env python3
"""
Database migration to add user-based data separation
Run this script to add user documents and chat history tables
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'legaleagle'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def migrate_user_documents_table():
    """Create user documents table for tracking uploaded documents"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Check if table already exists
    cursor.execute("SHOW TABLES LIKE 'user_documents'")
    if cursor.fetchone():
        print("user_documents table already exists")
        cursor.close()
        connection.close()
        return True
    
    # Create user_documents table
    cursor.execute("""
        CREATE TABLE user_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            filename VARCHAR(500) NOT NULL,
            original_filename VARCHAR(500) NOT NULL,
            document_name VARCHAR(500) NOT NULL,
            file_size BIGINT DEFAULT 0,
            file_type VARCHAR(50),
            collection_name VARCHAR(500) NOT NULL,
            tags TEXT,
            document_date VARCHAR(50),
            created_date VARCHAR(50),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chunk_count INT DEFAULT 0,
            status ENUM('uploaded', 'processing', 'completed', 'failed') DEFAULT 'uploaded',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_collection_name (collection_name),
            INDEX idx_upload_date (upload_date)
        )
    """)
    
    print("✅ user_documents table created successfully")
    connection.commit()
    cursor.close()
    connection.close()
    return True

def migrate_chat_history_table():
    """Create chat history table for user conversations"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Check if table already exists
    cursor.execute("SHOW TABLES LIKE 'chat_history'")
    if cursor.fetchone():
        print("chat_history table already exists")
        cursor.close()
        connection.close()
        return True
    
    # Create chat_history table
    cursor.execute("""
        CREATE TABLE chat_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            session_id VARCHAR(100) NOT NULL,
            user_query TEXT NOT NULL,
            ai_response LONGTEXT NOT NULL,
            document_filter VARCHAR(500),
            sources JSON,
            response_time DECIMAL(10,3) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_session_id (session_id),
            INDEX idx_created_at (created_at)
        )
    """)
    
    print("✅ chat_history table created successfully")
    connection.commit()
    cursor.close()
    connection.close()
    return True

def migrate_user_collections_table():
    """Create user collections table to map collection names to users"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Check if table already exists
    cursor.execute("SHOW TABLES LIKE 'user_collections'")
    if cursor.fetchone():
        print("user_collections table already exists")
        cursor.close()
        connection.close()
        return True
    
    # Create user_collections table
    cursor.execute("""
        CREATE TABLE user_collections (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            collection_name VARCHAR(500) NOT NULL,
            document_name VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_collection (user_id, collection_name),
            INDEX idx_user_id (user_id),
            INDEX idx_collection_name (collection_name)
        )
    """)
    
    print("✅ user_collections table created successfully")
    connection.commit()
    cursor.close()
    connection.close()
    return True

def main():
    print("🔄 Starting user data separation migration...")
    
    if migrate_user_documents_table():
        print("✅ User documents table migration completed")
    else:
        print("❌ Failed to create user documents table")
        return
    
    if migrate_chat_history_table():
        print("✅ Chat history table migration completed")
    else:
        print("❌ Failed to create chat history table")
        return
    
    if migrate_user_collections_table():
        print("✅ User collections table migration completed")
    else:
        print("❌ Failed to create user collections table")
        return
    
    print("\n🎉 User data separation migration completed successfully!")
    print("\nNew tables created:")
    print("- user_documents: Tracks user-specific uploaded documents")
    print("- chat_history: Stores user conversation history")  
    print("- user_collections: Maps vector DB collections to users")

if __name__ == "__main__":
    main()