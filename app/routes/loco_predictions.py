from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.locomotive import Locomotive
from app.models.prediction import Prediction
from app.loco_ml_service import loco_ml_service
from datetime import datetime, timedelta
import json

loco_predictions_bp = Blueprint('loco_predictions', __name__)

@loco_predictions_bp.route('/')
@login_required
def index():
    """Loco Predictions main page"""
    # Get sample locomotives for dropdown (limit to 50 for performance)
    locomotives = Locomotive.query.limit(50).all()
    
    # Get recent predictions
    predictions = Prediction.query.filter_by(is_active=True)\
        .order_by(Prediction.created_at.desc()).limit(10).all()
    
    return render_template('loco_predictions/index.html', 
                         locomotives=locomotives,
                         predictions=predictions)

@loco_predictions_bp.route('/predict/<locomotive_id>')
@login_required
def predict_single(locomotive_id):
    """Redirect to predictions page with locomotive pre-selected"""
    # Verify locomotive exists
    locomotive = Locomotive.query.filter_by(locomotive_id=locomotive_id).first()
    if not locomotive:
        flash('Locomotive not found', 'error')
        return redirect(url_for('loco_predictions.index'))
    
    # Get locomotives for dropdown
    locomotives = Locomotive.query.limit(50).all()
    
    # Get recent predictions
    predictions = Prediction.query.filter_by(is_active=True)\
        .order_by(Prediction.created_at.desc()).limit(10).all()
    
    return render_template('loco_predictions/index.html', 
                         locomotives=locomotives,
                         predictions=predictions,
                         selected_locomotive=locomotive)

