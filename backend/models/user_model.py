from db import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Identity Fields
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Role System
    role = db.Column(db.Enum('donor', 'hospital', 'bank', 'admin', name='user_roles'), nullable=False)
    
    # Metadata (Updated to use timezone-aware datetime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships (Optional: helps in pulling profile data easily)
    # donor_profile = db.relationship('Donor', backref='user', uselist=False)
    # hospital_profile = db.relationship('Hospital', backref='user', uselist=False)

    def set_password(self, password):
        """Creates a secure hash of the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the plain text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Converts the SQL object to a Dictionary for Frontend JSON responses."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }