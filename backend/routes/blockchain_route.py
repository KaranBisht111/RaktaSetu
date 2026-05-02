import time
import hashlib
from flask import Blueprint, jsonify, request
from utils.blockchain import blood_ledger

blockchain_bp = Blueprint('blockchain_view', __name__)

@blockchain_bp.route('/get_chain', methods=['GET'])
def get_chain():
    """
    Returns the full blockchain and its current validity status.
    """
    response = {
        'chain': blood_ledger.chain,
        'length': len(blood_ledger.chain),
        'is_valid': blood_ledger.is_chain_valid()
    }
    return jsonify(response), 200

@blockchain_bp.route('/validate_chain', methods=['GET'])
def validate():
    """
    Manually triggers a security check on the ledger.
    """
    valid = blood_ledger.is_chain_valid()
    if valid:
        return jsonify({'message': 'Blockchain is secure. No tampering detected.'}), 200
    else:
        return jsonify({'message': 'Security Alert! Blockchain integrity compromised.'}), 500

@blockchain_bp.route('/generate_hash', methods=['POST'])
def generate_hash():
    """
    Generates a true SHA-256 cryptographic hash for a new marketplace transaction.
    """
    try:
        data = request.json
        sender = data.get('from_hub', 'Unknown')
        receiver = data.get('to_hub', 'Unknown')
        payload = data.get('payload', '')
        
        # Generate an exact UNIX timestamp (in milliseconds)
        timestamp = str(int(time.time() * 1000)) 

        # Concatenate the transaction data into a single string block
        block_data = f"{sender}|{receiver}|{payload}|{timestamp}"
        
        # Generate the true SHA-256 cryptographic hash
        secure_hash = "blk_" + hashlib.sha256(block_data.encode('utf-8')).hexdigest()[:32]
        
        return jsonify({
            "hash": secure_hash,
            "timestamp": int(timestamp)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500