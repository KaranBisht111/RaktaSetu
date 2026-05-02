# backend/init_db.py
from app import app
from db import db
import models.user_model
import models.donor_model
import models.hospital_model

with app.app_context():
    db.create_all()
    print("✅ MySQL Tables Created Successfully!")