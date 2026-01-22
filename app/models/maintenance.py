from app import db
from datetime import datetime, date

class MaintenanceRecord(db.Model):
    __tablename__ = 'lpps_maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    locomotive_id = db.Column(db.Integer, db.ForeignKey('lpps_locomotives.id'), nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)  # 'routine', 'repair', 'overhaul'
    description = db.Column(db.Text, nullable=False)
    performed_by = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    cost = db.Column(db.Float)
    parts_replaced = db.Column(db.Text)  # JSON list of parts
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('lpps_users.id'), nullable=False)
    
    def __init__(self, locomotive_id, maintenance_type, description, performed_by, 
                 start_date, end_date=None, cost=None, parts_replaced=None, 
                 notes=None, created_by=None):
        self.locomotive_id = locomotive_id
        self.maintenance_type = maintenance_type
        self.description = description
        self.performed_by = performed_by
        self.start_date = start_date
        self.end_date = end_date
        self.cost = cost
        self.parts_replaced = parts_replaced
        self.notes = notes
        self.created_by = created_by
    
    @property
    def duration_days(self):
        """Calculate maintenance duration in days"""
        if self.end_date:
            return (self.end_date - self.start_date).days
        return (date.today() - self.start_date).days
    
    @property
    def is_completed(self):
        """Check if maintenance is completed"""
        return self.end_date is not None
    
    @property
    def status(self):
        """Get maintenance status"""
        if self.is_completed:
            return 'Completed'
        elif self.duration_days > 30:
            return 'Overdue'
        else:
            return 'In Progress'
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.id} for Locomotive {self.locomotive_id}>'
