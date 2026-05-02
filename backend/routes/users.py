# backend/routes/users.py
from flask import Blueprint, request, jsonify
from db import db
from models.user_model import User
from models.donor_model import Donor
from utils.auth_utils import token_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    user = User.query.get(user_id)
    donor = Donor.query.filter_by(user_id=user_id).first()
    
    if not donor:
        return jsonify({'message': 'Donor profile not found'}), 404

    return jsonify({
        'full_name': user.full_name,
        'email': user.email,
        'blood_type': donor.blood_type,
        'phone_number': donor.phone_number, # Ensure this column exists in your donors table
        'location': donor.city,
        'total_donations': donor.total_donations, # Ensure this exists
        'points': donor.points
    }), 200

@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    donor = Donor.query.filter_by(user_id=user_id).first()

    if data.get('full_name'): user.full_name = data.get('full_name')
    if data.get('phone_number'): donor.phone_number = data.get('phone_number')
    if data.get('location'): donor.city = data.get('location')

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully!'}), 200