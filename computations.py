"""
computations.py

Handles ML model loading, feature engineering, prediction routines,
and price-impact KPI generation for Airbnb and renting modules.

This version is cleaned, documented, and uses helpers/constants
from the utils modules to avoid redundancy and improve readability.
"""

import pandas as pd
import numpy as np
import pickle
import streamlit as st

from utils.constants import (
    ARRONDISSEMENT_MAP,
    ARRONDISSEMENT_COLUMNS,
    INSEE_MAP,
    MEDIAN_ARRONDISSEMENT,
)

from utils.helpers import build_amenity_maps


# -------------------------------------------------------------------
# LOAD ML MODELS
# -------------------------------------------------------------------

model_airbnb_price = pickle.load(open("ml_models/predict_airbnb_price.sav", "rb"))
model_cleaning_costs = pickle.load(open("ml_models/predict_cost_of_cleaning.sav", "rb"))
model_renting_price = pickle.load(open("ml_models/predict_renting_price.sav", "rb"))

# Airbnb model input columns (needed for ordering)
airbnb_features = list(model_airbnb_price.feature_names_in_)

# Build amenity maps after loading model features
label_to_amenity_col, amenity_col_to_label = build_amenity_maps(airbnb_features)


# -------------------------------------------------------------------
# FEATURE ENGINEERING
# -------------------------------------------------------------------

def build_airbnb_feature_df(user_profile: dict) -> pd.DataFrame:
    """
    Build a model-ready DataFrame for Airbnb price prediction.

    Parameters
    ----------
    user_profile : dict
        Dictionary of Airbnb-related user inputs.

    Returns
    -------
    pd.DataFrame
        Row-aligned DataFrame matching the ML model's feature order.
    """

    feat = {name: 0 for name in airbnb_features}

    # Basic numeric inputs
    feat["host_is_superhost"] = int(bool(user_profile.get("host_is_superhost", False)))
    feat["host_listings_count"] = int(user_profile.get("host_listings_count", 0))
    feat["host_identity_verified"] = int(bool(user_profile.get("host_identity_verified", False)))
    feat["bathrooms_text"] = int(user_profile.get("bathrooms", 1))
    feat["bedrooms"] = int(user_profile.get("bedrooms", 1))

    # Arrondissement one-hot
    arr_num = int(user_profile.get("arrondissement", 1))
    arr_col = ARRONDISSEMENT_MAP.get(arr_num)
    if arr_col in feat:
        feat[arr_col] = 1

    # Room type one-hot
    room_type = user_profile.get("room_type", "Entire home/apt")
    for rt in ["Entire home/apt", "Hotel room", "Private room", "Shared room"]:
        col = f"room_{rt}"
        if col in feat:
            feat[col] = int(room_type == rt)

    # Amenities one-hot (dynamic)
    for label in user_profile.get("amenities", []) or []:
        model_col = label_to_amenity_col.get(label)
        if model_col in feat:
            feat[model_col] = 1

    # Build DataFrame in exact required column order
    row = [[feat[col] for col in airbnb_features]]
    df = pd.DataFrame(row, columns=airbnb_features)

    # Debug file (unchanged from your version)
    df.to_csv("data/user_dataset_airbnb.csv", index=False)

    return df


def build_renting_feature_df(user_profile: dict) -> pd.DataFrame:
    """
    Build a model-ready DataFrame for renting price prediction.

    Parameters
    ----------
    user_profile : dict
        Dictionary containing renting inputs.

    Returns
    -------
    pd.DataFrame
        Feature DataFrame for the renting model.
    """

    rent_features = [
        "Nombre de pièces principales",
        "Arrondissement_10e", "Arrondissement_11e", "Arrondissement_12e",
        "Arrondissement_13e", "Arrondissement_14e", "Arrondissement_15e",
        "Arrondissement_16e", "Arrondissement_17e", "Arrondissement_18e",
        "Arrondissement_19e", "Arrondissement_1er", "Arrondissement_20e",
        "Arrondissement_2e", "Arrondissement_3e", "Arrondissement_4e",
        "Arrondissement_5e", "Arrondissement_6e", "Arrondissement_7e",
        "Arrondissement_8e", "Arrondissement_9e",
        "Type de locationom_meublé",
        "Type de locationom_non meublé"
    ]

    feat = {name: 0 for name in rent_features}

    # Arrondissement one-hot
    arr_num = int(user_profile.get("arrondissement", 1))
    arr_col = ARRONDISSEMENT_MAP.get(arr_num)
    if arr_col in feat:
        feat[arr_col] = 1

    # Number of rooms
    feat["Nombre de pièces principales"] = user_profile.get("Number of rooms renting")

    # Furnished / unfurnished
    furnished = bool(user_profile.get("furnished", False))
    feat["Type de locationom_meublé"] = int(furnished)
    feat["Type de locationom_non meublé"] = int(not furnished)

    df = pd.DataFrame([[feat[col] for col in rent_features]], columns=rent_features)

    # Debug file
    df.to_csv("data/user_dataset_renting.csv", encoding="utf-8-sig", index=False)

    return df


# -------------------------------------------------------------------
# PREDICTION FUNCTIONS
# -------------------------------------------------------------------

