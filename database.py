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
    
    # Disable foreign key checks temporarily
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    # Drop tables in correct order (child tables first)
    cursor.execute("DROP TABLE IF EXISTS chat_history")
    cursor.execute("DROP TABLE IF EXISTS contact_us")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS user_subscriptions")
    cursor.execute("DROP TABLE IF EXISTS user_plans")
    cursor.execute("DROP TABLE IF EXISTS user_ai_settings")
    cursor.execute("DROP TABLE IF EXISTS general_settings")
    cursor.execute("DROP TABLE IF EXISTS subscription_plans")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Re-enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
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
            max_documents INT DEFAULT 10,
            max_chat_prompts INT DEFAULT 100,
            validity_days INT DEFAULT 30,
            status ENUM('active', 'inactive') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # User plans table
    cursor.execute("""
        CREATE TABLE user_plans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            plan_id INT NOT NULL,
            plan_name VARCHAR(255),
            plan_price DECIMAL(10,2) DEFAULT 0,
            plan_type ENUM('free', 'paid') DEFAULT 'free',
            max_documents INT DEFAULT 10,
            max_prompts INT DEFAULT 100,
            used_documents INT DEFAULT 0,
            used_prompts INT DEFAULT 0,
            status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE CASCADE
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
            payment_method VARCHAR(50) DEFAULT 'admin_assigned',
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
    
    # Chat history table
    cursor.execute("""
        CREATE TABLE chat_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            user_query TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            document_filter VARCHAR(255),
            response_time DECIMAL(5,3),
            session_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
        INSERT IGNORE INTO subscription_plans (name, price, features, max_documents, max_chat_prompts) VALUES 
        ('Free Plan', 0.00, 'Basic features, 5 documents, 50 chat prompts', 5, 50),
        ('Solo Lawyer', 99.00, 'Basic AI assistance, 1K documents', 1000, 5000),
        ('Law Firm', 79.00, 'Team collaboration, Unlimited documents', 999999, 999999),
        ('Enterprise', 299.00, 'Custom AI, SSO, Priority support', 999999, 999999)
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
    
    # Insert sample chat history
    cursor.execute("""
        INSERT IGNORE INTO chat_history (user_id, user_query, ai_response, document_filter, response_time, session_id) VALUES 
        (2, 'What are the key terms in this contract?', 'Based on the contract analysis, the key terms include: 1. Payment terms - Net 30 days, 2. Liability limitations - Capped at contract value, 3. Termination clause - 30 days notice required', 'Contract_Agreement.pdf', 2.45, 'sess_001'),
        (3, 'Explain the confidentiality clause', 'The confidentiality clause requires both parties to maintain strict confidentiality of proprietary information for a period of 5 years after contract termination. Violations may result in monetary damages.', 'NDA_Document.pdf', 1.89, 'sess_002'),
        (2, 'What are the payment obligations?', 'Payment obligations include: Monthly payments of $5,000 due by the 15th of each month, Late payment penalty of 1.5% per month, Accepted payment methods: Wire transfer or certified check', 'Service_Agreement.pdf', 3.12, 'sess_003'),
        (3, 'Are there any renewal terms?', 'Yes, the contract includes automatic renewal terms: Contract renews for 1-year periods unless either party provides 60 days written notice, Pricing may be adjusted annually based on CPI index', 'Contract_Agreement.pdf', 2.67, 'sess_004'),
        (2, 'What happens in case of breach?', 'In case of breach: 1. Written notice must be provided within 30 days, 2. Cure period of 15 days is allowed, 3. Damages may include actual losses plus attorney fees, 4. Injunctive relief may be sought for material breaches', 'Legal_Terms.pdf', 4.23, 'sess_005')
    """)
    
    # Insert sample user plans
    cursor.execute("""
        INSERT IGNORE INTO user_plans (user_id, plan_id, plan_name, plan_price, plan_type, max_documents, max_prompts, used_documents, used_prompts, status) VALUES 
        (2, 1, 'Solo Lawyer', 99.00, 'paid', 1000, 5000, 15, 45, 'active'),
        (3, 2, 'Law Firm', 79.00, 'paid', 999999, 999999, 8, 23, 'active')
    """)
    
    # Insert sample user subscriptions
    cursor.execute("""
        INSERT IGNORE INTO user_subscriptions (user_id, plan_id, status, start_date, end_date) VALUES 
        (2, 1, 'active', '2025-01-01', '2025-02-01'),
        (3, 2, 'active', '2025-01-15', '2025-02-15')
    """)
    
    # Insert sample transactions
    cursor.execute("""
        INSERT IGNORE INTO transactions (user_id, plan_id, amount, status, payment_method) VALUES 
        (2, 2, 99.00, 'completed', 'stripe'),
        (3, 3, 79.00, 'completed', 'paypal')
    """)
    
    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
    create_tables()
    insert_sample_data()
    print("Database setup completed!")