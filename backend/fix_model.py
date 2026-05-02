import joblib
import xgboost as xgb

# Load your current model
model = joblib.load('ml_models/xgb_donor_model.pkl')

# If it's a Booster object, save it properly
if isinstance(model, xgb.Booster):
    model.save_model('ml_models/xgb_donor_model.json')
else:
    # If it's a Scikit-Learn wrapper, just re-save it with current joblib
    joblib.dump(model, 'ml_models/xgb_donor_model.pkl')

print("Model re-saved to current version.")