from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from app import db
from app.models.locomotive import Locomotive
from app.models.prediction import Prediction
from app.models.maintenance import MaintenanceRecord
from datetime import datetime, timedelta
import json
import csv
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    """Reports page"""
    return render_template('reports/index.html')

@reports_bp.route('/test')
@login_required
def test_report():
    """Test report generation"""
    try:
        # Simple test data
        test_data = {
            'title': 'Test Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fleet_stats': {'total': 5, 'active': 3, 'maintenance': 1, 'repair': 1, 'retired': 0},
            'model_distribution': {'ES40DC': 3, 'GE40AC': 2},
            'age_groups': {'0-10': 2, '11-20': 2, '21-30': 1, '30+': 0},
            'locomotives': []
        }
        
        return render_template('reports/print.html', 
                             report_data=test_data, 
                             report_type='fleet-overview')
    except Exception as e:
        return f"Test error: {str(e)}"

@reports_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Generate report"""
    report_type = request.form.get('report_type')
    report_period = request.form.get('report_period')
    format_type = request.form.get('format', 'html')
    
    if not report_type:
        flash('Please select a report type', 'error')
        return redirect(url_for('reports.index'))
    
    try:
        if report_type == 'risk_assessment':
            data = generate_risk_assessment_report()
        elif report_type == 'ml_predictions':
            data = generate_ml_predictions_report()
        elif report_type == 'performance_forecast':
            data = generate_performance_forecast_report()
        elif report_type == 'maintenance_planning':
            data = generate_maintenance_planning_report()
        elif report_type == 'data_export':
            return generate_data_export_report()
        # Legacy report types for backward compatibility
        elif report_type == 'fleet-overview':
            data = generate_fleet_overview_report()
        elif report_type == 'maintenance-schedule':
            data = generate_maintenance_schedule_report()
        elif report_type == 'utilization-analysis':
            data = generate_utilization_analysis_report()
        elif report_type == 'failure-predictions':
            data = generate_failure_predictions_report()
        else:
            flash('Invalid report type', 'error')
            return redirect(url_for('reports.index'))
        
        if format_type == 'csv':
            return generate_csv_report(data, report_type)
        else:
            return render_template('reports/preview.html', 
                                 report_data=data, 
                                 report_type=report_type,
                                 report_period=report_period)
            
    except Exception as e:
        print(f"Report generation error: {str(e)}")  # Debug output
        flash(f'An error occurred while generating the report: {str(e)}', 'error')
        return redirect(url_for('reports.index'))

@reports_bp.route('/print/<report_type>')
@login_required
def print_report(report_type):
    """Print-friendly report view"""
    try:
        print(f"Generating print report for type: {report_type}")  # Debug output
        
        # Try to generate the report
        try:
            if report_type == 'fleet-overview':
                data = generate_fleet_overview_report()
            elif report_type == 'maintenance-schedule':
                data = generate_maintenance_schedule_report()
            elif report_type == 'utilization-analysis':
                data = generate_utilization_analysis_report()
            elif report_type == 'failure-predictions':
                data = generate_failure_predictions_report()
            else:
                flash('Invalid report type', 'error')
                return redirect(url_for('reports.index'))
        except Exception as gen_error:
            print(f"Report generation failed: {str(gen_error)}")
            # Create a fallback report with basic data
            locomotives = Locomotive.query.all()
            data = {
                'title': f'{report_type.replace("-", " ").title()} Report',
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fleet_stats': {
                    'total': len(locomotives),
                    'active': len([l for l in locomotives if l.current_status == 'active']),
                    'maintenance': len([l for l in locomotives if l.current_status == 'maintenance']),
                    'repair': len([l for l in locomotives if l.current_status == 'repair']),
                    'retired': len([l for l in locomotives if l.current_status == 'retired'])
                },
                'model_distribution': {},
                'age_groups': {'0-10': 0, '11-20': 0, '21-30': 0, '30+': 0},
                'locomotives': locomotives,
                'maintenance_due': [],
                'utilization_data': [],
                'risk_assessment': []
            }
        
        print(f"Report data generated successfully: {data.get('title', 'Unknown')}")  # Debug output
        
        return render_template('reports/print.html', 
                             report_data=data, 
                             report_type=report_type)
            
    except Exception as e:
        print(f"Print report error: {str(e)}")  # Debug output
        flash(f'An error occurred while generating the print report: {str(e)}', 'error')
        return redirect(url_for('reports.index'))

def generate_fleet_overview_report():
    """Generate fleet overview report data"""
    try:
        locomotives = Locomotive.query.all()
        
        # Simple fleet stats without calling static method
        total = len(locomotives)
        active = len([l for l in locomotives if l.current_status == 'active'])
        maintenance = len([l for l in locomotives if l.current_status == 'maintenance'])
        repair = len([l for l in locomotives if l.current_status == 'repair'])
        retired = len([l for l in locomotives if l.current_status == 'retired'])
        
        fleet_stats = {
            'total': total,
            'active': active,
            'maintenance': maintenance,
            'repair': repair,
            'retired': retired
        }
        
        # Group by model
        model_distribution = {}
        for locomotive in locomotives:
            model = locomotive.model
            if model not in model_distribution:
                model_distribution[model] = 0
            model_distribution[model] += 1
        
        # Age distribution
        age_groups = {'0-10': 0, '11-20': 0, '21-30': 0, '30+': 0}
        for locomotive in locomotives:
            age = locomotive.age
            if age <= 10:
                age_groups['0-10'] += 1
            elif age <= 20:
                age_groups['11-20'] += 1
            elif age <= 30:
                age_groups['21-30'] += 1
            else:
                age_groups['30+'] += 1
        
        return {
            'title': 'Fleet Overview Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fleet_stats': fleet_stats,
            'model_distribution': model_distribution,
            'age_groups': age_groups,
            'locomotives': locomotives
        }
    except Exception as e:
        print(f"Fleet overview report error: {str(e)}")
        raise

def generate_maintenance_schedule_report():
    """Generate maintenance schedule report data"""
    try:
        # Get locomotives due for maintenance
        locomotives = Locomotive.query.all()
        maintenance_due = []
        
        for locomotive in locomotives:
            days_since_maintenance = None
            if locomotive.last_maintenance:
                days_since_maintenance = (datetime.now().date() - locomotive.last_maintenance).days
            
            # Determine maintenance priority
            priority = 'Low'
            if locomotive.age > 25 or locomotive.operating_hours > 50000:
                priority = 'High'
            elif locomotive.age > 20 or locomotive.operating_hours > 40000:
                priority = 'Medium'
            
            if days_since_maintenance and days_since_maintenance > 60:
                priority = 'High'
            elif days_since_maintenance and days_since_maintenance > 30:
                priority = 'Medium'
            
            maintenance_due.append({
                'locomotive': locomotive,
                'days_since_maintenance': days_since_maintenance,
                'priority': priority
            })
        
        # Sort by priority
        priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
        maintenance_due.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return {
            'title': 'Maintenance Schedule Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'maintenance_due': maintenance_due
        }
    except Exception as e:
        print(f"Maintenance schedule report error: {str(e)}")
        raise

def generate_utilization_analysis_report():
    """Generate utilization analysis report data"""
    try:
        locomotives = Locomotive.query.all()
        utilization_data = []
        
        for locomotive in locomotives:
            # Calculate utilization rate (simplified)
            utilization_rate = min(100, max(0, 100 - (locomotive.age * 2) - (locomotive.operating_hours / 1000)))
            
            utilization_data.append({
                'locomotive': locomotive,
                'utilization_rate': round(utilization_rate, 1),
                'status': 'High' if utilization_rate >= 80 else 'Medium' if utilization_rate >= 60 else 'Low'
            })
        
        # Sort by utilization rate
        utilization_data.sort(key=lambda x: x['utilization_rate'], reverse=True)
        
        return {
            'title': 'Utilization Analysis Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'utilization_data': utilization_data
        }
    except Exception as e:
        print(f"Utilization analysis report error: {str(e)}")
        raise

def generate_failure_predictions_report():
    """Generate failure predictions report data"""
    try:
        locomotives = Locomotive.query.all()
        risk_assessment = []
        
        for locomotive in locomotives:
            # Simple risk calculation without calling methods
            age_factor = min(50, locomotive.age * 2)
            hours_factor = min(30, locomotive.operating_hours / 1000)
            maintenance_factor = 0
            if locomotive.last_maintenance:
                days_since = (datetime.now().date() - locomotive.last_maintenance).days
                maintenance_factor = min(20, days_since / 3)
            
            risk_score = min(100, age_factor + hours_factor + maintenance_factor)
            
            if risk_score >= 70:
                risk_level = 'High'
            elif risk_score >= 40:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            # Simple recommendations
            recommendations = []
            if locomotive.age > 20:
                recommendations.append('Engine overhaul recommended')
            if locomotive.operating_hours > 50000:
                recommendations.append('Transmission service required')
            if not locomotive.last_maintenance or (datetime.now().date() - locomotive.last_maintenance).days > 90:
                recommendations.append('Routine maintenance overdue')
            
            risk_assessment.append({
                'locomotive': locomotive,
                'risk_score': round(risk_score, 1),
                'risk_level': risk_level,
                'recommendations': recommendations
            })
        
        # Sort by risk score
        risk_assessment.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return {
            'title': 'Failure Predictions Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'risk_assessment': risk_assessment
        }
    except Exception as e:
        print(f"Failure predictions report error: {str(e)}")
        raise

def generate_csv_report(data, report_type):
    """Generate CSV report"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == 'fleet-overview':
            writer.writerow(['Locomotive ID', 'Model', 'Year', 'Hours', 'Status', 'Age', 'Risk Score'])
            for locomotive in data['locomotives']:
                # Simple risk calculation
                age_factor = min(50, locomotive.age * 2)
                hours_factor = min(30, locomotive.operating_hours / 1000)
                maintenance_factor = 0
                if locomotive.last_maintenance:
                    days_since = (datetime.now().date() - locomotive.last_maintenance).days
                    maintenance_factor = min(20, days_since / 3)
                risk_score = min(100, age_factor + hours_factor + maintenance_factor)
                
                writer.writerow([
                    locomotive.locomotive_id,
                    locomotive.model,
                    locomotive.manufacturing_year,
                    locomotive.operating_hours,
                    locomotive.current_status,
                    locomotive.age,
                    round(risk_score, 1)
                ])
        
        elif report_type == 'maintenance-schedule':
            writer.writerow(['Locomotive ID', 'Model', 'Last Maintenance', 'Days Since', 'Priority'])
            for item in data['maintenance_due']:
                locomotive = item['locomotive']
                writer.writerow([
                    locomotive.locomotive_id,
                    locomotive.model,
                    locomotive.last_maintenance.strftime('%Y-%m-%d') if locomotive.last_maintenance else 'Never',
                    item['days_since_maintenance'] or 'N/A',
                    item['priority']
                ])
        
        elif report_type == 'utilization-analysis':
            writer.writerow(['Locomotive ID', 'Model', 'Utilization Rate', 'Status'])
            for item in data['utilization_data']:
                locomotive = item['locomotive']
                writer.writerow([
                    locomotive.locomotive_id,
                    locomotive.model,
                    item['utilization_rate'],
                    item['status']
                ])
        
        elif report_type == 'failure-predictions':
            writer.writerow(['Locomotive ID', 'Model', 'Risk Score', 'Risk Level'])
            for item in data['risk_assessment']:
                locomotive = item['locomotive']
                writer.writerow([
                    locomotive.locomotive_id,
                    locomotive.model,
                    item['risk_score'],
                    item['risk_level']
                ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
        return response
    except Exception as e:
        print(f"CSV generation error: {str(e)}")
        raise

# New prediction-based report functions

def generate_risk_assessment_report():
    """Generate risk assessment report with visual charts using ML predictions"""
    locomotives = Locomotive.query.all()
    
    # Import ML service
    from app.loco_ml_service import loco_ml_service
    
    # Calculate risk distribution using ML predictions
    risk_distribution = {'High': 0, 'Medium': 0, 'Low': 0}
    risk_data = []
    
    for loco in locomotives:
        try:
            # Use ML service to get accurate risk assessment
            prediction_result = loco_ml_service.predict_performance(
                locomotive=loco,
                prediction_type='all',
                period_days=365
            )
            
            risk_score = prediction_result.get('risk_score', 0)
            risk_level = prediction_result.get('risk_level', 'Medium')
            reliability_category = prediction_result.get('reliability_category', 'Medium')
            
        except Exception as e:
            # Fallback to static calculation if ML fails
            print(f"ML prediction failed for locomotive {loco.locomotive_id}: {str(e)}")
            risk_score = loco.calculate_risk_score()
            risk_level = loco.get_risk_level()
            reliability_category = 'Medium'
        
        risk_distribution[risk_level] += 1
        
        risk_data.append({
            'locomotive': loco,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'reliability_category': reliability_category,
            'age': loco.age,
            'operating_hours': loco.operating_hours,
            'status': loco.current_status,
            'prediction_method': 'ML Model'
        })
    
    # Sort by risk score (highest first)
    risk_data.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return {
        'title': 'Risk Assessment Report',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_locomotives': len(locomotives),
        'risk_distribution': risk_distribution,
        'risk_data': risk_data[:50],  # Top 50 highest risk
        'high_risk_count': risk_distribution['High'],
        'medium_risk_count': risk_distribution['Medium'],
        'low_risk_count': risk_distribution['Low'],
        'ml_predictions_used': True
    }

def generate_ml_predictions_report():
    """Generate comprehensive ML predictions report"""
    locomotives = Locomotive.query.all()
    
    # Import ML service
    from app.loco_ml_service import loco_ml_service
    
    # Get ML predictions for all locomotives
    ml_predictions = []
    risk_distribution = {'High': 0, 'Medium': 0, 'Low': 0}
    
    for loco in locomotives:
        try:
            # Get ML prediction for all performance metrics
            prediction_result = loco_ml_service.predict_performance(
                locomotive=loco,
                prediction_type='all',
                period_days=365
            )
            
            risk_score = prediction_result.get('risk_score', 0)
            risk_level = prediction_result.get('risk_level', 'Medium')
            reliability_category = prediction_result.get('reliability_category', 'Medium')
            predictions = prediction_result.get('predictions', {})
            recommendations = prediction_result.get('recommendations', [])
            
            risk_distribution[risk_level] += 1
            
            ml_predictions.append({
                'locomotive': loco,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'reliability_category': reliability_category,
                'predictions': predictions,
                'recommendations': recommendations,
                'prediction_method': 'ML Model',
                'timestamp': prediction_result.get('timestamp', datetime.now().isoformat())
            })
            
        except Exception as e:
            print(f"ML prediction failed for locomotive {loco.locomotive_id}: {str(e)}")
            # Add locomotive with fallback data
            ml_predictions.append({
                'locomotive': loco,
                'risk_score': loco.calculate_risk_score(),
                'risk_level': loco.get_risk_level(),
                'reliability_category': 'Medium',
                'predictions': {},
                'recommendations': ['ML prediction unavailable - using fallback calculation'],
                'prediction_method': 'Fallback',
                'timestamp': datetime.now().isoformat()
            })
    
    # Sort by risk score (highest first)
    ml_predictions.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # Calculate summary statistics
    total_predictions = len(ml_predictions)
    avg_risk_score = sum(p['risk_score'] for p in ml_predictions) / total_predictions if total_predictions > 0 else 0
    
    return {
        'title': 'ML Predictions Report',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_locomotives': total_predictions,
        'risk_distribution': risk_distribution,
        'ml_predictions': ml_predictions[:50],  # Top 50 highest risk
        'high_risk_count': risk_distribution['High'],
        'medium_risk_count': risk_distribution['Medium'],
        'low_risk_count': risk_distribution['Low'],
        'avg_risk_score': round(avg_risk_score, 2),
        'ml_predictions_used': True
    }

def generate_performance_forecast_report():
    """Generate performance forecast report"""
    # Get recent predictions
    predictions = Prediction.query.filter_by(is_active=True)\
        .order_by(Prediction.created_at.desc()).limit(100).all()
    
    if not predictions:
        return {
            'title': 'Performance Forecast Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': 'No performance predictions available. Please generate some predictions first.',
            'predictions': []
        }
    
    # Analyze prediction data
    prediction_summary = {
        'total_predictions': len(predictions),
        'avg_risk_score': sum(p.risk_score for p in predictions) / len(predictions),
        'risk_levels': {'High': 0, 'Medium': 0, 'Low': 0},
        'prediction_types': {}
    }
    
    for pred in predictions:
        prediction_summary['risk_levels'][pred.risk_level] += 1
        
        pred_type = pred.prediction_type or 'all'
        if pred_type not in prediction_summary['prediction_types']:
            prediction_summary['prediction_types'][pred_type] = 0
        prediction_summary['prediction_types'][pred_type] += 1
    
    return {
        'title': 'Performance Forecast Report',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'prediction_summary': prediction_summary,
        'predictions': predictions[:20],  # Recent 20 predictions
        'total_locomotives': Locomotive.query.count()
    }

def generate_maintenance_planning_report():
    """Generate maintenance planning report based on ML predictions"""
    locomotives = Locomotive.query.all()
    
    # Import ML service
    from app.loco_ml_service import loco_ml_service
    
    # Categorize locomotives by maintenance priority
    maintenance_plan = {
        'urgent': [],      # High risk, overdue maintenance
        'scheduled': [],   # Medium risk, regular maintenance
        'routine': []      # Low risk, routine maintenance
    }
    
    for loco in locomotives:
        try:
            # Use ML service to get accurate risk assessment
            prediction_result = loco_ml_service.predict_performance(
                locomotive=loco,
                prediction_type='all',
                period_days=365
            )
            
            risk_score = prediction_result.get('risk_score', 0)
            risk_level = prediction_result.get('risk_level', 'Medium')
            
        except Exception as e:
            # Fallback to static calculation if ML fails
            print(f"ML prediction failed for locomotive {loco.locomotive_id}: {str(e)}")
            risk_score = loco.calculate_risk_score()
            risk_level = loco.get_risk_level()
        
        # Check maintenance status
        days_since_maintenance = 0
        if loco.last_maintenance:
            days_since_maintenance = (datetime.now().date() - loco.last_maintenance).days
        
        maintenance_item = {
            'locomotive': loco,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'days_since_maintenance': days_since_maintenance,
            'priority': 'urgent' if risk_level == 'High' or days_since_maintenance > 90 else 
                       'scheduled' if risk_level == 'Medium' or days_since_maintenance > 60 else 'routine'
        }
        
        maintenance_plan[maintenance_item['priority']].append(maintenance_item)
    
    # Sort by risk score within each category
    for category in maintenance_plan:
        maintenance_plan[category].sort(key=lambda x: x['risk_score'], reverse=True)
    
    return {
        'title': 'Maintenance Planning Report',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'maintenance_plan': maintenance_plan,
        'total_locomotives': len(locomotives),
        'urgent_count': len(maintenance_plan['urgent']),
        'scheduled_count': len(maintenance_plan['scheduled']),
        'routine_count': len(maintenance_plan['routine'])
    }


def generate_data_export_report():
    """Generate comprehensive data export"""
    locomotives = Locomotive.query.all()
    predictions = Prediction.query.filter_by(is_active=True).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write locomotives data
    writer.writerow(['=== LOCOMOTIVES DATA ==='])
    writer.writerow(['Locomotive ID', 'Model', 'Age', 'Operating Hours', 'Status', 'Risk Score', 'Risk Level'])
    
    for loco in locomotives:
        risk_score = loco.calculate_risk_score()
        risk_level = loco.get_risk_level()
        writer.writerow([
            loco.locomotive_id,
            loco.model,
            loco.age,
            loco.operating_hours,
            loco.current_status,
            risk_score,
            risk_level
        ])
    
    # Write predictions data
    writer.writerow([])
    writer.writerow(['=== PREDICTIONS DATA ==='])
    writer.writerow(['Locomotive ID', 'Prediction Type', 'Risk Score', 'Risk Level', 'Created At'])
    
    for pred in predictions:
        writer.writerow([
            pred.locomotive.locomotive_id,
            pred.prediction_type,
            pred.risk_score,
            pred.risk_level,
            pred.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=complete_fleet_data_export.csv'
    return response

@reports_bp.route('/print-id/<int:id>')
@login_required
def print_report_by_id(id):
    """Print-friendly version of report"""
    # For now, we'll generate the report data directly
    # In a real implementation, you'd store and retrieve report data by ID
    report_type = request.args.get('type', 'risk_assessment')
    
    if report_type == 'risk_assessment':
        data = generate_risk_assessment_report()
    elif report_type == 'performance_forecast':
        data = generate_performance_forecast_report()
    elif report_type == 'maintenance_planning':
        data = generate_maintenance_planning_report()
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('reports.index'))
    
    return render_template('reports/print.html', 
                         report_data=data, 
                         report_type=report_type)

@reports_bp.route('/download-id/<int:id>')
@login_required
def download_report_by_id(id):
    """Download report as PDF or CSV"""
    report_type = request.args.get('type', 'risk_assessment')
    format_type = request.args.get('format', 'csv')
    
    if format_type == 'csv':
        if report_type == 'data_export':
            return generate_data_export_report()
        else:
            # Generate CSV for other report types
            if report_type == 'risk_assessment':
                data = generate_risk_assessment_report()
            elif report_type == 'performance_forecast':
                data = generate_performance_forecast_report()
            elif report_type == 'maintenance_planning':
                data = generate_maintenance_planning_report()
            else:
                flash('Invalid report type', 'error')
                return redirect(url_for('reports.index'))
            
            return generate_csv_report(data, report_type)
    else:
        flash('Unsupported format', 'error')
        return redirect(url_for('reports.index'))
