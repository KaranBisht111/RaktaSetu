# backend/db.py
import firebase_admin
from firebase_admin import credentials, db as firebase_db
import os

# 1. THE IMPROVED MOCK: This handles Column, Integer, String, etc.
class MockSQLAlchemy:
    def __init__(self):
        self.Model = object
    
    # This magic method catches db.Column, db.Integer, db.ForeignKey, etc.
    # and returns a dummy function or object so the code doesn't crash.
    def __getattr__(self, name):
        def dummy_func(*args, **kwargs): return None
        return dummy_func

    def init_app(self, app):
        pass

# Create the instance that models import
db = MockSQLAlchemy()

# 2. Global variable for the Blockchain
blockchain_instance = None

def init_firebase(app):
    """Initializes the Real-time Firebase connection."""
    try:
        cred_path = os.path.join(app.root_path, 'serviceAccountKey.json')
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': app.config['FIREBASE_DB_URL']
            })
            print("🔥 Firebase Cloud: CONNECTED")
    except Exception as e:
        print(f"❌ Firebase Initialization Error: {e}")

def init_blockchain():
    """Initializes the Blood Tracking Blockchain."""
    global blockchain_instance
    try:
        from utils.blockchain import BloodBlockchain
        blockchain_instance = BloodBlockchain()
        print("⛓️  Blockchain Ledger: INITIALIZED (Genesis Block Created)")
    except Exception as e:
        print(f"❌ Blockchain Error: {e}")

def get_firebase_ref(path='/'):
    try:
        return firebase_db.reference(path)
    except Exception as e:
        print(f"❌ Firebase Reference Error: {e}")
        return None