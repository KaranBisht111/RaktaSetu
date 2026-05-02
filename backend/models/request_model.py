# backend/models/request_model.py
from db import db
from datetime import datetime

class BloodRequest(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    
    # Who is asking?
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    
    # What is needed?
    blood_group = db.Column(db.Enum('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', name='blood_groups'), nullable=False)
    units_required = db.Column(db.Integer, nullable=False)
    
    # How urgent is it? (Used by AI to prioritize)
    urgency = db.Column(db.Enum('Normal', 'Urgent', 'Critical', name='urgency_levels'), default='Normal')
    
    # Where is the emergency? (For the Matching Engine)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # Progress Tracking
    status = db.Column(db.Enum('Pending', 'Fulfilled', 'Cancelled', name='request_status'), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    hospital = db.relationship('Hospital', backref=db.backref('blood_requests', lazy=True))

    def __repr__(self) -> str:
        return f"<Request {self.blood_group} for Hospital {self.hospital_id} - {self.status}>"
    