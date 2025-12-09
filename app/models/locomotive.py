from app import db
from datetime import datetime, date
from sqlalchemy import func

class Locomotive(db.Model):
    __tablename__ = 'locomotives'
    
    id = db.Column(db.Integer, primary_key=True)
    locomotive_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    model = db.Column(db.String(50), nullable=False)
    manufacturing_year = db.Column(db.Integer, nullable=False)
    operating_hours = db.Column(db.Integer, default=0)
    last_maintenance = db.Column(db.Date)
    current_status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    predictions = db.relationship('Prediction', backref='locomotive', lazy='dynamic', cascade='all, delete-orphan')
    maintenance_records = db.relationship('MaintenanceRecord', backref='locomotive', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, locomotive_id, model, manufacturing_year, operating_hours=0, 
                 last_maintenance=None, current_status='active', created_by=None):
        self.locomotive_id = locomotive_id
        self.model = model
        self.manufacturing_year = manufacturing_year
        self.operating_hours = operating_hours
        self.last_maintenance = last_maintenance
        self.current_status = current_status
        self.created_by = created_by
    
    @property
    def age(self):
        """Calculate locomotive age in years"""
        return datetime.now().year - self.manufacturing_year
    
    @property
    def status_display(self):
        """Get formatted status for display"""
        status_map = {
            'active': 'Active',
            'maintenance': 'Under Maintenance',
            'repair': 'Repair Required',
            'retired': 'Retired'
        }
        return status_map.get(self.current_status, self.current_status)
    
    @property
    def status_color(self):
        """Get status color for UI"""
        color_map = {
            'active': 'success',
            'maintenance': 'warning',
            'repair': 'danger',
            'retired': 'secondary'
        }
        return color_map.get(self.current_status, 'secondary')
    
    def calculate_risk_score(self):
        """Calculate failure risk score based on age and usage"""
        age_risk = min(50, self.age * 2)  # Age risk (max 50 points)
        usage_risk = min(30, (self.operating_hours / 1000) * 0.6)  # Usage risk (max 30 points)
        maintenance_risk = 0
        
        # Maintenance risk based on last maintenance date
        if self.last_maintenance:
            days_since_maintenance = (date.today() - self.last_maintenance).days
            maintenance_risk = min(20, days_since_maintenance * 0.2)  # Max 20 points
        else:
            maintenance_risk = 20  # No maintenance record
        
        total_risk = age_risk + usage_risk + maintenance_risk
        return min(100, total_risk)
    
    def get_risk_level(self):
        """Get risk level based on calculated score"""
        score = self.calculate_risk_score()
        if score >= 70:
            return 'High'
        elif score >= 40:
            return 'Medium'
        else:
            return 'Low'
    
    def calculate_reliability(self):
        """Calculate reliability percentage based on age, usage, and maintenance"""
        # Base reliability starts at 100%
        reliability = 100.0
        
        # Age factor (older locomotives have lower reliability)
        age_factor = min(30, self.age * 1.5)  # Max 30% reduction for age
        reliability -= age_factor
        
        # Usage factor (high operating hours reduce reliability)
        usage_factor = min(20, (self.operating_hours / 10000) * 2)  # Max 20% reduction for usage
        reliability -= usage_factor
        
        # Maintenance factor
        if self.last_maintenance:
            days_since_maintenance = (date.today() - self.last_maintenance).days
            if days_since_maintenance > 90:
                maintenance_factor = min(15, (days_since_maintenance - 90) * 0.1)  # Max 15% reduction
                reliability -= maintenance_factor
        else:
            reliability -= 15  # No maintenance record
        
        # Status factor
        if self.current_status == 'repair':
            reliability -= 25
        elif self.current_status == 'maintenance':
            reliability -= 10
        
        # Ensure reliability is between 0 and 100
        return max(0, min(100, reliability))
    
    def get_maintenance_recommendations(self):
        """Get maintenance recommendations based on risk factors"""
        recommendations = []
        score = self.calculate_risk_score()
        
        if self.age > 20:
            recommendations.append({
                'type': 'Engine Overhaul',
                'priority': 'High' if self.age > 25 else 'Medium',
                'description': 'Consider major engine overhaul due to age'
            })
        
        if self.operating_hours > 50000:
            recommendations.append({
                'type': 'Transmission Service',
                'priority': 'High',
                'description': 'Transmission requires major service'
            })
        
        if not self.last_maintenance or (date.today() - self.last_maintenance).days > 90:
            recommendations.append({
                'type': 'Routine Maintenance',
                'priority': 'High',
                'description': 'Overdue for routine maintenance'
            })
        
        if score > 60:
            recommendations.append({
                'type': 'Comprehensive Inspection',
                'priority': 'High',
                'description': 'Full system inspection recommended'
            })
        
        return recommendations
    
    @staticmethod
    def get_fleet_statistics():
        """Get fleet-wide statistics"""
        total = Locomotive.query.count()
        active = Locomotive.query.filter_by(current_status='active').count()
        maintenance = Locomotive.query.filter_by(current_status='maintenance').count()
        repair = Locomotive.query.filter_by(current_status='repair').count()
        retired = Locomotive.query.filter_by(current_status='retired').count()
        
        return {
            'total': total,
            'active': active,
            'maintenance': maintenance,
            'repair': repair,
            'retired': retired,
            'utilization': round((active / total * 100) if total > 0 else 0, 1)
        }
    
    def __repr__(self):
        return f'<Locomotive {self.locomotive_id}>'
