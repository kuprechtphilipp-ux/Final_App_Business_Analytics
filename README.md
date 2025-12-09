📘 README.md
# Airbnb & Renting Pricing Prediction App

## Overview

This project provides a Streamlit-based web application that predicts:

- Airbnb nightly prices  
- Monthly long-term rent prices  

based on:
- Paris arrondissement  
- Room count, bathrooms, amenities  
- Host information  
- Furnishing status  
- Historical market quartiles to determine realistic RMSE-based confidence intervals  

The application combines machine learning models with an intuitive interface.  
All business logic is separated from UI code for maintainability.

---

## Project Structure

root/
│
├── main.py             # Central navigation & routing
├── home.py             # Landing page
├── login.py            # Login & Sign-Up logic
├── computations.py     # ML prediction logic (Airbnb + Renting + KPIs)
│
├── pages/
│ ├── airbnb_page.py    # Airbnb prediction dashboard
│ ├── renting_page.py   # Renting prediction dashboard
│ └── profile_page.py   # User profile editor
│
├── utils/
│ ├── constants.py      # INSEE mapping, arrondissement names, constants
│ ├── helpers.py        # Formatting, CSS utilities
│ └── quartiles.py      # Quartile-based RMSE interval functions
│
├── data/
│ ├── profiles.json     # User profiles (auto-generated)
│ ├── occupancy_arrondissement.csv
│ └── paris.geojson
│
├── ml_models/
│ ├──  predict_airbnb_prices.sav     # ML model files
│ ├──  predict_cost_of_cleaning.sav
│ └── predict_renting_price.sav
│
├── images/
│ ├──  app_logo.png
│ └── logo.png
│
└── README.md

---

## Authentication System

User credentials and profile defaults are stored in `profiles.json`.

Each profile contains:
- Username, password, email  
- Property details (rooms, bathrooms, amenities)  
- Host attributes  
- Arrondissement default  
- Renting attributes  

Login process:
1. User selects **Login** or **Sign Up**
2. Credentials are validated via `validate_user()`
3. On success, `session_state['logged_in'] = True`
4. App navigates to the Airbnb dashboard

Sign-Up automatically logs the user in.

---

## Machine Learning Logic (computations.py)

All prediction logic is in one central file.

Main functions:

| Function | Purpose |
|----------|----------|
| `run_computations_airbnb()` | Predict nightly Airbnb price + cleaning fee |
| `predict_all_arrondissement_prices()` | Generate heatmap data |
| `calculate_price_impact_kpis()` | Baseline → quality → location price breakdown |
| `run_computations_renting()` | Predict monthly long-term rent |
| `airbnb_confidence_interval()` | RMSE-based uncertainty interval (Airbnb) |
| `renting_confidence_interval()` | RMSE-based uncertainty interval (Renting) |

### Quartile RMSE logic (example Airbnb)

| Quartile | Price Range (€) | RMSE |
|----------|-----------------|------|
| Q1       | < 102           | 40.2 |
| Q2       | 102–151         | 40.4 |
| Q3       | 151–239         | 53.0 |
| Q4       | > 239           | 115.5 |

Prediction interval:
lower = predicted_price - RMSE
upper = predicted_price + RMSE

The same structure is used for Renting.

This replaces fixed ±15% ranges and produces realistic confidence intervals.

---

## UI Logic (Streamlit Pages)

### airbnb_page.py
Contains:
- Sidebar with dynamic profile-loaded defaults  
- Price prediction execution  
- RMSE-based confidence intervals  
- Monthly revenue computation  
- Occupancy-based calculations  
- Choropleth map of predicted prices  
- Waterfall chart for price contributions  

### renting_page.py
Contains:
- Sidebar inputs for rooms, arrondissement, furnishing  
- Rent prediction  
- Quartile-based RMSE uncertainty interval  
- Horizontal bar range visualization  

### profile_page.py
Contains:
- User profile editing  
- Expanders to structure information  
- Persistent JSON-based storage  

### home.py
The landing page:
- Logo  
- Short description  
- Login/Signup redirect button  

### main.py
- Initializes Streamlit session state  
- Controls navigation (home → login → dashboard)  
- Renders sidebar navigation when logged in  

---

## Installation & Setup

### 1. Clone the repository

git clone <your_repo_url>
cd <project_folder>

### 2. Install required dependencies

pip install -r requirements.txt

### 3. Run the application

streamlit run main.py

### 4. Data folder requirements

Ensure the `data/` folder contains:

profiles.json # Auto-created if missing
paris.geojson
occupancy_arrondissement.csv
model_airbnb.pkl
model_renting.pkl
model_cleaning.pkl

---

## GeoJSON Map

The Paris heatmap uses:

- `paris.geojson`
- INSEE arrondissement codes (`constants.py`)
- Feature key: `"properties.c_arinsee"`

Used for:
- Displaying predicted Airbnb prices per arrondissement  
- Highlighting user-selected arrondissement 




## 🔎 KPI System (Price Impact Breakdown)

The Airbnb price prediction is decomposed into three interpretable components using controlled model simulations:

### **1. Baseline Price**
Price of a minimal-quality listing in the **median arrondissement**, defined by:
- 1 bedroom  
- 1 bathroom  
- No amenities  
- Not a superhost  
- Minimal host activity  

Serves as the neutral model reference.

### **2. Quality Impact**
Measures how much the user's **features and amenities** increase price compared to baseline.

Computed as:
Price(user_quality, median_arrondissement)
− Price(baseline_quality, median_arrondissement)

### **3. Location Impact**
Measures how much the user's **arrondissement** affects price, holding quality constant.

Computed as:
Price(user_quality, user_arrondissement)
− Price(user_quality, median_arrondissement)

### **4. Final Predicted Price**
The sum of:
baseline_price
quality_impact
location_impact

### **Dynamic Amenity Handling**
Amenities are reset dynamically via `label_to_amenity_col`, ensuring the KPI system adapts automatically if new features are added.

### **Purpose**
This breakdown explains:
- How much **location** drives price  
- How much **quality features** drive price  
- Where hosts can improve to increase revenue  

The KPIs feed directly into the **Waterfall Chart** for clear visualization.
