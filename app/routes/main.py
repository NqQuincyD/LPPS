from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.models.locomotive import Locomotive
from app.models.prediction import Prediction
from app.models.maintenance import MaintenanceRecord
from datetime import datetime, timedelta
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with key metrics and charts"""
    # Get fleet statistics
    fleet_stats = Locomotive.get_fleet_statistics()
    
    # Get recent predictions
    recent_predictions = Prediction.query.filter_by(is_active=True)\
        .order_by(Prediction.created_at.desc())\
        .limit(5).all()
    
    # Get top performing locomotives (highest reliability)
    top_performers = Locomotive.query.order_by(Locomotive.manufacturing_year.desc())\
        .limit(5).all()
    
    # Get performance trends data for charts
    performance_data = get_performance_trends()
    fleet_type_distribution = get_fleet_type_distribution()
    
    return render_template('main/dashboard.html',
                         fleet_stats=fleet_stats,
                         recent_predictions=recent_predictions,
                         top_performers=top_performers,
                         performance_data=performance_data,
                         fleet_type_distribution=fleet_type_distribution)

@main_bp.route('/api/dashboard_metrics')
@login_required
def dashboard_metrics():
    """API endpoint for dashboard metrics"""
    fleet_stats = Locomotive.get_fleet_statistics()
    
    # Calculate total fleet
    total_fleet = Locomotive.query.count()
    
    # Calculate average reliability
    locomotives = Locomotive.query.all()
    avg_reliability = round(sum(loco.calculate_reliability() for loco in locomotives) / len(locomotives), 1) if locomotives else 0
    
    # Calculate high risk locomotives
    high_risk_count = sum(1 for loco in locomotives if loco.get_risk_level() == 'High')
    
    # Calculate total predictions
    total_predictions = Prediction.query.filter_by(is_active=True).count()
    
    return jsonify({
        'total_fleet': total_fleet,
        'avg_reliability': avg_reliability,
        'high_risk_count': high_risk_count,
        'total_predictions': total_predictions
    })

@main_bp.route('/api/performance_chart')
@login_required
def performance_chart():
    """API endpoint for performance trends chart"""
    data = get_performance_trends()
    return jsonify(data)

@main_bp.route('/api/fleet_type_chart')
@login_required
def fleet_type_chart():
    """API endpoint for fleet type distribution chart"""
    data = get_fleet_type_distribution()
    return jsonify(data)

def get_performance_trends():
    """Get performance trends data for charts"""
    # Get real data from locomotives
    locomotives = Locomotive.query.all()
    
    # Calculate reliability distribution
    high_reliability = sum(1 for loco in locomotives if loco.calculate_reliability() >= 80)
    medium_reliability = sum(1 for loco in locomotives if 60 <= loco.calculate_reliability() < 80)
    low_reliability = sum(1 for loco in locomotives if loco.calculate_reliability() < 60)
    
    return {
        'labels': ['High Reliability (≥80%)', 'Medium Reliability (60-79%)', 'Low Reliability (<60%)'],
        'datasets': [{
            'label': 'Number of Locomotives',
            'data': [high_reliability, medium_reliability, low_reliability],
            'backgroundColor': ['#10B981', '#F59E0B', '#EF4444'],
            'borderColor': ['#059669', '#D97706', '#DC2626'],
            'borderWidth': 2
        }]
    }

def get_fleet_type_distribution():
    """Get fleet type distribution for charts"""
    # Count locomotives by model
    de10_count = Locomotive.query.filter_by(model='DE10').count()
    de11_count = Locomotive.query.filter_by(model='DE11').count()
    
    return {
        'labels': ['NRZ Fleet (DE10)', 'Hired Fleet (DE11)'],
        'datasets': [{
            'data': [de10_count, de11_count],
            'backgroundColor': ['#3B82F6', '#06B6D4'],
            'borderColor': ['#2563EB', '#0891B2'],
            'borderWidth': 2
        }]
    }
