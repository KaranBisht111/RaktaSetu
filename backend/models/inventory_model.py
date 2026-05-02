# backend/models/inventory_model.py
from db import db
from datetime import datetime

class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    
    # Link to the Hospital that owns this blood
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    
    # Blood details
    blood_group = db.Column(db.Enum('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', name='blood_groups'), nullable=False)
    units = db.Column(db.Integer, default=0)
    
    # Advanced tracking for AI
    expiry_date = db.Column(db.Date, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to get hospital details easily
    hospital = db.relationship('Hospital', backref=db.backref('inventory_stocks', lazy=True))

    def __repr__(self) -> str:
        return f"<Inventory {self.blood_group}: {self.units} units at Hospital {self.hospital_id}>"