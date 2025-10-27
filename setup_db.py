#!/usr/bin/env python3
"""
Database setup script for LegalEagle
Run this script to create database and tables
"""

from database import create_tables, insert_sample_data

def main():
    print("Setting up LegalEagle database...")
    
    # Create tables
    if create_tables():
        print("Database tables created successfully")
    else:
        print("Failed to create database tables")
        return
    
    # Insert sample data
    insert_sample_data()
    print("Sample data inserted successfully")
    
    print("\nDatabase setup completed!")
    print("\nDefault admin login:")
    print("Email: admin@legaleagle.com")
    print("Password: password")

if __name__ == "__main__":
    main()