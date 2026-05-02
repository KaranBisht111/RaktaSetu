# backend/models/donor_model.py
from db import db

class Donor(db.Model):
    """
    Firebase-Native Donor Model.
    We inherit from db.Model (which is now a Mock object) to prevent import errors,
    but we use a standard constructor to handle Firebase JSON data.
    """
    # Table name kept for internal reference, though not used by Firebase
    __tablename__ = "donors"

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.user_id = data.get('user_id')
            
            # Blood details for AI Matching
            self.blood_type = data.get('bloodType') or data.get('blood_type', 'N/A')
            self.last_donation_date = data.get('last_donation_date')
            
            # Location for the Live Map
            self.city = data.get('location') or data.get('city', 'Mumbai')
            self.latitude = data.get('latitude', 19.0760)
            self.longitude = data.get('longitude', 72.8777)
            
            # Reward System
            self.points = data.get('points', 0)
            self.total_donations = data.get('totalDonations', 0)

    def __repr__(self) -> str:
        return f"<Donor {self.blood_type} at {self.city}>"