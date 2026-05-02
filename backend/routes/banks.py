# backend/routes/banks.py

from flask import Blueprint, request, jsonify

# Using the modular imports from your DB setup
from db import db
from utils.auth_utils import token_required
from models.hospital_model import Hospital
from models.inventory_model import Inventory as BloodInventory
from models.transaction_model import Transaction as MarketplaceTransaction
banks_bp = Blueprint('banks', __name__)

# =====================================================
# 1️⃣ GET MARKETPLACE LISTINGS
# =====================================================
@banks_bp.route('/', methods=['GET'])
@token_required
def get_marketplace_listings(current_user):
    """
    Fetch all available blood units from other hospitals/banks.
    """
    try:
        # Find the hospital profile of the currently logged-in user
        user_hospital = Hospital.query.filter_by(user_id=current_user.id).first()
        if not user_hospital:
            return jsonify({'message': 'User is not associated with a hospital or bank.'}), 403

        # Query all blood inventory, but exclude the user's own hospital
        listings = BloodInventory.query.join(Hospital).filter(Hospital.id != user_hospital.id).all()
        
        marketplace_data = []
        for item in listings:
            if item.quantity_in_units > 0: 
                marketplace_data.append({
                    'inventory_id': item.id,
                    'bank_name': item.hospital.name,
                    'blood_type': item.blood_type,
                    'available_units': item.quantity_in_units,
                    'credits_per_unit': 1 
                })
                
        return jsonify(marketplace_data), 200
    except Exception as e:
        print(f"[ERROR] Marketplace GET failed: {e}")
        return jsonify({'message': 'Failed to load marketplace.'}), 500

# =====================================================
# 2️⃣ REQUEST BLOOD (P2P TRANSACTION)
# =====================================================
@banks_bp.route('/request', methods=['POST'])
@token_required
def request_from_marketplace(current_user):
    """
    Handle the transfer of blood units between two nodes.
    Updates credits and inventory levels.
    """
    data = request.get_json()
    inventory_id = data.get('inventory_id')
    quantity = data.get('quantity')

    if not inventory_id or not quantity or quantity <= 0:
        return jsonify({'message': 'Inventory ID and a valid quantity are required'}), 400

    requester_hospital = Hospital.query.filter_by(user_id=current_user.id).first()
    inventory_item = BloodInventory.query.get(inventory_id)
    
    if not inventory_item:
        return jsonify({'message': 'Inventory item not found'}), 404
        
    provider_hospital = inventory_item.hospital

    # --- Start Atomicity (Transaction) ---
    try:
        credits_needed = 1 * quantity 
        
        # Validation
        if requester_hospital.id == provider_hospital.id:
            return jsonify({'message': "Cannot request from your own bank"}), 400
        if inventory_item.quantity_in_units < quantity:
            return jsonify({'message': f"Only {inventory_item.quantity_in_units} units available"}), 400
        if requester_hospital.credits < credits_needed:
            return jsonify({'message': 'Not enough credits for this transaction'}), 402

        # 1. Update Inventory
        inventory_item.quantity_in_units -= quantity
        
        # 2. Update Credits (The Peer-to-Peer Economy)
        requester_hospital.credits -= credits_needed
        provider_hospital.credits += credits_needed
        
        # 3. Log the transaction in the MySQL Ledger
        new_transaction = MarketplaceTransaction(
            requesting_hospital_id=requester_hospital.id,
            providing_hospital_id=provider_hospital.id,
            blood_type=inventory_item.blood_type,
            units_transferred=quantity,
            credits_exchanged=credits_needed
        )
        db.session.add(new_transaction)
        
        # Final Commit
        db.session.commit()
        
        return jsonify({'message': 'Transaction authorized and ledger updated!', 'credits_used': credits_needed}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Marketplace Transaction failed: {e}")
        return jsonify({'message': 'An error occurred during the transaction.'}), 500