#!/usr/bin/env python3
"""
Database Reset Script for NRZ Locomotive Performance Prediction System
This script completely empties the database by dropping all tables
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def drop_all_tables():
    """Drop all database tables"""
    print("Dropping all database tables...")
    
    try:
        # Drop all tables
        db.drop_all()
        print("✅ All tables dropped successfully")
        return True
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False

def verify_empty_database():
    """Verify that the database is completely empty"""
    print("Verifying database is empty...")
    
    try:
        # Check if any tables exist by trying to query system tables
        result = db.engine.execute("SHOW TABLES")
        tables = [row[0] for row in result]
        
        if not tables:
            print("✅ Database is completely empty - no tables found")
            return True
        else:
            print(f"⚠️  Warning: {len(tables)} tables still exist: {', '.join(tables)}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False

def print_reset_summary():
    """Print reset summary"""
    print("\n" + "="*60)
    print("DATABASE RESET COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("✅ All database tables have been dropped")
    print("✅ Database is now completely empty")
    print("✅ No data or tables remain in the database")
    
    print(f"\nNext Steps:")
    print(f"   1. Run database_setup.py to create tables and sample data")
    print(f"   2. Or run the application: python run.py")
    print(f"   3. The application will create tables on first run")
    
    print("="*60)

def main():
    """Main reset function"""
    print("NRZ Locomotive Performance Prediction System")
    print("Database Complete Reset Script")
    print("="*60)
    print("⚠️  WARNING: This will completely empty the database!")
    print("⚠️  All tables and data will be permanently deleted!")
    print("="*60)
    
    # Ask for confirmation
    confirm = input("Are you sure you want to proceed? Type 'YES' to continue: ")
    if confirm != 'YES':
        print("❌ Operation cancelled by user")
        sys.exit(0)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all tables
            if not drop_all_tables():
                print("❌ Failed to drop tables. Exiting.")
                sys.exit(1)
            
            # Verify database is empty
            verify_empty_database()
            
            # Print summary
            print_reset_summary()
            
        except Exception as e:
            print(f"❌ Error during reset: {e}")
            print("Please check your database connection and try again.")
            sys.exit(1)

if __name__ == '__main__':
    main()