@loco_predictions_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """Generate locomotive performance prediction"""
    locomotive_number = request.form.get('locomotive_number')
    locomotive_type = request.form.get('locomotive_type')
    prediction_type = request.form.get('prediction_type')
    prediction_period = 365  # Fixed to 1 year for realistic predictions
    
    if not locomotive_number or not locomotive_type or not prediction_type:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('loco_predictions.index'))
    
    try:
        # Get locomotive from database
        locomotive = Locomotive.query.filter_by(locomotive_id=locomotive_number).first()
        
        if not locomotive:
            flash(f'Locomotive {locomotive_number} not found in database.', 'error')
            return redirect(url_for('loco_predictions.index'))
        
        # Validate that the selected locomotive type matches the actual type in database
        if locomotive.model != locomotive_type:
            flash(f'Locomotive {locomotive_number} is actually a {locomotive.model}, not {locomotive_type}. Please select the correct type.', 'error')
            return redirect(url_for('loco_predictions.index'))
        
        # Generate prediction using ML service
        prediction_result = loco_ml_service.predict_performance(
            locomotive=locomotive,
            prediction_type=prediction_type,
            period_days=prediction_period
        )
        
        # Store prediction in database
        prediction = Prediction(
            locomotive_id=locomotive.id,
            prediction_type=prediction_type,
            prediction_period=prediction_period,
            risk_score=prediction_result.get('risk_score', 0),
            risk_level=prediction_result.get('risk_level', 'Medium'),
            prediction_data=prediction_result,
            recommendations=prediction_result.get('recommendations', [])
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        flash(f'Performance prediction generated successfully for {locomotive_number}!', 'success')
        return redirect(url_for('loco_predictions.view_result', id=prediction.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating prediction: {str(e)}', 'error')
        return redirect(url_for('loco_predictions.index'))

@loco_predictions_bp.route('/result/<int:id>')
@login_required
def view_result(id):
    """View prediction result"""
    prediction = Prediction.query.get_or_404(id)
    locomotive = Locomotive.query.get_or_404(prediction.locomotive_id)
    
    # Parse prediction data
    try:
        prediction_data = json.loads(prediction.prediction_data) if prediction.prediction_data else {}
        recommendations = json.loads(prediction.recommendations) if prediction.recommendations else []
    except:
        prediction_data = {}
        recommendations = []
    
    return render_template('loco_predictions/result.html',
                         prediction=prediction,
                         locomotive=locomotive,
                         prediction_data=prediction_data,
                         recommendations=recommendations)

@loco_predictions_bp.route('/api/quick_predict')
@login_required
def api_quick_predict():
    """API endpoint for quick prediction without saving"""
    locomotive_number = request.args.get('locomotive_number')
    locomotive_type = request.args.get('locomotive_type')
    prediction_type = request.args.get('prediction_type')
    period = int(request.args.get('period', 30))
    
    if not locomotive_number or not locomotive_type or not prediction_type:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Get locomotive from database
        locomotive = Locomotive.query.filter_by(locomotive_id=locomotive_number).first()
        
        if not locomotive:
            return jsonify({'error': f'Locomotive {locomotive_number} not found'}), 404
        
        # Validate that the selected locomotive type matches the actual type in database
        if locomotive.model != locomotive_type:
            return jsonify({'error': f'Locomotive {locomotive_number} is actually a {locomotive.model}, not {locomotive_type}. Please select the correct type.'}), 400
        
        # Generate prediction using ML service
        prediction_result = loco_ml_service.predict_performance(
            locomotive=locomotive,
            prediction_type=prediction_type,
            period_days=period
        )
        
        return jsonify(prediction_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@loco_predictions_bp.route('/search_locomotive')
@login_required
def search_locomotive():
    """Search for locomotive by number"""
    search_term = request.args.get('q', '')
    
    if not search_term:
        return jsonify([])
    
    locomotives = Locomotive.query.filter(
        Locomotive.locomotive_id.contains(search_term)
    ).limit(10).all()
    
    results = []
    for loco in locomotives:
        results.append({
            'id': loco.id,
            'locomotive_id': loco.locomotive_id,
            'model': loco.model,
            'fleet': getattr(loco, 'fleet', 'NRZ'),
            'age': loco.age,
            'operating_hours': loco.operating_hours
        })
    
    return jsonify(results)

@loco_predictions_bp.route('/api/locomotive_info/<locomotive_number>')
@login_required
def get_locomotive_info(locomotive_number):
    """Get locomotive information by number"""
    locomotive = Locomotive.query.filter_by(locomotive_id=locomotive_number).first()
    
    if not locomotive:
        return jsonify({'error': 'Locomotive not found'}), 404
    
    return jsonify({
        'locomotive_id': locomotive.locomotive_id,
        'model': locomotive.model,
        'age': locomotive.age,
        'operating_hours': locomotive.operating_hours,
        'current_status': locomotive.current_status
    })

@loco_predictions_bp.route('/bulk_predict', methods=['POST'])
@login_required
def bulk_predict():
    """Generate predictions for multiple locomotives - Simplified approach"""
    locomotive_text = request.form.get('locomotive_numbers', '').strip()
    prediction_type = request.form.get('prediction_type')
    prediction_period = 365  # Fixed to 1 year for realistic predictions
    
    if not locomotive_text or not prediction_type:
        flash('Please enter locomotive numbers and select prediction type.', 'error')
        return redirect(url_for('loco_predictions.index'))
    
    # Parse locomotive numbers from textarea
    locomotive_numbers = [line.strip() for line in locomotive_text.split('\n') if line.strip()]
    
    if not locomotive_numbers:
        flash('Please enter at least one locomotive number.', 'error')
        return redirect(url_for('loco_predictions.index'))
    
    if len(locomotive_numbers) > 20:
        flash('Maximum 20 locomotives allowed for bulk prediction.', 'error')
        return redirect(url_for('loco_predictions.index'))
    
    results = []
    errors = []
    
    for loco_number in locomotive_numbers:
        try:
            # Get locomotive from database
            locomotive = Locomotive.query.filter_by(locomotive_id=loco_number).first()
            
            if not locomotive:
                errors.append(f'Locomotive {loco_number} not found in database')
                continue
            
            # Use simple risk calculation instead of ML service for bulk predictions
            risk_score = locomotive.calculate_risk_score()
            risk_level = locomotive.get_risk_level()
            
            # Generate simple predictions based on locomotive data
            predictions = {}
            age = locomotive.age
            hours = locomotive.operating_hours
            
            if prediction_type == 'all' or prediction_type == 'availability_days':
                predictions['availability_days'] = max(200, 365 - (age * 8))
            
            if prediction_type == 'all' or prediction_type == 'distance_travelled':
                predictions['distance_travelled'] = int(hours * 45 * (prediction_period / 365))
            
            if prediction_type == 'all' or prediction_type == 'distance_per_day':
                predictions['distance_per_day'] = round(120 - (age * 2), 2)
            
            if prediction_type == 'all' or prediction_type == 'total_failures':
                predictions['total_failures'] = max(0, int(age * 1.5))
            
            if prediction_type == 'all' or prediction_type == 'reliability':
                predictions['reliability'] = max(50, 95 - (age * 3))
            
            if prediction_type == 'all' or prediction_type == 'fuel_efficiency':
                predictions['fuel_efficiency'] = max(60, 90 - (age * 2))
            
            # Generate targeted recommendations based on prediction type
            recommendations = []
            
            # Always include basic risk assessment
            if risk_level == 'High':
                recommendations.append('🚨 URGENT: High risk detected. Schedule immediate inspection before operations.')
            elif risk_level == 'Medium':
                recommendations.append('📅 Medium risk level. Monitor performance closely during operations.')
            else:
                recommendations.append('✅ Low risk level. Locomotive is in good operational condition.')
            
            # Generate recommendations based on prediction type
            if prediction_type == 'availability_days':
                recommendations.extend(_get_availability_recommendations(risk_level, age, hours))
            elif prediction_type == 'distance_travelled':
                recommendations.extend(_get_distance_recommendations(risk_level, age, hours))
            elif prediction_type == 'distance_per_day':
                recommendations.extend(_get_daily_distance_recommendations(risk_level, age, hours))
            elif prediction_type == 'total_failures':
                recommendations.extend(_get_failure_recommendations(risk_level, age, hours))
            elif prediction_type == 'reliability':
                recommendations.extend(_get_reliability_recommendations(risk_level, age, hours))
            elif prediction_type == 'fuel_efficiency':
                recommendations.extend(_get_fuel_efficiency_recommendations(risk_level, age, hours))
            elif prediction_type == 'all':
                # For 'all', show a mix of the most important recommendations
                recommendations.extend(_get_availability_recommendations(risk_level, age, hours)[:1])
                recommendations.extend(_get_daily_distance_recommendations(risk_level, age, hours)[:1])
                recommendations.extend(_get_fuel_efficiency_recommendations(risk_level, age, hours)[:1])
                recommendations.extend(_get_failure_recommendations(risk_level, age, hours)[:1])
            
            # Ensure we always have at least one recommendation
            if len(recommendations) == 1:  # Only the basic risk assessment
                recommendations.append('✅ Continue regular maintenance and monitoring')
            
            # Create prediction result
            prediction_result = {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'reliability_category': 'High' if risk_score < 30 else 'Medium' if risk_score < 60 else 'Low',
                'predictions': predictions,
                'recommendations': recommendations,
                'prediction_method': 'Simplified Bulk Model',
                'period_days': prediction_period
            }
            
            # Store prediction in database
            prediction = Prediction(
                locomotive_id=locomotive.id,
                prediction_type=prediction_type,
                prediction_period=prediction_period,
                risk_score=risk_score,
                risk_level=risk_level,
                prediction_data=prediction_result,
                recommendations=recommendations
            )
            
            db.session.add(prediction)
            db.session.flush()  # Get the ID immediately
            
            # Add to results
            results.append({
                'locomotive_id': locomotive.locomotive_id,
                'model': locomotive.model,
                'age': locomotive.age,
                'operating_hours': locomotive.operating_hours,
                'prediction': prediction_result,
                'prediction_id': prediction.id
            })
            
        except Exception as e:
            errors.append(f'Error processing {loco_number}: {str(e)}')
            continue
    
    # Commit all predictions
    try:
        db.session.commit()
        
        # Store results in session for display
        from flask import session
        session['bulk_prediction_results'] = results
        session['bulk_prediction_errors'] = errors
        session['bulk_prediction_type'] = prediction_type
        session['bulk_prediction_period'] = prediction_period
        
        success_count = len(results)
        error_count = len(errors)
        
        if success_count > 0:
            flash(f'Successfully generated {success_count} predictions!', 'success')
        if error_count > 0:
            flash(f'{error_count} predictions failed. Check results for details.', 'warning')
        
        return redirect(url_for('loco_predictions.bulk_results'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving predictions: {str(e)}', 'error')
        return redirect(url_for('loco_predictions.index'))

def _get_availability_recommendations(risk_level, age, hours):
    """Get recommendations specific to availability predictions"""
    recommendations = []
    
    if risk_level == 'High':
        recommendations.append('📉 LOW AVAILABILITY EXPECTED: Schedule extended maintenance downtime to improve reliability.')
        recommendations.append('🛠️ Multiple system checks required. Consider component replacement.')
    elif risk_level == 'Medium':
        recommendations.append('📊 MODERATE AVAILABILITY: Plan maintenance during low-demand periods.')
        recommendations.append('🔍 Increase inspection frequency to prevent unexpected downtime.')
    else:
        recommendations.append('📈 HIGH AVAILABILITY EXPECTED: Continue current maintenance schedule.')
        recommendations.append('✅ Suitable for continuous operations and high-demand periods.')
    
    if age > 20:
        recommendations.append('⏰ AGED LOCOMOTIVE: Plan for increased maintenance windows due to age.')
    
    return recommendations

def _get_distance_recommendations(risk_level, age, hours):
    """Get recommendations specific to distance travelled predictions"""
    recommendations = []
    
    if risk_level == 'High':
        recommendations.append('🛤️ LIMITED DISTANCE CAPABILITY: Avoid long-distance routes (>500km).')
        recommendations.append('📉 Reduced operational range expected. Plan for shorter routes.')
    elif risk_level == 'Medium':
        recommendations.append('🛤️ MODERATE DISTANCE CAPABILITY: Suitable for medium-distance routes (200-500km).')
        recommendations.append('📊 Monitor fuel consumption and system performance on longer routes.')
    else:
        recommendations.append('🛤️ HIGH DISTANCE CAPABILITY: Suitable for long-distance operations.')
        recommendations.append('✅ Can handle extended routes and heavy freight operations.')
    
    if hours > 50000:
        recommendations.append('⏱️ HIGH USAGE: Consider route planning to minimize wear on high-mileage components.')
    
    return recommendations

def _get_daily_distance_recommendations(risk_level, age, hours):
    """Get recommendations specific to daily distance predictions"""
    recommendations = []
    
    if risk_level == 'High':
        recommendations.append('📉 LOW DAILY DISTANCE: Limit to short-haul operations (<200km/day).')
        recommendations.append('🛠️ System performance issues affecting daily range. Schedule diagnostics.')
    elif risk_level == 'Medium':
        recommendations.append('📊 MODERATE DAILY DISTANCE: Suitable for medium-haul operations (200-400km/day).')
        recommendations.append('🔍 Monitor daily performance metrics and fuel consumption.')
    else:
        recommendations.append('📈 HIGH DAILY DISTANCE: Capable of long-haul operations (>400km/day).')
        recommendations.append('✅ Optimal for high-intensity daily operations.')
    
    if age > 20:
        recommendations.append('⏰ AGED LOCOMOTIVE: Daily distance may be limited by component wear.')
    
    return recommendations

def _get_failure_recommendations(risk_level, age, hours):
    """Get recommendations specific to failure predictions"""
    recommendations = []
    
    if risk_level == 'High':
        recommendations.append('⚠️ HIGH FAILURE RISK: Schedule comprehensive maintenance before operations.')
        recommendations.append('🚫 Avoid critical routes. Have backup locomotive ready.')
    elif risk_level == 'Medium':
        recommendations.append('📊 MODERATE FAILURE RISK: Increase monitoring frequency during operations.')
        recommendations.append('🛠️ Schedule preventive maintenance to reduce failure probability.')
    else:
        recommendations.append('✅ LOW FAILURE RISK: Continue current maintenance practices.')
        recommendations.append('📈 Suitable for critical and time-sensitive operations.')
    
    if age > 20:
        recommendations.append('🔧 AGED LOCOMOTIVE: Higher failure risk due to component aging.')
    
    if hours > 50000:
        recommendations.append('⏱️ HIGH USAGE: Component fatigue may increase failure probability.')
    
    return recommendations

def _get_reliability_recommendations(risk_level, age, hours):
    """Get recommendations specific to reliability predictions"""
    recommendations = []
    
    if risk_level == 'High':
        recommendations.append('🔴 LOW RELIABILITY: Do not assign to critical routes or time-sensitive operations.')
        recommendations.append('🛠️ Schedule comprehensive diagnostic check. Multiple systems need attention.')
    elif risk_level == 'Medium':
        recommendations.append('🟡 MODERATE RELIABILITY: Suitable for non-critical operations with backup plans.')
        recommendations.append('📋 Increase monitoring frequency. Prepare contingency plans.')
    else:
        recommendations.append('✅ HIGH RELIABILITY: Suitable for all types of operations.')
        recommendations.append('🚂 Optimal for critical routes and time-sensitive deliveries.')
    
    if age > 20:
        recommendations.append('⏰ AGED LOCOMOTIVE: Reliability may decrease due to component aging.')
    
    return recommendations

def _get_fuel_efficiency_recommendations(risk_level, age, hours):
    """Get recommendations specific to fuel efficiency predictions"""
    recommendations = []
    
    if age > 20 and hours > 50000:
        recommendations.append('⛽ POOR FUEL EFFICIENCY: Check engine tuning, air filters, and fuel injection systems.')
        recommendations.append('🚫 Avoid this locomotive for fuel-sensitive operations. Consider engine overhaul.')
    elif age > 15 or hours > 40000:
        recommendations.append('⛽ MODERATE FUEL EFFICIENCY: Schedule engine tune-up and filter replacement.')
        recommendations.append('📈 Monitor fuel consumption closely. Consider driver training for fuel-efficient operation.')
    else:
        recommendations.append('⛽ GOOD FUEL EFFICIENCY: Continue current maintenance practices to maintain efficiency.')
        recommendations.append('✅ Suitable for fuel-sensitive operations and long-distance routes.')
    
    # Seasonal fuel efficiency tips
    from datetime import datetime
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:  # Winter months
        recommendations.append('❄️ WINTER: Cold weather reduces fuel efficiency. Plan for increased consumption.')
    elif current_month in [6, 7, 8]:  # Summer months
        recommendations.append('☀️ SUMMER: High temperatures may reduce fuel efficiency. Monitor cooling systems.')
    
    return recommendations

@loco_predictions_bp.route('/bulk_results')
@login_required
def bulk_results():
    """Display bulk prediction results from database"""
    from flask import session
    
    # Get recent predictions from database (last 100 predictions)
    recent_predictions = Prediction.query.filter_by(is_active=True)\
        .order_by(Prediction.created_at.desc()).limit(100).all()
    
    # Convert database predictions to display format
    results = []
    for pred in recent_predictions:
        locomotive = Locomotive.query.get(pred.locomotive_id)
        if locomotive:
            results.append({
                'locomotive_id': locomotive.locomotive_id,
                'model': locomotive.model,
                'age': locomotive.age,
                'operating_hours': locomotive.operating_hours,
                'prediction': {
                    'risk_score': pred.risk_score,
                    'risk_level': pred.risk_level,
                    'reliability_category': pred.prediction_data_dict.get('reliability_category', 'Medium'),
                    'predictions': pred.prediction_data_dict.get('predictions', {}),
                    'recommendations': pred.recommendations_list
                },
                'prediction_id': pred.id,
                'created_at': pred.created_at,
                'prediction_type': pred.prediction_type or 'all',
                'prediction_period': pred.prediction_period or 30
            })
    
    # Get session data for any new results (don't clear immediately)
    session_results = session.get('bulk_prediction_results', [])
    session_errors = session.get('bulk_prediction_errors', [])
    session_prediction_type = session.get('bulk_prediction_type', 'all')
    session_prediction_period = session.get('bulk_prediction_period', 30)
    
    # If we have session results, prepend them to the database results
    if session_results:
        results = session_results + results
        # Clear session data after displaying
        session.pop('bulk_prediction_results', None)
        session.pop('bulk_prediction_errors', None)
        session.pop('bulk_prediction_type', None)
        session.pop('bulk_prediction_period', None)
    
    # Use session data for display if available, otherwise use database data
    display_prediction_type = session_prediction_type if session_results else 'all'
    display_prediction_period = session_prediction_period if session_results else 30
    
    return render_template('loco_predictions/bulk_results.html',
                         results=results,
                         errors=session_errors,
                         prediction_type=display_prediction_type,
                         prediction_period=display_prediction_period,
                         generated_at=datetime.now())

@loco_predictions_bp.route('/clear_all', methods=['POST'])
@login_required
def clear_all():
    """Clear all predictions"""
    try:
        # Deactivate all predictions instead of deleting them
        predictions = Prediction.query.filter_by(is_active=True).all()
        for prediction in predictions:
            prediction.is_active = False
        
        db.session.commit()
        flash('All predictions have been cleared successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing predictions: {str(e)}', 'error')
    
    return redirect(url_for('loco_predictions.index'))
