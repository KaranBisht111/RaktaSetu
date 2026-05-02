# backend/models/hospital_model.py
from db import db

class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    
    # Connects this record to the main User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Official Information
    name = db.Column(db.String(150), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Location for the Matching Engine
    city = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Marketplace Logic
    # Credits are used as "currency" in the Blood Marketplace
    credits = db.Column(db.Integer, default=100)

    # Link back to the User object
    user = db.relationship('User', backref=db.backref('hospital_profile', uselist=False))

    def __repr__(self) -> str:
        return f"<Hospital {self.name} in {self.city}>"