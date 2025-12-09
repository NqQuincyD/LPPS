from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.user import User
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        if not username_or_email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact administrator.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=bool(remember))
            user.last_login = db.func.now()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username/email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validate all fields are provided
        if not all([username, email, password, confirm_password, first_name, last_name]):
            flash('Please fill in all fields', 'error')
            return render_template('auth/register.html')
        
        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        # Validate username
        is_valid_username, username_message = User.validate_username(username)
        if not is_valid_username:
            flash(username_message, 'error')
            return render_template('auth/register.html')
        
        # Validate email
        is_valid_email, email_message = User.validate_email(email)
        if not is_valid_email:
            flash(email_message, 'error')
            return render_template('auth/register.html')
        
        # Validate password strength
        is_valid_password, password_message = User.validate_password_strength(password)
        if not is_valid_password:
            flash(password_message, 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/check_username')
def check_username():
    """AJAX endpoint to check username availability"""
    username = request.args.get('username')
    if not username:
        return jsonify({'valid': False, 'message': 'Username is required'})
    
    is_valid, message = User.validate_username(username)
    return jsonify({'valid': is_valid, 'message': message})

@auth_bp.route('/check_email')
def check_email():
    """AJAX endpoint to check email availability"""
    email = request.args.get('email')
    if not email:
        return jsonify({'valid': False, 'message': 'Email is required'})
    
    is_valid, message = User.validate_email(email)
    return jsonify({'valid': is_valid, 'message': message})

@auth_bp.route('/check_password_strength')
def check_password_strength():
    """AJAX endpoint to check password strength"""
    password = request.args.get('password')
    if not password:
        return jsonify({'level': 'weak', 'score': 0, 'message': 'Password is required'})
    
    level, score = User.get_password_strength_level(password)
    return jsonify({'level': level, 'score': score})
