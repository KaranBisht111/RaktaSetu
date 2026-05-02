# backend/routes/requests.py

from flask import Blueprint, request, jsonify
from db import get_firebase_ref
import datetime
import uuid

requests_bp = Blueprint("requests", __name__)

# =====================================================
# 1️⃣ CREATE A NEW BLOOD REQUEST (Cloud-Native)
# =====================================================
@requests_bp.route("/raise", methods=["POST"])
def raise_blood_request():
    """
    Allows a donor/user to create a new blood request saved to Firebase.
    """
    data = request.get_json(silent=True) or {}

    # Required fields based on your HTML form
    required_fields = ["patient", "hospital", "group", "units", "urgency", "location"]
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        return jsonify({"message": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        requests_ref = get_firebase_ref('requests')
        
        # We push to generate a unique ID automatically in Firebase
        new_request = requests_ref.push({
            'patient': data["patient"],
            'hospital': data["hospital"],
            'group': data["group"],
            'units': data["units"],
            'urgency': data["urgency"],
            'location': data["location"],
            'status': 'OPEN',
            'timestamp': datetime.datetime.now().timestamp(),
            'created_at': str(datetime.datetime.now())
        })

        return jsonify({
            "message": "Blood request broadcasted successfully!",
            "request_id": new_request.key
        }), 201

    except Exception as e:
        print(f"[CLOUD ERROR] raise_request failed: {e}")
        return jsonify({"message": "Unexpected server error occurred."}), 500


# =====================================================
# 2️⃣ GET ALL BLOOD REQUESTS (Cloud-Native)
# =====================================================
@requests_bp.route("/", methods=["GET"])
def get_all_requests():
    """
    Returns all blood requests from the cloud ledger.
    """
    try:
        requests_ref = get_firebase_ref('requests')
        data = requests_ref.get()

        if not data:
            return jsonify([]), 200

        # Convert Firebase dictionary tree into a list for the frontend tables
        requests_list = []
        for key, val in data.items():
            val['id'] = key # Attach the unique Firebase key
            requests_list.append(val)

        # Sort by timestamp (newest first)
        requests_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        return jsonify(requests_list), 200

    except Exception as e:
        print(f"[CLOUD ERROR] get_all_requests failed: {e}")
        return jsonify({"message": "Error fetching cloud data."}), 500


# =====================================================
# 3️⃣ UPDATE REQUEST STATUS (Cloud-Native)
# =====================================================
@requests_bp.route("/<string:request_id>/status", methods=["PUT"])
def update_request_status(request_id):
    """
    Allows Admin or Hospitals to fulfill/reject a request.
    Valid statuses: Approved, Fulfilled, Rejected
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    valid_statuses = ["Approved", "Fulfilled", "Rejected", "CLOSED"]
    if new_status not in valid_statuses:
        return jsonify({"message": f"Invalid status. Must be one of {valid_statuses}"}), 400

    try:
        # Update the specific node in Firebase
        request_ref = get_firebase_ref(f'requests/{request_id}')
        
        # Check if it exists
        if not request_ref.get():
            return jsonify({"message": "Request not found"}), 404

        request_ref.update({
            "status": new_status,
            "updated_at": str(datetime.datetime.now())
        })

        return jsonify({"message": f"Request status updated to '{new_status}'"}), 200

    except Exception as e:
        print(f"[CLOUD ERROR] update_status failed: {e}")
        return jsonify({"message": "Error updating cloud ledger."}), 500