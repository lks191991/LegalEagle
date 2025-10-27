#!/usr/bin/env python3

import mysql.connector
import sys
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'legaleagle'
}

def create_faq_table():
    """Create FAQ table in the database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create FAQs table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS faqs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category VARCHAR(100) DEFAULT 'General',
            is_active BOOLEAN DEFAULT TRUE,
            sort_order INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by INT DEFAULT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_query)
        print("✅ FAQ table created successfully!")
        
        # Insert sample FAQs
        sample_faqs = [
            ("What is LegalEagle?", "LegalEagle is an AI-powered legal document analysis platform that helps you understand and analyze legal documents quickly and efficiently.", "General", True, 1),
            ("How do I upload a document?", "Simply go to the Upload section in your dashboard, select your PDF file, and click upload. Our AI will analyze it within minutes.", "Usage", True, 2),
            ("What file formats are supported?", "Currently, we support PDF files up to 10MB in size. We're working on adding support for more formats.", "Technical", True, 3),
            ("Is my data secure?", "Yes, we use enterprise-grade encryption and security measures to protect your documents and personal information.", "Security", True, 4),
            ("How much does it cost?", "We offer various subscription plans starting from basic free tier to premium plans. Check our pricing page for details.", "Pricing", True, 5),
            ("Can I cancel my subscription anytime?", "Yes, you can cancel your subscription at any time from your account settings. No questions asked.", "Billing", True, 6),
            ("How accurate is the AI analysis?", "Our AI model has been trained on thousands of legal documents and provides 95%+ accuracy in most cases.", "AI & Technology", True, 7),
            ("Do you offer customer support?", "Yes, we provide 24/7 customer support via email and live chat for all our premium users.", "Support", True, 8)
        ]
        
        insert_query = """
        INSERT INTO faqs (question, answer, category, is_active, sort_order) 
        VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.executemany(insert_query, sample_faqs)
        print(f"✅ Inserted {len(sample_faqs)} sample FAQs!")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 FAQ system setup completed successfully!")
        print("📋 Sample FAQs have been added to get you started.")
        print("🔧 Admin can now manage FAQs through the admin panel.")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_faq_table()