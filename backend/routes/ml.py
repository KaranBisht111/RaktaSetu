# backend/routes/ml.py
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date
from utils.auth_utils import token_required
from db import get_firebase_ref 
from matching_engine import MatchingEngine
import traceback

ml_bp = Blueprint("ml", __name__)

# Helper to fetch user dictionary safely
def get_user_data(uid):
    return get_firebase_ref(f'users/{uid}').get()

# 🛡️ DATA SAFEGUARD: Prevents crashes from empty Firebase fields
def safe_int(value, default):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(value)) 
    except (ValueError, TypeError):
        return default

# 🛡️ XGBOOST FORMATTER: Translates text gender to notebook numbers
def get_gender_encoded(gender_str):
    if not gender_str:
        return 0 # Default Male
    g = str(gender_str).strip().lower()
    if g == 'female' or g == 'f':
        return 1
    elif g == 'other' or g == 'o':
        return 2
    return 0 # Default Male

# 🛡️ XGBOOST FORMATTER: Translates donations into a Tier Score (1 to 5)
def get_tier_score(total_donations):
    donations = safe_int(total_donations, 0)
    # E.g., Bronze=1, Silver=2, Gold=3, Platinum=4, Diamond=5
    return min(5, max(1, (donations // 2) + 1))



# =====================================================
# 1️⃣ BLOOD DEMAND FORECASTING (LSTM)
# =====================================================
@ml_bp.route("/predict_demand", methods=["POST"])
@token_required
def predict_demand(current_user_id, *args, **kwargs):
    scaler = current_app.demand_scaler
    model = current_app.lstm_model

    if model is None or scaler is None:
        return jsonify({"error": "AI Engine is offline"}), 503

    try:
        data = request.get_json(silent=True) or {}
        history = data.get("history")
        
        # 🚨 FIX: If no history, provide a baseline
        if not history or len(history) < 14:
            history = [21, 19, 25, 22, 28, 24, 30, 26, 29, 23, 27, 31, 25, 28]

        # 🚨 FIX: Force exactly 14 days so the LSTM matrix doesn't crash!
        recent_history = history[-14:]

        city_scale_history = [val * 200 for val in recent_history]
        history_df = pd.DataFrame(city_scale_history, columns=['Units_Demanded'])
        scaled_input = scaler.transform(history_df)
        lstm_input = scaled_input.reshape(1, 14, 1)

        prediction_scaled = model.predict(lstm_input, verbose=0)
        prediction_real = scaler.inverse_transform(prediction_scaled)

        hospital_prediction = float(prediction_real[0][0]) / 200

        return jsonify({"predicted_units": int(abs(hospital_prediction))}), 200

    except Exception as e:
        print(f"❌ Forecast Error: {e}")
        return jsonify({"error": str(e)}), 500


# =====================================================
# 2️⃣ DONOR AVAILABILITY PREDICTION (XGBOOST REGRESSOR)
# =====================================================
@ml_bp.route("/predict_availability", methods=["POST"])
@token_required
def predict_availability(current_user_id, *args, **kwargs):
    user_info = get_user_data(current_user_id)
    if not user_info or user_info.get('role') != "donor":
        return jsonify({"message": "Unauthorized access"}), 403

    try:
        date_str = user_info.get('last_donation_date')
        last_donation = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str and date_str.strip() else date(2000, 1, 1)
        days_since = (date.today() - last_donation).days
        
        # 🚨 FIX: Match Notebook feature names EXACTLY (Case Sensitive)
        feature_names = ['Age', 'Gender_Encoded', 'Tier_Score', 'Days_Since_Donation']
        
        # Safely pull and format data for XGBoost
        age = safe_int(user_info.get('age'), 30)
        gender_enc = get_gender_encoded(user_info.get('gender'))
        total_donations = safe_int(user_info.get('totalDonations'), 0)
        tier_score = safe_int(user_info.get('Tier_Score'), get_tier_score(total_donations))

        features_df = pd.DataFrame([[
            age, 
            gender_enc, 
            tier_score, 
            days_since
        ]], columns=feature_names)
        
        model = current_app.xgb_donor_model
        raw_score = float(model.predict(features_df)[0])
        final_score = raw_score * 100 if raw_score <= 1.0 else raw_score

        return jsonify({"donor_reliability_score": round(final_score, 2), "status": "Analysis Complete"}), 200

    except Exception as e:
        print("❌ predict_availability Error:")
        traceback.print_exc()
        return jsonify({"message": f"Reliability Error: {str(e)}"}), 500


# =====================================================
# 3️⃣ INTELLIGENT DONOR MATCHING (MATCHING ENGINE)
# =====================================================
@ml_bp.route("/match_donors", methods=["POST"])
@token_required
def match_donors(current_user_id, *args, **kwargs):
    data = request.get_json(silent=True) or {}
    blood_type = data.get("blood_type")
    hospital_pincode = safe_int(data.get("hospital_pincode"), 0)

    if not blood_type or hospital_pincode == 0:
        return jsonify({"error": "Missing or invalid search data"}), 400

    try:
        all_users = get_firebase_ref('users').get()
        donors_list = []

        if all_users:
            # 🚨 FIX: Match Notebook feature names EXACTLY (Case Sensitive)
            feature_names = ['Age', 'Gender_Encoded', 'Tier_Score', 'Days_Since_Donation']
            
            for uid, info in all_users.items():
                if info.get('role') == 'donor':
                    
                    date_str = info.get('last_donation_date')
                    last_donation = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str and date_str.strip() else date(2000, 1, 1)
                    actual_days_since = (date.today() - last_donation).days

                    # Safely extract and encode variables
                    age = safe_int(info.get('age'), 25)
                    gender_enc = get_gender_encoded(info.get('gender'))
                    total_donations = safe_int(info.get('totalDonations'), 0)
                    tier_score = safe_int(info.get('Tier_Score'), get_tier_score(total_donations))

                    feat_df = pd.DataFrame([[
                        age,
                        gender_enc,
                        tier_score,
                        actual_days_since
                    ]], columns=feature_names)
                    
                    raw_score = float(current_app.xgb_donor_model.predict(feat_df)[0])
                    prob_val = raw_score if raw_score <= 1.0 else raw_score / 100.0

                    donors_list.append({
                        "Donor_ID": uid,
                        "Name": info.get('full_name') or info.get('name') or "Unknown Donor",
                        "Blood_Type": info.get('bloodType') or info.get('blood_type') or "Unknown",
                        "Location_Pincode": safe_int(info.get('pincode'), 0),
                        "phone": info.get('phone'), 
                        "Predicted_Availability": prob_val, 
                        "Total_Donations": total_donations
                    })

        if not donors_list:
            return jsonify([]), 200 

        donors_df = pd.DataFrame(donors_list)
        matcher = MatchingEngine(donors_df)
        
        ranked_donors = matcher.rank_donors(
            patient_bt=blood_type,
            hospital_pincode=hospital_pincode
        )

        return jsonify(ranked_donors.to_dict(orient="records")), 200

    except Exception as e:
        print("❌ Match Engine Exception Occurred:")
        traceback.print_exc()
        return jsonify({"message": "Server error while ranking donors."}), 500