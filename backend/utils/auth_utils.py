# backend/utils/auth_utils.py
import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from config import Config

def generate_token(user_id, role):
    """Generates a secure JWT token valid for 24 hours."""
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id,
            'role': role
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    except Exception as e:
        return str(e)

def token_required(f):
    """
    Decorator to protect routes. 
    Usage: Put @token_required above any route that needs a login.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check if 'Authorization' header is present
        if 'Authorization' in request.headers:
            # Format: 'Bearer <token>'
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['sub']
        except:
            return jsonify({'message': 'Token is invalid or expired!'}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated