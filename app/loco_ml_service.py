import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import warnings

# Suppress sklearn warnings about feature names
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

class LocomotiveMLService:
    def __init__(self):
        self.models_loaded = False
        self.risk_model = None
        self.reliability_model = None
        self.scaler = None
        self.fleet_encoder = None
        self.reliability_encoder = None
        self.age_encoder = None
        self.feature_columns = None
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load the trained ML models and preprocessing objects"""
        try:
            models_dir = os.path.join(os.path.dirname(__file__), 'ml_models')
            
            # Load models
            self.risk_model = joblib.load(os.path.join(models_dir, 'risk_score_model.pkl'))
            self.reliability_model = joblib.load(os.path.join(models_dir, 'reliability_model.pkl'))
            self.scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
            
            # Load encoders
            self.fleet_encoder = joblib.load(os.path.join(models_dir, 'fleet_encoder.pkl'))
            self.reliability_encoder = joblib.load(os.path.join(models_dir, 'reliability_encoder.pkl'))
            self.age_encoder = joblib.load(os.path.join(models_dir, 'age_encoder.pkl'))
            
            # Load feature columns
            self.feature_columns = joblib.load(os.path.join(models_dir, 'feature_columns.pkl'))
            
            self.models_loaded = True
            print("Locomotive ML models loaded successfully!")
            
        except Exception as e:
            print(f"Error loading ML models: {str(e)}")
            self.models_loaded = False
    
    def _prepare_locomotive_features(self, locomotive):
        """Prepare locomotive features for ML prediction"""
        try:
            # Get locomotive attributes
            loco_type = 1 if locomotive.model == 'DE10' else 2  # DE10=1, DE11=2
            age = locomotive.age
            operating_hours = locomotive.operating_hours
            manufacturing_year = locomotive.manufacturing_year
            
            # Calculate derived features based on typical locomotive performance
            # These are estimated based on the dataset patterns
            availability_days = max(300, 365 - (age * 5))  # Decreases with age
            distance_travelled = operating_hours * 50  # Average 50 km/h
            distance_per_day = distance_travelled / 365 if availability_days > 0 else 0
            total_failures = max(0, age * 2 + (operating_hours / 10000))  # Increases with age and usage
            reliability = max(60, 95 - (age * 2) - (total_failures * 5))  # Decreases with age and failures
            failure_rate = total_failures / max(1, operating_hours / 1000)
            usage_intensity = operating_hours / max(1, age * 365 * 24)
            maintenance_frequency = max(2, age * 0.5)  # Maintenance increases with age
            fuel_efficiency = max(70, 90 - (age * 1.5))  # Decreases with age
            efficiency_score = (reliability + fuel_efficiency) / 2
            maintenance_score = max(60, 100 - (maintenance_frequency * 10))
            risk_score = (total_failures * 10) + (age * 2) + (failure_rate * 100)
            
            # Determine categories
            if reliability >= 90:
                reliability_category = 'High'
            elif reliability >= 75:
                reliability_category = 'Medium'
            elif reliability >= 60:
                reliability_category = 'Low'
            else:
                reliability_category = 'Critical'
            
            if age <= 5:
                age_category = 'New'
            elif age <= 10:
                age_category = 'Young'
            elif age <= 20:
                age_category = 'Mature'
            else:
                age_category = 'Old'
            
            # Encode categorical variables
            fleet_type = getattr(locomotive, 'fleet', 'NRZ')
            fleet_encoded = self.fleet_encoder.transform([fleet_type])[0]
            reliability_encoded = self.reliability_encoder.transform([reliability_category])[0]
            age_encoded = self.age_encoder.transform([age_category])[0]
            
            # Create additional features
            failure_rate_per_hour = total_failures / max(1, operating_hours)
            distance_per_hour = distance_travelled / max(1, operating_hours)
            availability_rate = availability_days / 365
            
            # Create feature vector in the same order as training (21 features)
            feature_data = {
                'LOCO_TYPE': [loco_type],
                'YEAR': [datetime.now().year],
                'Availability_Days': [availability_days],
                'Distance_Travelled': [distance_travelled],
                'Distance_per_day': [distance_per_day],
                'Total_Failures': [total_failures],
                'Reliability': [reliability],
                'Failure_Rate': [failure_rate],
                'Age_of_Locomotive': [age],
                'Usage_Intensity': [usage_intensity],
                'Maintenance_Frequency': [maintenance_frequency],
                'Fuel_Efficiency': [fuel_efficiency],
                'Operating_Hours': [operating_hours],
                'Fleet_Type_Encoded': [fleet_encoded],
                'Efficiency_Score': [efficiency_score],
                'Maintenance_Score': [maintenance_score],
                'Reliability_Category_Encoded': [reliability_encoded],
                'Age_Category_Encoded': [age_encoded],
                'Failure_Rate_per_Hour': [failure_rate_per_hour],
                'Distance_per_Hour': [distance_per_hour],
                'Availability_Rate': [availability_rate]
            }
            
            # Create DataFrame with proper column names
            features_df = pd.DataFrame(feature_data)
            return features_df
            
        except Exception as e:
            print(f"Error preparing locomotive features: {str(e)}")
            return None
    
    def predict_performance(self, locomotive, prediction_type, period_days=30):
        """Predict locomotive performance for specified type and period"""
        if not self.models_loaded:
            return self._fallback_prediction(locomotive, prediction_type, period_days)
        
        try:
            # Prepare features
            features = self._prepare_locomotive_features(locomotive)
            if features is None:
                return self._fallback_prediction(locomotive, prediction_type, period_days)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make predictions
            ml_risk_score = self.risk_model.predict(features_scaled)[0]
            reliability_encoded = self.reliability_model.predict(features_scaled)[0]
            reliability_category = self.reliability_encoder.inverse_transform([reliability_encoded])[0]
            
            # Scale ML risk score to provide more realistic distribution
            # ML model tends to predict very low scores, so we scale them up
            if ml_risk_score < 10:
                # Scale low ML scores to more realistic range
                risk_score = ml_risk_score * 8 + locomotive.age * 1.5 + (locomotive.operating_hours / 1000) * 0.3
            else:
                risk_score = ml_risk_score * 2 + locomotive.age * 0.5
            
            # Ensure risk score is within reasonable bounds
            risk_score = max(5, min(100, risk_score))
            
            # Determine risk level
            if risk_score >= 70:
                risk_level = 'High'
            elif risk_score >= 40:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            # Generate specific predictions based on type
            predictions = self._generate_specific_predictions(
                locomotive, prediction_type, period_days, risk_score, reliability_category
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                locomotive, risk_score, risk_level, reliability_category, prediction_type
            )
            
            return {
                'prediction_type': prediction_type,
                'period_days': period_days,
                'risk_score': float(risk_score),
                'risk_level': risk_level,
                'reliability_category': reliability_category,
                'predictions': predictions,
                'recommendations': recommendations,
                'prediction_method': 'ML Performance Model',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in ML prediction: {str(e)}")
            return self._fallback_prediction(locomotive, prediction_type, period_days)
    
    def _generate_specific_predictions(self, locomotive, prediction_type, period_days, risk_score, reliability_category):
        """Generate realistic annual performance predictions"""
        predictions = {}
        
        # Base calculations for annual projections
        age = locomotive.age
        operating_hours = locomotive.operating_hours
        
        if prediction_type == 'all' or prediction_type == 'availability_days':
            # Annual availability (days per year)
            base_availability = max(250, 365 - (age * 8))
            risk_factor = 1 - (risk_score / 200)  # Higher risk = lower availability
            predicted_availability = int(base_availability * risk_factor)
            predictions['availability_days'] = max(0, predicted_availability)
        
        if prediction_type == 'all' or prediction_type == 'distance_travelled':
            # Annual distance travelled
            base_distance = operating_hours * 45  # Average 45 km/h
            risk_factor = 1 - (risk_score / 300)
            predicted_distance = int(base_distance * risk_factor)
            predictions['distance_travelled'] = max(0, predicted_distance)
        
        if prediction_type == 'all' or prediction_type == 'distance_per_day':
            # Average daily distance
            base_daily_distance = 120  # Average daily distance
            risk_factor = 1 - (risk_score / 200)
            predicted_daily_distance = round(base_daily_distance * risk_factor, 2)
            predictions['distance_per_day'] = max(0, predicted_daily_distance)
        
        if prediction_type == 'all' or prediction_type == 'total_failures':
            # Annual failures
            base_failure_rate = age * 0.5 + (operating_hours / 15000)
            risk_factor = 1 + (risk_score / 100)  # Higher risk = more failures
            predicted_failures = int(base_failure_rate * risk_factor)
            predictions['total_failures'] = max(0, predicted_failures)
        
        if prediction_type == 'all' or prediction_type == 'reliability':
            # Annual reliability
            base_reliability = max(50, 95 - (age * 2.5))
            risk_factor = 1 - (risk_score / 150)
            predicted_reliability = round(base_reliability * risk_factor, 2)
            predictions['reliability'] = max(0, min(100, predicted_reliability))
        
        if prediction_type == 'all' or prediction_type == 'fuel_efficiency':
            # Annual fuel efficiency
            base_efficiency = max(60, 90 - (age * 1.8))
            risk_factor = 1 - (risk_score / 200)
            predicted_efficiency = round(base_efficiency * risk_factor, 2)
            predictions['fuel_efficiency'] = max(0, min(100, predicted_efficiency))
        
        return predictions
    
    def _generate_recommendations(self, locomotive, risk_score, risk_level, reliability_category, prediction_type):
        """Generate targeted recommendations based on prediction type"""
        recommendations = []
        age = locomotive.age
        hours = locomotive.operating_hours
        
        # Always include basic risk assessment
        if risk_level == 'High':
            recommendations.append('🚨 URGENT: High risk detected. Schedule immediate inspection before operations.')
        elif risk_level == 'Medium':
            recommendations.append('📅 Medium risk level. Monitor performance closely during operations.')
        else:
            recommendations.append('✅ Low risk level. Locomotive is in good operational condition.')
        
        # Generate recommendations based on prediction type
        if prediction_type == 'availability_days':
            recommendations.extend(self._get_availability_recommendations(risk_level, age, hours))
        elif prediction_type == 'distance_travelled':
            recommendations.extend(self._get_distance_recommendations(risk_level, age, hours))
        elif prediction_type == 'distance_per_day':
            recommendations.extend(self._get_daily_distance_recommendations(risk_level, age, hours))
        elif prediction_type == 'total_failures':
            recommendations.extend(self._get_failure_recommendations(risk_level, age, hours))
        elif prediction_type == 'reliability':
            recommendations.extend(self._get_reliability_recommendations(risk_level, reliability_category, age, hours))
        elif prediction_type == 'fuel_efficiency':
            recommendations.extend(self._get_fuel_efficiency_recommendations(risk_level, age, hours))
        elif prediction_type == 'all':
            # For 'all', show a mix of the most important recommendations
            recommendations.extend(self._get_availability_recommendations(risk_level, age, hours)[:1])
            recommendations.extend(self._get_daily_distance_recommendations(risk_level, age, hours)[:1])
            recommendations.extend(self._get_fuel_efficiency_recommendations(risk_level, age, hours)[:1])
            recommendations.extend(self._get_failure_recommendations(risk_level, age, hours)[:1])
        
        # Ensure we always have at least one recommendation
        if len(recommendations) == 1:  # Only the basic risk assessment
            recommendations.append('✅ Continue regular maintenance and monitoring')
        
        return recommendations[:6]  # Limit to 6 recommendations
    
    def _get_availability_recommendations(self, risk_level, age, hours):
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
    
    def _get_distance_recommendations(self, risk_level, age, hours):
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
    
    def _get_daily_distance_recommendations(self, risk_level, age, hours):
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
    
    def _get_failure_recommendations(self, risk_level, age, hours):
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
    
    def _get_reliability_recommendations(self, risk_level, reliability_category, age, hours):
        """Get recommendations specific to reliability predictions"""
        recommendations = []
        
        if reliability_category == 'Critical':
            recommendations.append('🔴 CRITICAL RELIABILITY: Do not assign to critical routes or time-sensitive operations.')
            recommendations.append('🛠️ Schedule comprehensive diagnostic check. Multiple systems need attention.')
        elif reliability_category == 'Low':
            recommendations.append('🟡 LOW RELIABILITY: Suitable for non-critical operations with backup plans.')
            recommendations.append('📋 Increase monitoring frequency. Prepare contingency plans.')
        else:
            recommendations.append('✅ HIGH RELIABILITY: Suitable for all types of operations.')
            recommendations.append('🚂 Optimal for critical routes and time-sensitive deliveries.')
        
        if age > 20:
            recommendations.append('⏰ AGED LOCOMOTIVE: Reliability may decrease due to component aging.')
        
        return recommendations
    
    def _get_fuel_efficiency_recommendations(self, risk_level, age, hours):
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
    
    def _fallback_prediction(self, locomotive, prediction_type, period_days):
        """Fallback prediction when ML models are not available"""
        risk_score = locomotive.calculate_risk_score()
        risk_level = locomotive.get_risk_level()
        
        # Simple predictions based on locomotive attributes
        predictions = {}
        age = locomotive.age
        operating_hours = locomotive.operating_hours
        
        if prediction_type == 'all' or prediction_type == 'availability_days':
            predictions['availability_days'] = max(200, 365 - (age * 10))
        
        if prediction_type == 'all' or prediction_type == 'distance_travelled':
            predictions['distance_travelled'] = int(operating_hours * 40 * (period_days / 365))
        
        if prediction_type == 'all' or prediction_type == 'distance_per_day':
            predictions['distance_per_day'] = round(100 - (age * 2), 2)
        
        if prediction_type == 'all' or prediction_type == 'total_failures':
            predictions['total_failures'] = max(0, int(age * 1.5))
        
        if prediction_type == 'all' or prediction_type == 'reliability':
            predictions['reliability'] = max(50, 95 - (age * 3))
        
        if prediction_type == 'all' or prediction_type == 'fuel_efficiency':
            predictions['fuel_efficiency'] = max(60, 90 - (age * 2))
        
        # Generate enhanced recommendations for fallback method
        recommendations = []
        
        # Risk-based recommendations
        if risk_level == 'High':
            recommendations.append('🚨 URGENT: Do not use this locomotive for heavy operations. Schedule immediate comprehensive inspection and maintenance before next deployment.')
            recommendations.append('⚠️ Avoid long-distance routes (>500km) until risk assessment improves. Consider short-haul operations only.')
        elif risk_level == 'Medium':
            recommendations.append('📅 Schedule preventive maintenance within 2 weeks. Monitor performance closely during operations.')
            recommendations.append('🛤️ Suitable for medium-distance routes (200-500km). Avoid extreme weather conditions.')
        else:
            recommendations.append('✅ Locomotive is in good condition. Continue current maintenance schedule and regular operations.')
            recommendations.append('🚂 Suitable for all types of operations including long-distance and heavy freight.')
        
        # Age-based recommendations
        if age > 25:
            recommendations.append('🔧 CRITICAL: Major overhaul required due to age. Consider retiring from primary operations.')
            recommendations.append('⏰ Plan for component replacement - engine, transmission, and braking systems need attention.')
        elif age > 20:
            recommendations.append('📋 Schedule major maintenance cycle. Age indicates increased component wear.')
            recommendations.append('🛡️ Use for lighter operations during peak maintenance periods.')
        elif age > 15:
            recommendations.append('🔍 Increase inspection frequency. Monitor for early signs of component degradation.')
        
        # Operating hours recommendations
        if operating_hours > 60000:
            recommendations.append('⏱️ HIGH USAGE: Operating hours exceed recommended limits. Schedule extended maintenance downtime.')
            recommendations.append('🔄 Consider rotating this locomotive to lighter duty cycles to extend service life.')
        elif operating_hours > 50000:
            recommendations.append('📊 High operating hours detected. Plan for major component inspection and replacement.')
        
        # Seasonal usage recommendations
        from datetime import datetime
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:  # Winter months
            recommendations.append('❄️ WINTER OPERATIONS: Ensure heating systems are functional. Check antifreeze levels and battery condition.')
            recommendations.append('🌨️ Avoid operations in severe weather conditions. Plan for reduced availability due to weather.')
        elif current_month in [6, 7, 8]:  # Summer months
            recommendations.append('☀️ SUMMER OPERATIONS: Monitor cooling systems closely. Ensure adequate ventilation for crew comfort.')
            recommendations.append('🌡️ High temperature operations may reduce efficiency. Plan for increased maintenance intervals.')
        
        # Fuel efficiency recommendations
        predicted_fuel_efficiency = predictions.get('fuel_efficiency', 0)
        if predicted_fuel_efficiency < 60:
            recommendations.append('⛽ POOR FUEL EFFICIENCY: Check engine tuning, air filters, and fuel injection systems.')
            recommendations.append('🚫 Avoid this locomotive for fuel-sensitive operations. Consider engine overhaul.')
        elif predicted_fuel_efficiency < 75:
            recommendations.append('⛽ MODERATE FUEL EFFICIENCY: Schedule engine tune-up and filter replacement.')
            recommendations.append('📈 Monitor fuel consumption closely. Consider driver training for fuel-efficient operation.')
        else:
            recommendations.append('⛽ GOOD FUEL EFFICIENCY: Continue current maintenance practices to maintain efficiency.')
        
        # Fleet-specific recommendations
        if locomotive.model == 'DE10':
            recommendations.append('🏢 NRZ FLEET: Follow NRZ maintenance protocols. Ensure compliance with internal standards.')
        elif locomotive.model == 'DE11':
            recommendations.append('📋 HIRED FLEET: Review contractual maintenance obligations. Coordinate with vendor for major repairs.')
        
        # Ensure we always have at least one recommendation
        if not recommendations:
            recommendations.append('✅ Continue regular maintenance schedule and monitor performance indicators.')
        
        return {
            'prediction_type': prediction_type,
            'period_days': period_days,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'reliability_category': 'Medium',
            'predictions': predictions,
            'recommendations': recommendations,
            'prediction_method': 'Fallback Method',
            'timestamp': datetime.now().isoformat()
        }

# Create global instance
loco_ml_service = LocomotiveMLService()
