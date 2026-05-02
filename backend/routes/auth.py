# backend/routes/auth.py
from flask import Blueprint, request, jsonify
from db import get_firebase_ref
from utils.auth_utils import generate_token
from datetime import datetime, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/test', methods=['GET'])
def test_route():
    return jsonify({"status": "Auth Blueprint is LIVE"}), 200

# =====================================================
# 1️⃣ REGISTER ROUTE (Cloud-Native)
# =====================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    email = data.get('email', '').strip()
    role = data.get('role')
    password = data.get('password')
    
    # 🚨 ADMIN DOMAIN RULE
    if email and email.endswith('@raktasetu2026.com'):
        role = 'admin'

    # Generate a unique string ID for Firebase
    user_id = str(uuid.uuid4())[:8] 

    try:
        users_ref = get_firebase_ref('users')
        
        # Check if email exists
        all_users = users_ref.get()
        if all_users:
            for uid, info in all_users.items():
                if info.get('email') == email:
                    return jsonify({'message': 'Email already registered in the system!'}), 400

        # Logic for initial verification status
        # Donors/Admins are auto-verified. Hospitals/Banks need Admin approval.
        is_verified = True
        if role in ['hospital', 'bank']:
            is_verified = False

        # Create the data payload
        user_payload = {
            'id': user_id,
            'full_name': data.get('name'),
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role,
            'location': data.get('location', 'Mumbai'),
            'pincode': data.get('pincode', 'N/A'),
            'bloodType': data.get('bloodType', 'N/A'),
            'phone': data.get('phone', 'Not Set'), 
            'verified': is_verified,
            'points': 20 if role == 'donor' else 0,              
            'totalDonations': 0,          
            'credits': 100.0 if role in ['hospital', 'bank'] else 0.0,
            'created_at': str(datetime.now(timezone.utc))
        }

        # 1. Save to main users table
        users_ref.child(user_id).set(user_payload)

        # 2. Save to role-specific node
        get_firebase_ref(f'{role}s/{user_id}').set(user_payload)

        # 3. 🔥 SYNC LIVE STATUS
        get_firebase_ref(f'status/{role}s/{user_id}').set({
            'name': data.get('name'),
            'online': True,
            'last_active': str(datetime.now(timezone.utc))
        })

        return jsonify({
            'message': f'Registration successful as {role.upper()}!',
            'verified': is_verified
        }), 201

    except Exception as e:
        print(f"❌ Firebase Register Error: {e}")
        return jsonify({'message': f'Cloud Registration failed: {str(e)}'}), 500

# =====================================================
# 2️⃣ LOGIN ROUTE (Cloud-Native)
# =====================================================
@auth_bp.route('/login', methods=['POST'], strict_slashes=False)
def login():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    email = data.get('email', '').strip()
    password = data.get('password')

    try:
        users_ref = get_firebase_ref('users')
        users = users_ref.get()

        if not users:
            return jsonify({'message': 'Network empty. Please register.'}), 404

        for uid, user_info in users.items():
            if user_info.get('email') == email:
                if check_password_hash(user_info.get('password_hash'), password):
                    user_role = user_info.get('role')
                    
                    get_firebase_ref(f'status/{user_role}s/{uid}').update({
                        'online': True,
                        'last_login': str(datetime.now(timezone.utc))
                    })
                    
                    token = generate_token(uid, user_role)
                    return jsonify({
                        'token': token,
                        'role': user_role,
                        'name': user_info.get('full_name') or user_info.get('name'),
                        'user_id': uid,
                        'verified': user_info.get('verified', False)
                    }), 200

        return jsonify({'message': 'Access Denied: Invalid Credentials'}), 401
    except Exception as e:
        return jsonify({'message': f'Cloud Authentication failed: {str(e)}'}), 500

# =====================================================
# 3️⃣ UPDATE PROFILE ROUTE (Identity Sync)
# =====================================================
@auth_bp.route('/update_profile', methods=['POST'])
def update_profile():
    data = request.get_json()
    uid = data.get('user_id')
    
    if not uid:
        return jsonify({"message": "User ID missing"}), 400

    try:
        user_node = get_firebase_ref(f'users/{uid}').get()
        if not user_node:
            return jsonify({"message": "Node ID not found"}), 404
        
        user_role = user_node.get('role')

        update_data = {
            'full_name': data.get('full_name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'location': data.get('location'),
            'pincode': data.get('pincode'),
            'bloodType': data.get('bloodType')
        }
        
        # Filter out None values
        update_data = {k: v for k, v in update_data.items() if v is not None}

        get_firebase_ref(f'users/{uid}').update(update_data)
        if user_role:
             get_firebase_ref(f'{user_role}s/{uid}').update(update_data)

        return jsonify({"message": "Identity synchronized successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500