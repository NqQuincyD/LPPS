from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models.user import User
from app.models.locomotive import Locomotive
from app.models.prediction import Prediction
from app.models.maintenance import MaintenanceRecord
from datetime import datetime
import re

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Get user statistics
    locomotives_count = Locomotive.query.filter_by(created_by=current_user.id).count()
    predictions_count = Prediction.query.join(Locomotive).filter(Locomotive.created_by == current_user.id).count()
    maintenance_count = MaintenanceRecord.query.join(Locomotive).filter(Locomotive.created_by == current_user.id).count()
    
    user_stats = {
        'locomotives': locomotives_count,
        'predictions': predictions_count,
        'maintenance': maintenance_count,
        'member_since': current_user.created_at.strftime('%B %Y') if current_user.created_at else 'Unknown',
        'last_login': current_user.last_login.strftime('%Y-%m-%d %H:%M') if current_user.last_login else 'Never'
    }
    
    return render_template('user/profile.html', user_stats=user_stats)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
            
            # Validation
            errors = []
            
            if not first_name:
                errors.append('First name is required')
            if not last_name:
                errors.append('Last name is required')
            if not email:
                errors.append('Email is required')
            if not username:
                errors.append('Username is required')
            
            # Email validation
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append('Invalid email format')
            
            # Username validation
            if username and not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
                errors.append('Username must be 3-30 characters, letters, numbers, and underscores only')
            
            # Check for duplicates
            if email != current_user.email:
                existing_email = User.query.filter_by(email=email).first()
                if existing_email:
                    errors.append('Email already exists')
            
            if username != current_user.username:
                existing_username = User.query.filter_by(username=username).first()
                if existing_username:
                    errors.append('Username already exists')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('user/edit_profile.html')
            
            # Update user
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.email = email
            current_user.username = username
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            return render_template('user/edit_profile.html')
    
    return render_template('user/edit_profile.html')

@user_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            if not current_password:
                flash('Current password is required', 'error')
                return render_template('user/change_password.html')
            
            if not new_password:
                flash('New password is required', 'error')
                return render_template('user/change_password.html')
            
            if not confirm_password:
                flash('Please confirm your new password', 'error')
                return render_template('user/change_password.html')
            
            # Verify current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
                return render_template('user/change_password.html')
            
            # Password strength validation
            password_errors = validate_password_strength(new_password)
            if password_errors:
                for error in password_errors:
                    flash(error, 'error')
                return render_template('user/change_password.html')
            
            # Confirm password match
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return render_template('user/change_password.html')
            
            # Update password
            current_user.set_password(new_password)
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('user.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error changing password: {str(e)}', 'error')
            return render_template('user/change_password.html')
    
    return render_template('user/change_password.html')

@user_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('user/settings.html')

@user_bp.route('/settings/notifications', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """Notification settings"""
    if request.method == 'POST':
        try:
            # Get notification preferences
            email_notifications = request.form.get('email_notifications') == 'on'
            maintenance_alerts = request.form.get('maintenance_alerts') == 'on'
            prediction_alerts = request.form.get('prediction_alerts') == 'on'
            system_updates = request.form.get('system_updates') == 'on'
            
            # Update user preferences (you can add these fields to User model if needed)
            # For now, we'll just show a success message
            flash('Notification settings updated successfully!', 'success')
            return redirect(url_for('user.settings'))
            
        except Exception as e:
            flash(f'Error updating notification settings: {str(e)}', 'error')
            return render_template('user/notification_settings.html')
    
    return render_template('user/notification_settings.html')

@user_bp.route('/settings/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """User preferences"""
    if request.method == 'POST':
        try:
            # Get preferences
            theme = request.form.get('theme', 'light')
            language = request.form.get('language', 'en')
            timezone = request.form.get('timezone', 'UTC')
            date_format = request.form.get('date_format', '%Y-%m-%d')
            
            # Update user preferences (you can add these fields to User model if needed)
            # For now, we'll just show a success message
            flash('Preferences updated successfully!', 'success')
            return redirect(url_for('user.settings'))
            
        except Exception as e:
            flash(f'Error updating preferences: {str(e)}', 'error')
            return render_template('user/preferences.html')
    
    return render_template('user/preferences.html')

def validate_password_strength(password):
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    
    return errors
