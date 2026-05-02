# backend/models/transaction_model.py
from db import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    
    # 1. Standard Transfer Details
    sender_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    
    # 2. The Blockchain "Security Seal" ⭐
    # This hash links this record to the previous one in the chain
    block_index = db.Column(db.Integer, nullable=False)
    previous_hash = db.Column(db.String(255), nullable=False)
    current_hash = db.Column(db.String(255), nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to view hospital names in the marketplace
    sender = db.relationship('Hospital', foreign_keys=[sender_id])
    receiver = db.relationship('Hospital', foreign_keys=[receiver_id])

    def __repr__(self) -> str:
        return f"<Transaction Block {self.block_index}: {self.blood_group} Hash:{self.current_hash[:10]}...>"