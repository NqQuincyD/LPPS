from app import db
from datetime import datetime, timedelta
import json

class Prediction(db.Model):
    __tablename__ = 'lpps_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    locomotive_id = db.Column(db.Integer, db.ForeignKey('lpps_locomotives.id'), nullable=False)
    prediction_type = db.Column(db.String(50), nullable=False)  # 'failure', 'maintenance', 'performance'
    prediction_period = db.Column(db.Integer, nullable=False)  # days
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)  # 'Low', 'Medium', 'High'
    prediction_data = db.Column(db.Text)  # JSON data for charts
    recommendations = db.Column(db.Text)  # JSON recommendations
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, locomotive_id, prediction_type, prediction_period, risk_score, 
                 risk_level, prediction_data=None, recommendations=None):
        self.locomotive_id = locomotive_id
        self.prediction_type = prediction_type
        self.prediction_period = prediction_period
        self.risk_score = risk_score
        self.risk_level = risk_level
        self.prediction_data = json.dumps(prediction_data) if prediction_data else None
        self.recommendations = json.dumps(recommendations) if recommendations else None
        self.expires_at = datetime.utcnow() + timedelta(days=prediction_period)
    
    @property
    def prediction_data_dict(self):
        """Get prediction data as dictionary"""
        if self.prediction_data:
            return json.loads(self.prediction_data)
        return {}
    
    @property
    def recommendations_list(self):
        """Get recommendations as list"""
        if self.recommendations:
            return json.loads(self.recommendations)
        return []
    
    @property
    def is_expired(self):
        """Check if prediction is expired"""
        return datetime.utcnow() > self.expires_at
    
    def get_risk_color(self):
        """Get color class for risk level"""
        color_map = {
            'Low': 'success',
            'Medium': 'warning',
            'High': 'danger'
        }
        return color_map.get(self.risk_level, 'secondary')
    
    @staticmethod
    def generate_prediction_data(locomotive, period_days):
        """Generate sample prediction data for charts"""
        import random
        import math
        
        # Generate performance trend data
        performance_data = []
        risk_data = []
        labels = []
        
        base_performance = 90 - (locomotive.age * 1.5) - (locomotive.operating_hours / 10000)
        base_risk = locomotive.calculate_risk_score()
        
        for i in range(period_days):
            day = i + 1
            labels.append(f"Day {day}")
            
            # Performance degrades over time with some randomness
            performance = max(20, base_performance - (day * 0.3) + random.uniform(-5, 5))
            performance_data.append(round(performance, 1))
            
            # Risk increases over time
            risk = min(95, base_risk + (day * 0.2) + random.uniform(-2, 2))
            risk_data.append(round(risk, 1))
        
        return {
            'labels': labels,
            'performance': performance_data,
            'risk': risk_data
        }
    
    @staticmethod
    def generate_recommendations(locomotive):
        """Generate maintenance recommendations"""
        recommendations = []
        
        # Age-based recommendations
        if locomotive.age > 25:
            recommendations.append({
                'type': 'Major Overhaul',
                'priority': 'High',
                'description': 'Locomotive age exceeds 25 years - major overhaul recommended',
                'estimated_cost': 'High',
                'timeframe': '30-60 days'
            })
        elif locomotive.age > 20:
            recommendations.append({
                'type': 'Engine Inspection',
                'priority': 'Medium',
                'description': 'Comprehensive engine inspection due to age',
                'estimated_cost': 'Medium',
                'timeframe': '7-14 days'
            })
        
        # Usage-based recommendations
        if locomotive.operating_hours > 60000:
            recommendations.append({
                'type': 'Transmission Overhaul',
                'priority': 'High',
                'description': 'High operating hours - transmission overhaul needed',
                'estimated_cost': 'High',
                'timeframe': '14-30 days'
            })
        elif locomotive.operating_hours > 40000:
            recommendations.append({
                'type': 'Transmission Service',
                'priority': 'Medium',
                'description': 'Transmission service recommended',
                'estimated_cost': 'Medium',
                'timeframe': '3-7 days'
            })
        
        # Maintenance history recommendations
        if not locomotive.last_maintenance:
            recommendations.append({
                'type': 'Routine Maintenance',
                'priority': 'High',
                'description': 'No maintenance record - immediate inspection needed',
                'estimated_cost': 'Low',
                'timeframe': '1-3 days'
            })
        else:
            days_since_maintenance = (datetime.now().date() - locomotive.last_maintenance).days
            if days_since_maintenance > 90:
                recommendations.append({
                    'type': 'Overdue Maintenance',
                    'priority': 'High',
                    'description': f'Maintenance overdue by {days_since_maintenance - 90} days',
                    'estimated_cost': 'Medium',
                    'timeframe': '1-7 days'
                })
            elif days_since_maintenance > 60:
                recommendations.append({
                    'type': 'Scheduled Maintenance',
                    'priority': 'Medium',
                    'description': 'Routine maintenance due soon',
                    'estimated_cost': 'Low',
                    'timeframe': '7-14 days'
                })
        
        # Risk-based recommendations
        risk_score = locomotive.calculate_risk_score()
        if risk_score > 70:
            recommendations.append({
                'type': 'Comprehensive Inspection',
                'priority': 'High',
                'description': 'High risk score - comprehensive inspection required',
                'estimated_cost': 'Medium',
                'timeframe': '3-7 days'
            })
        
        return recommendations
    
    def __repr__(self):
        return f'<Prediction {self.id} for Locomotive {self.locomotive_id}>'