def run_computations_airbnb(user_data: dict):
    """
    Run the Airbnb price prediction pipeline.
    Saves nightly price and cleaning cost predictions into session state.
    """
    df = build_airbnb_feature_df(user_data)

    # Nightly price prediction (log → expm1)
    log_pred = float(model_airbnb_price.predict(df)[0])
    nightly_price = np.expm1(round(log_pred, 4))
    st.session_state["user_price_prediction"] = int(nightly_price)

    # Cleaning cost prediction (log → expm1)
    df_clean = df[['bedrooms', 'bathrooms_text']].copy()
    df_clean.columns = ['Bedroom', 'Bathroom']

    cleaning_pred = float(model_cleaning_costs.predict(df_clean)[0])
    st.session_state["user_cleaning_cost_prediction"] = int(cleaning_pred)


def run_computations_renting(user_data: dict):
    """
    Run renting price prediction pipeline.
    Saves predicted monthly rent into session state.
    """
    df = build_renting_feature_df(user_data)
    pred = float(model_renting_price.predict(df)[0])
    st.session_state["user_renting_price_prediction"] = int(pred)


# -------------------------------------------------------------------
# HEATMAP PRICE PREDICTION FOR ALL ARRONDISSEMENTS
# -------------------------------------------------------------------

def predict_all_arrondissement_prices(user_data: dict) -> pd.DataFrame:
    """
    Predict price for the user's listing across all 20 arrondissements.
    Used for heatmap visualization.

    Returns
    -------
    pd.DataFrame
        Contains arrondissement code, name, and predicted price.
    """

    base_df = build_airbnb_feature_df(user_data)
    results = []

    for arr_num, arr_col in ARRONDISSEMENT_MAP.items():
        df_temp = base_df.copy()

        # Zero out all arrondissement columns
        for c in ARRONDISSEMENT_COLUMNS:
            if c in df_temp:
                df_temp[c] = 0

        # Set only the current arrondissement to 1
        if arr_col in df_temp:
            df_temp[arr_col] = 1

        # Predict nightly price
        log_pred = float(model_airbnb_price.predict(df_temp)[0])
        price = int(np.expm1(log_pred))

        results.append({
            "Arrondissement_Code": str(INSEE_MAP[arr_num]),
            "Avg_Price_Apt": price,
            "Arrondissement_Number": arr_num,
        })

    return pd.DataFrame(results)


# -------------------------------------------------------------------
# KPI CALCULATION
# -------------------------------------------------------------------

def calculate_price_impact_kpis(user_data: dict, current_predicted_price: int):
    """
    Calculate KPI deltas for:
    - Location impact (user arrondissement vs. median)
    - Quality impact (quality features vs. baseline)

    Automatically handles any number of amenities based on label_to_amenity_col.
    """

    base_df = build_airbnb_feature_df(user_data)

    # ---------------------------------------------------------
    # 1. Price in median arrondissement
    # ---------------------------------------------------------
    df_median = base_df.copy()

    # Zero all arrondissement one-hot columns
    for col in ARRONDISSEMENT_COLUMNS:
        df_median[col] = 0

    # Set user to the median arrondissement
    median_col = ARRONDISSEMENT_MAP.get(MEDIAN_ARRONDISSEMENT)
    df_median[median_col] = 1

    median_log = float(model_airbnb_price.predict(df_median)[0])
    median_price = int(np.expm1(median_log))

    # ---------------------------------------------------------
    # 2. Baseline quality: NO amenities + minimal quality values
    # ---------------------------------------------------------
    df_base = df_median.copy()

    # Baseline neutral values
    df_base["host_is_superhost"] = 0
    df_base["host_listings_count"] = 1
    df_base["bedrooms"] = 1
    df_base["bathrooms_text"] = 1

    # Zero out ALL amenity columns dynamically
    for amenity_col in label_to_amenity_col.values():
        if amenity_col in df_base.columns:
            df_base[amenity_col] = 0

    baseline_log = float(model_airbnb_price.predict(df_base)[0])
    baseline_price = int(np.expm1(baseline_log))

    # ---------------------------------------------------------
    # 3. KPIs
    # ---------------------------------------------------------
    location_impact = current_predicted_price - median_price
    quality_impact = median_price - baseline_price

    return {
        "location_impact": location_impact,
        "quality_impact": quality_impact,
        "median_location_price": median_price,
        "baseline_price": baseline_price,
    }



# -------------------------------------------------------------------
# Confidence Interval Functions (Quartile-based RMSE)
# -------------------------------------------------------------------

def airbnb_confidence_interval(prediction: float):
    """
    Returns lower/upper bounds for Airbnb price prediction
    based on quartile-specific RMSE values.
    """
    if prediction < 102:
        rmse = 40.20
    elif prediction < 151:
        rmse = 40.44
    elif prediction < 239:
        rmse = 53.07
    else:
        rmse = 115.52

    return prediction - rmse, prediction + rmse


def renting_confidence_interval(prediction: float):
    """
    Returns lower/upper bounds for renting price prediction
    based on quartile-specific RMSE values.
    """
    if prediction < 560.17:
        rmse = 30.29
    elif prediction < 1379.23:
        rmse = 87.73
    elif prediction < 2025.77:
        rmse = 159.46
    else:
        rmse = 191.43

    return prediction - rmse, prediction + rmse
