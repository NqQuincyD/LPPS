from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.locomotive import Locomotive
from app.models.user import User
from app.models.prediction import Prediction
from app.models.maintenance import MaintenanceRecord
from datetime import datetime, date
import json

locomotives_bp = Blueprint('locomotives', __name__)

@locomotives_bp.route('/')
@login_required
def index():
    """Locomotive management page"""
    locomotives = Locomotive.query.order_by(Locomotive.created_at.desc()).all()
    return render_template('locomotives/index.html', locomotives=locomotives)

@locomotives_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add new locomotive"""
    if request.method == 'POST':
        locomotive_id = request.form.get('locomotive_id')
        model = request.form.get('model')
        manufacturing_year = request.form.get('manufacturing_year')
        operating_hours = request.form.get('operating_hours')
        last_maintenance = request.form.get('last_maintenance')
        current_status = request.form.get('current_status')
        
        # Validate required fields
        if not all([locomotive_id, model, manufacturing_year]):
            flash('Please fill in all required fields', 'error')
            return render_template('locomotives/add.html')
        
        # Check if locomotive ID already exists
        if Locomotive.query.filter_by(locomotive_id=locomotive_id).first():
            flash('Locomotive ID already exists', 'error')
            return render_template('locomotives/add.html')
        
        try:
            # Convert and validate data
            manufacturing_year = int(manufacturing_year)
            operating_hours = int(operating_hours) if operating_hours else 0
            last_maintenance = datetime.strptime(last_maintenance, '%Y-%m-%d').date() if last_maintenance else None
            
            # Create new locomotive
            locomotive = Locomotive(
                locomotive_id=locomotive_id,
                model=model,
                manufacturing_year=manufacturing_year,
                operating_hours=operating_hours,
                last_maintenance=last_maintenance,
                current_status=current_status,
                created_by=current_user.id
            )
            
            db.session.add(locomotive)
            db.session.commit()
            
            flash('Locomotive added successfully!', 'success')
            return redirect(url_for('locomotives.index'))
            
        except ValueError:
            flash('Invalid data format. Please check your inputs.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the locomotive.', 'error')
    
    return render_template('locomotives/add.html')

@locomotives_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit locomotive"""
    locomotive = Locomotive.query.get_or_404(id)
    
    if request.method == 'POST':
        locomotive.locomotive_id = request.form.get('locomotive_id')
        locomotive.model = request.form.get('model')
        locomotive.manufacturing_year = int(request.form.get('manufacturing_year'))
        locomotive.operating_hours = int(request.form.get('operating_hours'))
        locomotive.current_status = request.form.get('current_status')
        
        last_maintenance = request.form.get('last_maintenance')
        locomotive.last_maintenance = datetime.strptime(last_maintenance, '%Y-%m-%d').date() if last_maintenance else None
        
        try:
            db.session.commit()
            flash('Locomotive updated successfully!', 'success')
            return redirect(url_for('locomotives.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the locomotive.', 'error')
    
    return render_template('locomotives/edit.html', locomotive=locomotive)

@locomotives_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete locomotive"""
    locomotive = Locomotive.query.get_or_404(id)
    
    try:
        db.session.delete(locomotive)
        db.session.commit()
        flash('Locomotive deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the locomotive.', 'error')
    
    return redirect(url_for('locomotives.index'))

@locomotives_bp.route('/view/<int:id>')
@login_required
def view(id):
    """View locomotive details"""
    locomotive = Locomotive.query.get_or_404(id)
    
    # Get locomotive's predictions
    predictions = locomotive.predictions.filter_by(is_active=True)\
        .order_by(Prediction.created_at.desc()).limit(5).all()
    
    # Get maintenance records
    maintenance_records = locomotive.maintenance_records\
        .order_by(MaintenanceRecord.start_date.desc()).limit(10).all()
    
    return render_template('locomotives/view.html', 
                         locomotive=locomotive,
                         predictions=predictions,
                         maintenance_records=maintenance_records)

@locomotives_bp.route('/api/locomotives')
@login_required
def api_locomotives():
    """API endpoint for locomotives data"""
    locomotives = Locomotive.query.all()
    data = []
    
    for locomotive in locomotives:
        data.append({
            'id': locomotive.id,
            'locomotive_id': locomotive.locomotive_id,
            'model': locomotive.model,
            'year': locomotive.manufacturing_year,
            'hours': locomotive.operating_hours,
            'status': locomotive.current_status,
            'status_display': locomotive.status_display,
            'status_color': locomotive.status_color,
            'age': locomotive.age,
            'risk_score': locomotive.calculate_risk_score(),
            'risk_level': locomotive.get_risk_level()
        })
    
    return jsonify(data)

@locomotives_bp.route('/api/locomotive/<int:id>')
@login_required
def api_locomotive(id):
    """API endpoint for single locomotive data"""
    locomotive = Locomotive.query.get_or_404(id)
    
    return jsonify({
        'id': locomotive.id,
        'locomotive_id': locomotive.locomotive_id,
        'model': locomotive.model,
        'manufacturing_year': locomotive.manufacturing_year,
        'operating_hours': locomotive.operating_hours,
        'current_status': locomotive.current_status,
        'last_maintenance': locomotive.last_maintenance.isoformat() if locomotive.last_maintenance else None,
        'age': locomotive.age,
        'risk_score': locomotive.calculate_risk_score(),
        'risk_level': locomotive.get_risk_level(),
        'recommendations': locomotive.get_maintenance_recommendations()
    })
