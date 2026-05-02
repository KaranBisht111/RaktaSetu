from flask import Blueprint, jsonify, request
from utils.blockchain import blood_ledger
from utils.auth_utils import token_required

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/secure_donation', methods=['POST'])
@token_required
def secure_donation(current_user):
    data = request.get_json()
    
    # Information from our Matching Engine
    match_data = {
        "donor_id": data.get('donor_id'),
        "hospital_id": data.get('hospital_id'),
        "blood_type": data.get('blood_type'),
        "match_score": data.get('score')
    }

    # 1. Get the last link in the chain
    last_block = blood_ledger.get_last_block()
    prev_hash = blood_ledger.hash(last_block)

    # 2. Add the Match to the Blockchain
    new_block = blood_ledger.create_block(
        proof=123, # Simplified for your project
        previous_hash=prev_hash,
        data=match_data
    )

    return jsonify({
        "message": "Donation Match secured in Blockchain!",
        "block_index": new_block['index'],
        "block_hash": blood_ledger.hash(new_block)
    }), 201