# backend/utils/ml_models.py

import os
import sys
import pickle
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from models.donor_model import Donor  # Ensure models/__init__.py exists

# ===============================================================
# PATH CONFIGURATION
# ===============================================================

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_PATH = os.path.join(BASE_PATH, "ml_models")


# ===============================================================
# LOAD MODELS (REAL, PRODUCTION-LEVEL)
# ===============================================================

def load_model(filename: str) -> Any:
    """
    Safely loads a real machine learning model (.pkl file)
    from the ml_models directory. Raises clear errors if not found.
    """
    path = os.path.join(ML_PATH, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file '{filename}' not found at {path}")

    # Ensure pickle can resolve cross-module classes
    sys.modules["__main__"] = sys.modules[__name__]
    try:
        with open(path, "rb") as f:
            model = pickle.load(f)
        print(f"[SUCCESS] Loaded model: {filename}")
        return model
    except Exception as e:
        print(f"[ERROR] Could not load model {filename}: {e}")
        raise
    finally:
        # Clean up sys.modules override
        if "__main__" in sys.modules:
            del sys.modules["__main__"]


# ===============================================================
# LOAD ALL TRAINED MODELS
# ===============================================================

try:
    demand_model = load_model("xgboost_demand_model.pkl")
except Exception as e:
    raise RuntimeError(f"Failed to load demand model: {e}")

try:
    donor_model = load_model("xgb_donor_availability_model.pkl")
except Exception as e:
    raise RuntimeError(f"Failed to load donor availability model: {e}")

try:
    matching_model = load_model("matching_engine.pkl")
except Exception as e:
    raise RuntimeError(f"Failed to load matching engine model: {e}")


# ===============================================================
# MATCHING ENGINE WRAPPER (REAL DB-INTEGRATED)
# ===============================================================

class MatchingEngine:
    """
    Intelligent matching engine that integrates with database donors
    and uses machine learning to rank best matches.
    """

    def __init__(self, model):
        self.model = model
        self.compatibility: Dict[str, List[str]] = {
            "A+": ["A+", "A-", "O+", "O-"],
            "O+": ["O+", "O-"],
            "B+": ["B+", "B-", "O+", "O-"],
            "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            "A-": ["A-", "O-"],
            "O-": ["O-"],
            "B-": ["B-", "O-"],
            "AB-": ["A-", "B-", "AB-", "O-"],
        }

    # ------------------------------------------------------------
    # MAIN: FIND MATCHING DONORS
    # ------------------------------------------------------------
    def get_matches(
        self, patient_blood_type: str, requester_location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        compatible_types = self.compatibility.get(patient_blood_type, [])
        if not compatible_types:
            print(f"[WARNING] No compatible donors for {patient_blood_type}")
            return []

        try:
            donors = Donor.query.filter(Donor.blood_type.in_(compatible_types)).all()
        except Exception as e:
            print(f"[DB ERROR] Could not fetch donors: {e}")
            return []

        ranked_results = []
        for donor in donors:
            features = self._extract_features(donor, patient_blood_type, requester_location)
            try:
                # Use trained ML model (e.g. XGBoost / RandomForest)
                score = float(self.model.predict([features])[0])
            except Exception as e:
                print(f"[ML ERROR] Prediction failed for donor {donor.id}: {e}")
                continue

            ranked_results.append({
                "name": donor.full_name,
                "blood_type": donor.blood_type,
                "location": getattr(donor, "location", "N/A"),
                "match_score": round(score, 2),
                "last_donation": (
                    donor.last_donation_date.strftime("%Y-%m-%d")
                    if donor.last_donation_date else "N/A"
                ),
            })

        return sorted(ranked_results, key=lambda x: x["match_score"], reverse=True)[:5]

    # ------------------------------------------------------------
    # FEATURE EXTRACTION (convert donor attributes → ML input)
    # ------------------------------------------------------------
    def _extract_features(
        self, donor: Donor, patient_blood_type: str, requester_location: Optional[str]
    ) -> List[float]:
        """
        Extracts numeric features for the ML model from donor + context.
        This should match your training dataset's feature schema.
        """

        # Example — modify this according to your training features:
        days_since_donation = 999.0
        if donor.last_donation_date:
            days_since_donation = (date.today() - donor.last_donation_date).days

        same_blood = 1.0 if donor.blood_type == patient_blood_type else 0.0
        universal_donor = 1.0 if donor.blood_type == "O-" else 0.0
        same_city = 0.0
        if requester_location and getattr(donor, "location", None):
            if donor.location.strip().lower() == requester_location.strip().lower():
                same_city = 1.0

        # Feature order should match training schema
        return [days_since_donation, same_blood, universal_donor, same_city]


# ===============================================================
# CREATE LIVE MATCHING ENGINE INSTANCE
# ===============================================================

matching_engine = MatchingEngine(matching_model)
