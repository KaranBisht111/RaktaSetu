import pandas as pd
import numpy as np

class MatchingEngine:

    def __init__(self, donors_df):
        """
        Initializes the engine with a DataFrame of current donors from Firebase.
        """
        self.donors = donors_df.copy()

    # ------------------------------------------------------------
    # 1️⃣ Biological Blood Compatibility Logic
    # ------------------------------------------------------------
    def compatibility_score(self, patient_bt, donor_bt):
        # Exact match is priority 1
        if patient_bt == donor_bt:
            return 1.0

        # Standard Red Cross Compatibility Rules
        # Keys are what the Patient CAN RECEIVE
        rules = {
            "O+": ["O-"],
            "A+": ["A-", "O+", "O-"],
            "B+": ["B-", "O+", "O-"],
            "AB+": ["A+", "A-", "B+", "B-", "AB-", "O+", "O-"],
            "A-": ["O-"],
            "B-": ["O-"],
            "AB-": ["A-", "B-", "O-"],
            "O-": [] # Only O- can give to O-
        }

        # Return 0.7 for compatible but not identical, 0.0 for dangerous mismatch
        return 0.7 if donor_bt in rules.get(patient_bt, []) else 0.0

    # ------------------------------------------------------------
    # 2️⃣ Main Ranking Function (AI + Proximity + Biology)
    # ------------------------------------------------------------
    def rank_donors(
        self,
        patient_bt,
        hospital_pincode,
        top_n=5,
        availability_threshold=0.1 # Lowered to ensure results in small pools
    ):
        if self.donors.empty:
            return pd.DataFrame()

        temp_df = self.donors.copy()

        # Step 1: Apply Biological Biological Filter
        temp_df["Comp_Score"] = temp_df["Blood_Type"].apply(
            lambda bt: self.compatibility_score(patient_bt, bt)
        )

        # Drop dangerous mismatches immediately
        eligible = temp_df[temp_df["Comp_Score"] > 0].copy()

        if eligible.empty:
            return pd.DataFrame()

        # Step 2: XGBoost Reliability / Availability Filter
        # Rename column if Firebase uses 'Reliability_Score'
        avail_col = "Predicted_Availability" if "Predicted_Availability" in eligible.columns else "Reliability_Score"
        
        eligible = eligible[eligible[avail_col] >= availability_threshold]

        if eligible.empty:
            return pd.DataFrame()

        # Step 3: Pincode Proximity Logic
        # Convert to int to avoid string vs int comparison errors
        try:
            h_pin = int(hospital_pincode)
            eligible["Location_Pincode"] = eligible["Location_Pincode"].astype(int)
        except:
            h_pin = hospital_pincode

        eligible["Location_Score"] = np.where(
            eligible["Location_Pincode"] == h_pin,
            1.0,  # Same Pincode
            0.4   # Different sector (Mumbai-wide)
        )

        # Step 4: Normalization of Donation Experience
        max_donations = eligible["Total_Donations"].max()
        if max_donations == 0:
            eligible["Donation_Score"] = 0
        else:
            eligible["Donation_Score"] = (eligible["Total_Donations"] / max_donations)

        # Step 5: Final Weighted Decision Matrix
        # Weights: 40% AI Reliability, 30% Biology, 20% Geography, 10% Experience
        eligible["Final_Score"] = (
            0.4 * eligible[avail_col] +
            0.3 * eligible["Comp_Score"] +
            0.2 * eligible["Location_Score"] +
            0.1 * eligible["Donation_Score"]
        )

        # Convert score to percentage for UI display
        eligible["Final_Score"] = (eligible["Final_Score"] * 100).round(2)

        # Sort by best candidates
        ranked = eligible.sort_values(
            "Final_Score", ascending=False
        ).head(top_n)

        # Return relevant columns for the frontend
        return ranked[[
            "Donor_ID",
            "Name",
            "Blood_Type",
            "Location_Pincode",
            avail_col,
            "Final_Score"
        ]]