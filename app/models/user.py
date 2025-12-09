from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db, bcrypt
import re
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    locomotives = db.relationship('Locomotive', backref='created_by_user', lazy='dynamic')
    
    def __init__(self, username, email, password, first_name, last_name, role='user'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_username(username):
        """Validate username format and uniqueness"""
        if not username:
            return False, "Username is required"
        
        if len(username) < 3 or len(username) > 30:
            return False, "Username must be between 3 and 30 characters"
        
        # Check for valid characters (letters, numbers, underscores only)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return False, "Username already taken"
        
        return True, "Username is valid"
    
    @staticmethod
    def validate_email(email):
        """Validate email format and uniqueness"""
        if not email:
            return False, "Email is required"
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return False, "Email already registered"
        
        return True, "Email is valid"
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        # Check for uppercase letters
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for lowercase letters
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for numbers
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    @staticmethod
    def get_password_strength_level(password):
        """Get password strength level for real-time feedback"""
        if not password:
            return "weak", 0
        
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("At least 8 characters")
        
        # Uppercase check
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Uppercase letter")
        
        # Lowercase check
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Lowercase letter")
        
        # Number check
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Number")
        
        # Special character check
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Special character")
        
        if score <= 2:
            return "weak", score
        elif score <= 4:
            return "moderate", score
        else:
            return "strong", score
    
    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'
