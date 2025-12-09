from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.train_movement import TrainMovement
from app import db
from datetime import datetime, timedelta
import json

data_collection_bp = Blueprint('data_collection', __name__)

@data_collection_bp.route('/')
@login_required
def index():
    """Data Collection Dashboard"""
    # Get current month and year
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Get monthly summary
    monthly_summary = TrainMovement.get_monthly_summary(current_year, current_month)
    
    # Get recent movements
    recent_movements = TrainMovement.query.order_by(
        TrainMovement.created_at.desc()
    ).limit(10).all()
    
    # Get statistics
    total_movements = TrainMovement.query.count()
    this_month_movements = TrainMovement.query.filter_by(
        graph_year=current_year, 
        graph_month=current_month
    ).count()
    
    return render_template('data_collection/index.html',
                         monthly_summary=monthly_summary,
                         recent_movements=recent_movements,
                         total_movements=total_movements,
                         this_month_movements=this_month_movements,
                         current_month=current_month,
                         current_year=current_year)

@data_collection_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_movement():
    """Add new train movement data"""
    if request.method == 'POST':
        try:
            # Parse form data
            movement = TrainMovement(
                train_number=request.form.get('train_number'),
                locomotive_number=request.form.get('locomotive_number'),
                departure_station=request.form.get('departure_station'),
                arrival_station=request.form.get('arrival_station'),
                departure_time=datetime.strptime(
                    f"{request.form.get('departure_date')} {request.form.get('departure_time')}", 
                    '%Y-%m-%d %H:%M'
                ),
                arrival_time=datetime.strptime(
                    f"{request.form.get('arrival_date')} {request.form.get('arrival_time')}", 
                    '%Y-%m-%d %H:%M'
                ),
                load_tons=float(request.form.get('load_tons', 0)),
                wagons_count=int(request.form.get('wagons_count', 0)),
                axles_count=int(request.form.get('axles_count', 0)),
                net_weight=float(request.form.get('net_weight', 0)),
                distance_km=float(request.form.get('distance_km', 0)),
                route_type=request.form.get('route_type'),
                service_type=request.form.get('service_type'),
                graph_month=int(request.form.get('graph_month')),
                graph_year=int(request.form.get('graph_year')),
                collected_by=current_user.get_full_name(),
                status=request.form.get('status', 'Active')
            )
            
            # Calculate metrics
            movement.calculate_metrics()
            
            # Save to database
            db.session.add(movement)
            db.session.commit()
            
            flash('Train movement data added successfully!', 'success')
            return redirect(url_for('data_collection.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding movement data: {str(e)}', 'error')
    
    # Get current month/year for default values
    now = datetime.now()
    return render_template('data_collection/add_movement.html',
                         current_month=now.month,
                         current_year=now.year)

@data_collection_bp.route('/bulk_upload', methods=['GET', 'POST'])
@login_required
def bulk_upload():
    """Bulk upload train movement data"""
    if request.method == 'POST':
        try:
            # Handle CSV file upload
            if 'csv_file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['csv_file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Process CSV file (simplified - you'd implement proper CSV parsing)
            flash('Bulk upload feature coming soon!', 'info')
            return redirect(url_for('data_collection.index'))
            
        except Exception as e:
            flash(f'Error processing bulk upload: {str(e)}', 'error')
    
    return render_template('data_collection/bulk_upload.html')

@data_collection_bp.route('/monthly/<int:year>/<int:month>')
@login_required
def monthly_data(year, month):
    """View monthly train movement data"""
    movements = TrainMovement.query.filter_by(
        graph_year=year, 
        graph_month=month
    ).order_by(TrainMovement.departure_time.desc()).all()
    
    monthly_summary = TrainMovement.get_monthly_summary(year, month)
    
    return render_template('data_collection/monthly_data.html',
                         movements=movements,
                         monthly_summary=monthly_summary,
                         year=year,
                         month=month)

@data_collection_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_movement(id):
    """Edit train movement data"""
    movement = TrainMovement.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update movement data
            movement.train_number = request.form.get('train_number')
            movement.locomotive_number = request.form.get('locomotive_number')
            movement.departure_station = request.form.get('departure_station')
            movement.arrival_station = request.form.get('arrival_station')
            movement.departure_time = datetime.strptime(
                f"{request.form.get('departure_date')} {request.form.get('departure_time')}", 
                '%Y-%m-%d %H:%M'
            )
            movement.arrival_time = datetime.strptime(
                f"{request.form.get('arrival_date')} {request.form.get('arrival_time')}", 
                '%Y-%m-%d %H:%M'
            )
            movement.load_tons = float(request.form.get('load_tons', 0))
            movement.wagons_count = int(request.form.get('wagons_count', 0))
            movement.axles_count = int(request.form.get('axles_count', 0))
            movement.net_weight = float(request.form.get('net_weight', 0))
            movement.distance_km = float(request.form.get('distance_km', 0))
            movement.route_type = request.form.get('route_type')
            movement.service_type = request.form.get('service_type')
            movement.status = request.form.get('status', 'Active')
            
            # Recalculate metrics
            movement.calculate_metrics()
            
            db.session.commit()
            flash('Train movement data updated successfully!', 'success')
            return redirect(url_for('data_collection.monthly_data', 
                                 year=movement.graph_year, 
                                 month=movement.graph_month))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating movement data: {str(e)}', 'error')
    
    return render_template('data_collection/edit_movement.html', movement=movement)

@data_collection_bp.route('/delete/<int:id>')
@login_required
def delete_movement(id):
    """Delete train movement data"""
    movement = TrainMovement.query.get_or_404(id)
    
    try:
        db.session.delete(movement)
        db.session.commit()
        flash('Train movement data deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting movement data: {str(e)}', 'error')
    
    return redirect(url_for('data_collection.monthly_data', 
                         year=movement.graph_year, 
                         month=movement.graph_month))

@data_collection_bp.route('/api/monthly_stats/<int:year>/<int:month>')
@login_required
def api_monthly_stats(year, month):
    """API endpoint for monthly statistics"""
    summary = TrainMovement.get_monthly_summary(year, month)
    return jsonify(summary or {})

@data_collection_bp.route('/api/movements')
@login_required
def api_movements():
    """API endpoint for train movements"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    movements = TrainMovement.query.order_by(
        TrainMovement.created_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'movements': [movement.to_dict() for movement in movements.items],
        'total': movements.total,
        'pages': movements.pages,
        'current_page': movements.page
    })
