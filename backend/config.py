# backend/config.py
import os

class Config:
    # 1. Security & Identity
    SECRET_KEY = os.environ.get('SECRET_KEY') or ''
    
    # 2. MySQL Database Connection (Kept for structure, but app now uses Firebase)
    DB_USER = ''
    DB_PASSWORD = '' 
    DB_HOST = ''
    DB_NAME = ''
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 3. Firebase Cloud Configuration (CRITICAL: Matches your Asia-Southeast1 region)
    FIREBASE_DB_URL = ''

    # 4. AI & Machine Learning Paths (Synchronized with your files)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    ML_MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')
    
    # Exact filenames as they exist in your folder
    LSTM_DEMAND_MODEL = os.path.join(ML_MODEL_DIR, 'lstm_demand_model.h5')
    XGB_DONOR_MODEL = os.path.join(ML_MODEL_DIR, 'xgb_donor_model.pkl')
    MATCHING_ENGINE = os.path.join(ML_MODEL_DIR, 'matching_engine.pkl')
    SCALER_PATH = os.path.join(ML_MODEL_DIR, 'demand_scaler.pkl')

    # 5. Blockchain Settings
    BLOCKCHAIN_DIFFICULTY = 2