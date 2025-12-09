from app import db
from datetime import datetime

class TrainMovement(db.Model):
    """Model for storing train movement data from monthly graphs"""
    __tablename__ = 'train_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic train information
    train_number = db.Column(db.String(20), nullable=False, index=True)
    locomotive_number = db.Column(db.String(20), nullable=False, index=True)
    
    # Station information
    departure_station = db.Column(db.String(100), nullable=False)
    arrival_station = db.Column(db.String(100), nullable=False)
    
    # Time information
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    
    # Load and capacity information
    load_tons = db.Column(db.Float, nullable=False)
    wagons_count = db.Column(db.Integer, nullable=False)
    axles_count = db.Column(db.Integer, nullable=False)
    net_weight = db.Column(db.Float, nullable=False)
    
    # Distance and route
    distance_km = db.Column(db.Float, nullable=False)
    
    # Additional operational data
    route_type = db.Column(db.String(50))  # e.g., 'Passenger', 'Freight', 'Mixed'
    service_type = db.Column(db.String(50))  # e.g., 'Express', 'Local', 'Goods'
    
    # Data collection metadata
    graph_month = db.Column(db.Integer, nullable=False)  # 1-12
    graph_year = db.Column(db.Integer, nullable=False)
    data_collected_date = db.Column(db.DateTime, default=datetime.utcnow)
    collected_by = db.Column(db.String(100))
    
    # Performance metrics (calculated)
    journey_duration_hours = db.Column(db.Float)  # Calculated from departure/arrival times
    average_speed_kmh = db.Column(db.Float)  # Calculated from distance and duration
    load_efficiency = db.Column(db.Float)  # Calculated load vs capacity ratio
    
    # Status and validation
    status = db.Column(db.String(20), default='Active')  # Active, Cancelled, Delayed
    is_validated = db.Column(db.Boolean, default=False)
    validation_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrainMovement {self.train_number} - {self.departure_station} to {self.arrival_station}>'
    
    def calculate_metrics(self):
        """Calculate performance metrics from the movement data"""
        if self.departure_time and self.arrival_time:
            duration = self.arrival_time - self.departure_time
            self.journey_duration_hours = duration.total_seconds() / 3600
            
            if self.distance_km and self.journey_duration_hours > 0:
                self.average_speed_kmh = self.distance_km / self.journey_duration_hours
        
        # Calculate load efficiency (assuming standard wagon capacity)
        if self.wagons_count > 0:
            # Assuming average wagon capacity of 50 tons
            total_capacity = self.wagons_count * 50
            self.load_efficiency = (self.load_tons / total_capacity) * 100 if total_capacity > 0 else 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'train_number': self.train_number,
            'locomotive_number': self.locomotive_number,
            'departure_station': self.departure_station,
            'arrival_station': self.arrival_station,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'load_tons': self.load_tons,
            'wagons_count': self.wagons_count,
            'axles_count': self.axles_count,
            'net_weight': self.net_weight,
            'distance_km': self.distance_km,
            'journey_duration_hours': self.journey_duration_hours,
            'average_speed_kmh': self.average_speed_kmh,
            'load_efficiency': self.load_efficiency,
            'status': self.status,
            'graph_month': self.graph_month,
            'graph_year': self.graph_year,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_monthly_summary(year, month):
        """Get summary statistics for a specific month"""
        movements = TrainMovement.query.filter_by(
            graph_year=year, 
            graph_month=month
        ).all()
        
        if not movements:
            return None
            
        total_movements = len(movements)
        total_distance = sum(m.distance_km for m in movements)
        total_load = sum(m.load_tons for m in movements)
        avg_speed = sum(m.average_speed_kmh or 0 for m in movements) / total_movements
        
        return {
            'total_movements': total_movements,
            'total_distance': total_distance,
            'total_load': total_load,
            'average_speed': avg_speed,
            'unique_trains': len(set(m.train_number for m in movements)),
            'unique_locomotives': len(set(m.locomotive_number for m in movements))
        }
