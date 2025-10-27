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

def create_tables():
    """Create database tables"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Drop tables in correct order (child tables first)
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS user_subscriptions")
    cursor.execute("DROP TABLE IF EXISTS user_ai_settings")
    cursor.execute("DROP TABLE IF EXISTS general_settings")
    cursor.execute("DROP TABLE IF EXISTS subscription_plans")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Users table
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            mobile_number VARCHAR(20) DEFAULT NULL,
            password VARCHAR(255) NOT NULL,
            profile_photo VARCHAR(255) DEFAULT NULL,
            role ENUM('user', 'admin') DEFAULT 'user',
            status ENUM('active', 'inactive') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Subscription plans table
    cursor.execute("""
        CREATE TABLE subscription_plans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            features TEXT,
            validity_days INT DEFAULT 30,
            status ENUM('active', 'inactive') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # User subscriptions table
    cursor.execute("""
        CREATE TABLE user_subscriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            plan_id INT NOT NULL,
            status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE CASCADE
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            plan_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            status ENUM('completed', 'pending', 'failed') DEFAULT 'pending',
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE CASCADE
        )
    """)
    
    # General settings table
    cursor.execute("""
        CREATE TABLE general_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            setting_key VARCHAR(255) UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type ENUM('text', 'number', 'boolean', 'email') DEFAULT 'text',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # AI operations settings table for users
    cursor.execute("""
        CREATE TABLE user_ai_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            openai_api_key VARCHAR(255),
            openai_model VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
            qdrant_url VARCHAR(255),
            qdrant_api_key VARCHAR(255),
            qdrant_collection VARCHAR(100),
            vector_dimension INT DEFAULT 384,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Contact us table
    cursor.execute("""
        CREATE TABLE contact_us (
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

def insert_sample_data():
    """Insert sample data"""
    connection = get_db_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    # Insert admin user
    cursor.execute("""
        INSERT IGNORE INTO users (name, email, password, role) 
        VALUES ('Admin User', 'admin@legaleagle.com', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'admin')
    """)
    
    # Insert sample users
    cursor.execute("""
        INSERT IGNORE INTO users (name, email, password) VALUES 
        ('John Doe', 'john@example.com', 'hashed_password'),
        ('Jane Smith', 'jane@example.com', 'hashed_password')
    """)
    
    # Insert subscription plans
    cursor.execute("""
        INSERT IGNORE INTO subscription_plans (name, price, features) VALUES 
        ('Solo Lawyer', 99.00, 'Basic AI assistance, 1K documents'),
        ('Law Firm', 79.00, 'Team collaboration, Unlimited documents'),
        ('Enterprise', 299.00, 'Custom AI, SSO, Priority support')
    """)
    
    # Insert default settings
    cursor.execute("""
        INSERT IGNORE INTO general_settings (setting_key, setting_value, setting_type, description) VALUES 
        ('site_name', 'LegalEagle', 'text', 'Website name'),
        ('site_email', 'admin@legaleagle.com', 'email', 'Contact email address'),
        ('maintenance_mode', 'false', 'boolean', 'Enable maintenance mode'),
        ('max_upload_size', '10', 'number', 'Maximum file upload size in MB'),
        ('support_phone', '+1-555-0123', 'text', 'Support phone number'),
        ('company_address', '123 Legal Street, Law City, LC 12345', 'text', 'Company address')
    """)
    
    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
    create_tables()
    insert_sample_data()
    print("Database setup completed!")