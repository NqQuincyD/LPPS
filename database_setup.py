#!/usr/bin/env python3
"""
Database setup script for NRZ Locomotive Performance Prediction System
This script creates the database and initializes tables with sample data
"""

import os
import sys
from datetime import datetime, date, timedelta
import random

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.locomotive import Locomotive
from app.models.prediction import Prediction
from app.models.maintenance import MaintenanceRecord
from app.models.train_movement import TrainMovement

def create_database():
    """Create database and all tables"""
    print("Creating database and tables...")
    
    # Create all tables
    db.create_all()
    print("Database tables created successfully")
    
    # Create indexes for better performance
    try:
        # Add indexes for frequently queried columns
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON lpps_users(username)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON lpps_users(email)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_locomotives_id ON lpps_locomotives(locomotive_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_locomotives_status ON lpps_locomotives(current_status)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_predictions_locomotive ON lpps_predictions(locomotive_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_predictions_active ON lpps_predictions(is_active)")
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Warning: Could not create indexes: {e}")

def create_admin_user():
    """Create admin user"""
    print("Creating admin user...")
    
    # Check if admin user already exists
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print("Admin user already exists")
        return admin_user
    
    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@nrz.co.zw',
        password='Admin123!',
        first_name='System',
        last_name='Administrator',
        role='admin'
    )
    
    db.session.add(admin_user)
    db.session.commit()
    print("Admin user created successfully")
    print("  Username: admin")
    print("  Password: Admin123!")
    print("  Email: admin@nrz.co.zw")
    
    return admin_user

def create_sample_users():
    """Create sample users"""
    print("Creating sample users...")
    
    sample_users = [
        {
            'username': 'engineer1',
            'email': 'engineer1@nrz.co.zw',
            'password': 'Engineer123!',
            'first_name': 'John',
            'last_name': 'Mukamuri',
            'role': 'engineer'
        },
        {
            'username': 'manager1',
            'email': 'manager1@nrz.co.zw',
            'password': 'Manager123!',
            'first_name': 'Sarah',
            'last_name': 'Chidziva',
            'role': 'manager'
        },
        {
            'username': 'technician1',
            'email': 'technician1@nrz.co.zw',
            'password': 'Tech123!',
            'first_name': 'Peter',
            'last_name': 'Moyo',
            'role': 'technician'
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        # Check if user already exists
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if existing_user:
            created_users.append(existing_user)
            continue
        
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            role=user_data['role']
        )
        
        db.session.add(user)
        created_users.append(user)
    
    db.session.commit()
    print(f"{len(created_users)} sample users created")
    return created_users

def create_sample_locomotives():
    """Create sample locomotives"""
    print("Creating sample locomotives...")
    
    # Get admin user for created_by field
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("❌ Admin user not found. Please create admin user first.")
        return []
    
    locomotive_data = [
        {
            'locomotive_id': 'NRZ-001',
            'model': 'DE10',
            'manufacturing_year': 1995,
            'operating_hours': 45000,
            'last_maintenance': date(2024, 1, 15),
            'current_status': 'active'
        },
        {
            'locomotive_id': 'NRZ-002',
            'model': 'DE6',
            'manufacturing_year': 1988,
            'operating_hours': 52000,
            'last_maintenance': date(2024, 1, 20),
            'current_status': 'maintenance'
        },
        {
            'locomotive_id': 'NRZ-003',
            'model': 'ES40DC',
            'manufacturing_year': 2005,
            'operating_hours': 32000,
            'last_maintenance': date(2024, 1, 10),
            'current_status': 'active'
        },
        {
            'locomotive_id': 'NRZ-004',
            'model': 'SD40-2',
            'manufacturing_year': 1992,
            'operating_hours': 48000,
            'last_maintenance': date(2024, 1, 25),
            'current_status': 'repair'
        },
        {
            'locomotive_id': 'NRZ-005',
            'model': 'DE10',
            'manufacturing_year': 1998,
            'operating_hours': 38000,
            'last_maintenance': date(2023, 12, 15),
            'current_status': 'active'
        },
        {
            'locomotive_id': 'NRZ-006',
            'model': 'ES40DC',
            'manufacturing_year': 2010,
            'operating_hours': 25000,
            'last_maintenance': date(2024, 2, 1),
            'current_status': 'active'
        },
        {
            'locomotive_id': 'NRZ-007',
            'model': 'DE6',
            'manufacturing_year': 1985,
            'operating_hours': 65000,
            'last_maintenance': date(2023, 11, 20),
            'current_status': 'maintenance'
        },
        {
            'locomotive_id': 'NRZ-008',
            'model': 'SD40-2',
            'manufacturing_year': 1990,
            'operating_hours': 55000,
            'last_maintenance': date(2023, 10, 5),
            'current_status': 'retired'
        }
    ]
    
    created_locomotives = []
    for loco_data in locomotive_data:
        # Check if locomotive already exists
        existing_loco = Locomotive.query.filter_by(locomotive_id=loco_data['locomotive_id']).first()
        if existing_loco:
            created_locomotives.append(existing_loco)
            continue
        
        locomotive = Locomotive(
            locomotive_id=loco_data['locomotive_id'],
            model=loco_data['model'],
            manufacturing_year=loco_data['manufacturing_year'],
            operating_hours=loco_data['operating_hours'],
            last_maintenance=loco_data['last_maintenance'],
            current_status=loco_data['current_status'],
            created_by=admin_user.id
        )
        
        db.session.add(locomotive)
        created_locomotives.append(locomotive)
    
    db.session.commit()
    print(f"{len(created_locomotives)} sample locomotives created")
    return created_locomotives

def create_sample_predictions():
    """Create sample predictions"""
    print("Creating sample predictions...")
    
    locomotives = Locomotive.query.all()
    if not locomotives:
        print("❌ No locomotives found. Please create locomotives first.")
        return []
    
    created_predictions = []
    for locomotive in locomotives[:5]:  # Create predictions for first 5 locomotives
        # Check if prediction already exists
        existing_prediction = Prediction.query.filter_by(
            locomotive_id=locomotive.id,
            is_active=True
        ).first()
        if existing_prediction:
            created_predictions.append(existing_prediction)
            continue
        
        # Generate prediction data
        risk_score = locomotive.calculate_risk_score()
        risk_level = locomotive.get_risk_level()
        
        prediction_data = Prediction.generate_prediction_data(locomotive, 30)
        recommendations = Prediction.generate_recommendations(locomotive)
        
        prediction = Prediction(
            locomotive_id=locomotive.id,
            prediction_type='failure',
            prediction_period=30,
            risk_score=risk_score,
            risk_level=risk_level,
            prediction_data=prediction_data,
            recommendations=recommendations
        )
        
        db.session.add(prediction)
        created_predictions.append(prediction)
    
    db.session.commit()
    print(f"{len(created_predictions)} sample predictions created")
    return created_predictions

def create_sample_maintenance_records():
    """Create sample maintenance records"""
    print("Creating sample maintenance records...")
    
    locomotives = Locomotive.query.all()
    admin_user = User.query.filter_by(username='admin').first()
    
    if not locomotives or not admin_user:
        print("❌ No locomotives or admin user found.")
        return []
    
    maintenance_types = ['routine', 'repair', 'overhaul']
    performed_by_options = ['John Mukamuri', 'Sarah Chidziva', 'Peter Moyo', 'Maintenance Team A', 'Maintenance Team B']
    
    created_records = []
    for locomotive in locomotives[:4]:  # Create records for first 4 locomotives
        # Create 2-3 maintenance records per locomotive
        num_records = random.randint(2, 3)
        
        for i in range(num_records):
            start_date = date.today() - timedelta(days=random.randint(30, 365))
            end_date = start_date + timedelta(days=random.randint(1, 14)) if random.choice([True, False]) else None
            
            maintenance_record = MaintenanceRecord(
                locomotive_id=locomotive.id,
                maintenance_type=random.choice(maintenance_types),
                description=f"{random.choice(maintenance_types).title()} maintenance for {locomotive.locomotive_id}",
                performed_by=random.choice(performed_by_options),
                start_date=start_date,
                end_date=end_date,
                cost=random.uniform(500, 5000),
                parts_replaced=random.choice([
                    'Engine oil filter, Air filter',
                    'Brake pads, Brake fluid',
                    'Transmission fluid, Gasket',
                    'Spark plugs, Ignition coil'
                ]),
                notes=f"Maintenance performed on {locomotive.locomotive_id}",
                created_by=admin_user.id
            )
            
            db.session.add(maintenance_record)
            created_records.append(maintenance_record)
    
    db.session.commit()
    print(f"{len(created_records)} sample maintenance records created")
    return created_records

def print_setup_summary():
    """Print setup summary"""
    print("\n" + "="*60)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    # Count records
    user_count = User.query.count()
    locomotive_count = Locomotive.query.count()
    prediction_count = Prediction.query.count()
    maintenance_count = MaintenanceRecord.query.count()
    
    print(f"Database Statistics:")
    print(f"   - Users: {user_count}")
    print(f"   - Locomotives: {locomotive_count}")
    print(f"   - Predictions: {prediction_count}")
    print(f"   - Maintenance Records: {maintenance_count}")
    
    print(f"\nDefault Login Credentials:")
    print(f"   - Admin: admin / Admin123!")
    print(f"   - Engineer: engineer1 / Engineer123!")
    print(f"   - Manager: manager1 / Manager123!")
    print(f"   - Technician: technician1 / Tech123!")
    
    print(f"\nNext Steps:")
    print(f"   1. Run the application: python run.py")
    print(f"   2. Open browser: http://localhost:5000")
    print(f"   3. Login with admin credentials")
    print(f"   4. Start using the system!")
    
    print("="*60)

def main():
    """Main setup function"""
    print("NRZ Locomotive Performance Prediction System")
    print("Database Setup Script")
    print("="*60)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Create database and tables
            create_database()
            
            # Create admin user
            create_admin_user()
            
            # Create sample data
            create_sample_users()
            create_sample_locomotives()
            create_sample_predictions()
            create_sample_maintenance_records()
            
            # Print summary
            print_setup_summary()
            
        except Exception as e:
            print(f"Error during setup: {e}")
            print("Please check your database connection and try again.")
            sys.exit(1)

if __name__ == '__main__':
    main()
