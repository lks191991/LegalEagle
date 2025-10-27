#!/usr/bin/env python3
"""
Migrate contact_us table to use single name field instead of first_name and last_name
"""

from database import get_db_connection

def migrate_contact_table():
    """Migrate contact_us table to use single name field"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return False
    
    cursor = connection.cursor()
    
    try:
        # Add new name column
        print("Adding 'name' column...")
        cursor.execute("""
            ALTER TABLE contact_us 
            ADD COLUMN name VARCHAR(200) AFTER id
        """)
        
        # Copy data from first_name and last_name to name
        print("Migrating existing data...")
        cursor.execute("""
            UPDATE contact_us 
            SET name = CONCAT(first_name, ' ', last_name)
            WHERE first_name IS NOT NULL AND last_name IS NOT NULL
        """)
        
        # Make name column NOT NULL
        print("Making 'name' column NOT NULL...")
        cursor.execute("""
            ALTER TABLE contact_us 
            MODIFY COLUMN name VARCHAR(200) NOT NULL
        """)
        
        # Drop old columns
        print("Dropping old columns...")
        cursor.execute("""
            ALTER TABLE contact_us 
            DROP COLUMN first_name,
            DROP COLUMN last_name
        """)
        
        connection.commit()
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        connection.rollback()
        return False
        
    finally:
        cursor.close()
        connection.close()

def rollback_migration():
    """Rollback the migration (for testing purposes)"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database")
        return False
    
    cursor = connection.cursor()
    
    try:
        # Add back first_name and last_name columns
        print("Adding back first_name and last_name columns...")
        cursor.execute("""
            ALTER TABLE contact_us 
            ADD COLUMN first_name VARCHAR(100) AFTER id,
            ADD COLUMN last_name VARCHAR(100) AFTER first_name
        """)
        
        # Split name into first_name and last_name
        print("Splitting name data...")
        cursor.execute("""
            UPDATE contact_us 
            SET first_name = SUBSTRING_INDEX(name, ' ', 1),
                last_name = CASE 
                    WHEN LOCATE(' ', name) > 0 
                    THEN SUBSTRING(name, LOCATE(' ', name) + 1)
                    ELSE ''
                END
            WHERE name IS NOT NULL
        """)
        
        # Make columns NOT NULL
        cursor.execute("""
            ALTER TABLE contact_us 
            MODIFY COLUMN first_name VARCHAR(100) NOT NULL,
            MODIFY COLUMN last_name VARCHAR(100) NOT NULL
        """)
        
        # Drop name column
        print("Dropping name column...")
        cursor.execute("""
            ALTER TABLE contact_us 
            DROP COLUMN name
        """)
        
        connection.commit()
        print("Rollback completed successfully!")
        return True
        
    except Exception as e:
        print(f"Rollback failed: {e}")
        connection.rollback()
        return False
        
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        if rollback_migration():
            print("Database rollback completed!")
        else:
            print("Database rollback failed!")
    else:
        if migrate_contact_table():
            print("Database migration completed!")
        else:
            print("Database migration failed!")