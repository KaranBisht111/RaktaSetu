# backend/routes/inventory.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from db import db
from utils.auth_utils import token_required
from models.hospital_model import Hospital
from models.inventory_model import Inventory as BloodInventory
from models.user_model import User

inventory_bp = Blueprint('inventory', __name__)

# =====================================================
# GET: Fetch current hospital/bank's blood inventory
# =====================================================
@inventory_bp.route('/', methods=['GET'])
@token_required
def get_inventory(current_user: User):
    """
    Get all blood inventory details for the logged-in hospital or blood bank.
    """
    try:
        # Validate role
        if current_user.role not in ('hospital', 'bank'):
            return jsonify({'message': 'Unauthorized access — only hospitals or banks allowed'}), 403

        # Get hospital/bank profile
        hospital_profile = Hospital.query.filter_by(user_id=current_user.id).first()
        if not hospital_profile:
            return jsonify({'message': 'Hospital or bank profile not found'}), 404

        # Get all blood inventory records
        inventory_items = BloodInventory.query.filter_by(hospital_id=hospital_profile.id).all()

        # Serialize data
        inventory_data = [
            {
                'id': item.id,
                'blood_type': item.blood_type,
                'quantity_in_units': item.quantity_in_units,
                'last_updated': (
                    item.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                    if item.last_updated else None
                ),
            }
            for item in inventory_items
        ]

        return jsonify(inventory_data), 200

    except SQLAlchemyError as e:
        print(f"[DB ERROR] Fetch inventory failed: {e}")
        return jsonify({'message': 'Database error occurred while fetching inventory.'}), 500
    except Exception as e:
        print(f"[ERROR] Unexpected issue in get_inventory: {e}")
        return jsonify({'message': 'Internal server error occurred.'}), 500


# =====================================================
# POST: Add or update blood inventory
# =====================================================
@inventory_bp.route('/', methods=['POST'])
@token_required
def manage_inventory(current_user: User):
    """
    Add or update blood inventory for a hospital or blood bank.
    """
    try:
        # Validate role
        if current_user.role not in ('hospital', 'bank'):
            return jsonify({'message': 'Unauthorized access — only hospitals or banks allowed'}), 403

        # Get hospital/bank profile
        hospital_profile = Hospital.query.filter_by(user_id=current_user.id).first()
        if not hospital_profile:
            return jsonify({'message': 'Hospital or bank profile not found'}), 404

        # Get and validate JSON data
        data = request.get_json(silent=True) or {}
        blood_type = str(data.get('blood_type', '')).strip()
        quantity_raw = data.get('quantity')

        if not blood_type:
            return jsonify({'message': 'Blood type is required.'}), 400

        try:
            quantity = int(quantity_raw)
            if quantity < 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({'message': 'Quantity must be a non-negative integer.'}), 400

        # --- Database Operations ---
        inventory_item = BloodInventory.query.filter_by(
            hospital_id=hospital_profile.id,
            blood_type=blood_type
        ).first()

        if inventory_item:
            # Update existing record
            inventory_item.quantity_in_units = quantity
            inventory_item.last_updated = datetime.utcnow()
            action = "updated"
        else:
            # Create new record
            new_item = BloodInventory(
                hospital_id=hospital_profile.id,
                blood_type=blood_type,
                quantity_in_units=quantity,
                last_updated=datetime.utcnow()
            )
            db.session.add(new_item)
            action = "added"

        db.session.commit()
        return jsonify({'message': f'Inventory {action} successfully.'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR] Inventory update failed: {e}")
        return jsonify({'message': 'Database error occurred during update.'}), 500
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Unexpected issue in manage_inventory: {e}")
        return jsonify({'message': 'Internal server error occurred.'}), 500
