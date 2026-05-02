import os
# --- SILENCE TENSORFLOW LOGS ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import joblib
import tensorflow as tf
import webbrowser
import datetime
import time
import hashlib
import sys
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from firebase_admin import db

# 1. Class persistence for AI Models
try:
    from matching_engine import MatchingEngine
    sys.modules['__main__'].MatchingEngine = MatchingEngine
except ImportError:
    print("⚠️ Warning: matching_engine.py not found. Matching features may fail.")

# 2. Import configurations and Cloud-init functions
from config import Config
from db import init_firebase, init_blockchain

def load_model_safe(file_path):
    try:
        if os.path.exists(file_path):
            return joblib.load(file_path)
        print(f"⚠️ Model file not found at: {file_path}")
        return None
    except Exception as e:
        print(f"⚠️ Model Load Error ({file_path}): {e}")
        return None

def create_app():
    # Setup Directories
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    FRONTEND_DIR = os.path.join(ROOT_DIR, 'frontend')

    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
    app.config.from_object(Config)
    CORS(app)

    with app.app_context():
        # 3. Load AI Neural Core
        try:
            print("📡 Initializing Neural Core...")
            
            # Load Scaler
            app.demand_scaler = load_model_safe(app.config['SCALER_PATH'])

            # Load LSTM Model
            if os.path.exists(app.config['LSTM_DEMAND_MODEL']):
                app.lstm_model = tf.keras.models.load_model(
                    app.config['LSTM_DEMAND_MODEL'],
                    compile=False
                )
            else:
                app.lstm_model = None

            # Load Matching Engine & XGBoost
            app.matching_engine = load_model_safe(app.config['MATCHING_ENGINE'])
            app.xgb_donor_model = load_model_safe(app.config['XGB_DONOR_MODEL'])

            print("🧠 AI Models: ONLINE")
        except Exception as e:
            print(f"⚠️ AI Model initialization Warning: {e}")

        # 4. Initialize Cloud Modules
        init_firebase(app)
        init_blockchain()
        print("✅ CLOUD SYSTEMS GO (Firebase & Blockchain Ready)")

    # 5. Static Frontend Routes
    @app.route("/")
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)

    # 6. Global API Routes
    @app.route('/api/search/hospitals', methods=['GET'])
    def search_hospitals():
        query = request.args.get('q', '').lower()
        try:
            users_ref = db.reference('users').get()
            results = []
            if users_ref:
                for uid, info in users_ref.items():
                    if info.get('role') in ['hospital', 'bank']:
                        name = (info.get('full_name') or info.get('name') or "").lower()
                        if query in name:
                            results.append({
                                "name": info.get('full_name') or info.get('name'),
                                "blood": info.get('bloodType', 'Contact Node'),
                                "lat": info.get('latitude', 19.0760),
                                "lng": info.get('longitude', 72.8777)
                            })
            return jsonify(results), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/admin/stats', methods=['GET'])
    def get_admin_stats():
        try:
            users = db.reference('users').get() or {}
            requests = db.reference('requests').get() or {}
            stats = {
                "total_donors": len([u for u in users.values() if u.get('role') == 'donor']),
                "total_nodes": len([u for u in users.values() if u.get('role') in ['hospital', 'bank']]),
                "active_requests": len([r for r in requests.values() if r.get('status') == 'OPEN']),
                "system_status": "Operational"
            }
            return jsonify(stats), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # --- NEW: Secure SHA-256 Blockchain Hashing Endpoint ---
    @app.route('/api/blockchain/generate_hash', methods=['POST'])
    def generate_hash():
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

    # 7. Register Blueprints
    try:
        from routes.ml import ml_bp
        from routes.blockchain_route import blockchain_bp
        from routes.auth import auth_bp
        from routes.requests import requests_bp
        from routes.banks import banks_bp
        from routes.users import users_bp
        from routes.inventory import inventory_bp

        app.register_blueprint(ml_bp, url_prefix="/api/ml")
        app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')
        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(requests_bp, url_prefix="/api/requests")
        app.register_blueprint(banks_bp, url_prefix="/api/marketplace")
        app.register_blueprint(users_bp, url_prefix="/api/users")
        app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
    except ImportError as e:
        print(f"❌ Blueprint Import Error: {e}")

    return app

if __name__ == "__main__":
    app = create_app()
    url = "http://127.0.0.1:5000"

    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        print(f"🚀 Launching RaktaSetu Cloud Node on {url}")
        webbrowser.open(url)

    app.run(debug=True, port=5000)