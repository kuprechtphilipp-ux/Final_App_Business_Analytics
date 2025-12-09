"""
Renting Price Prediction Page
=============================

This Streamlit module predicts the monthly long-term rent for a property
based on location, room count, and furnishing status. It serves as the 
rent-focused counterpart to the Airbnb predictor.

The page:
- Loads user defaults from profile data
- Allows dynamic adjustment of key rental attributes
- Runs the ML model for monthly rent prediction
- Displays KPIs and a simple price range visualization

All computational logic lives in computations.py.
This file manages UI layout, interaction, and chart rendering.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from login import load_data
from computations import run_computations_renting, renting_confidence_interval
from utils.constants import ARRONDISSEMENT_NAMES


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def fmt(num):
    """Format numbers with thousands separators: 1'000."""
    return f"{num:,.0f}".replace(",", "'")


def _inject_styles():
    """Inject minimal CSS for styling."""
    st.markdown(
        """
        <style>
        .big-title { font-size: 36px; font-weight: 800; }
        .subtitle { color: #6b7280; margin-top: -0.25rem; }
        .card {
            border: 1px solid #e5e7eb; border-radius: 12px;
            padding: 18px; background: #242424; color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Main Page
# ---------------------------------------------------------
def renting_page():
    """Render the Renting price prediction dashboard."""
    _inject_styles()

    # ---------------------------------------------------------
    # Load profile defaults
    # ---------------------------------------------------------
    username = st.session_state.get("username")
    all_users = load_data()
    user_profile = all_users.get(username, {}) if username else {}

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    st.markdown('<div class="big-title">Renting Price Predictor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Data-driven monthly renting prediction for optimal profitability</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ---------------------------------------------------------
    # Sidebar inputs
    # ---------------------------------------------------------
    with st.sidebar:
        st.header("Renting Details")

        city = st.selectbox("City", ["Paris", "Vienna", "Berlin", "Zurich"])

        arrondissement = st.number_input(
            "Arrondissement",
            min_value=1,
            max_value=20,
            value=int(user_profile.get("arrondissement", 1)),
        )

        # Default total rooms = bedrooms + bathrooms (a reasonable base)
        default_rooms = int(user_profile.get("bathrooms", 0)) + int(user_profile.get("bedrooms", 0))
        rooms = st.number_input(
            "Number of Rooms",
            min_value=1,
            max_value=10,
            value=max(1, default_rooms),
        )

        furnished = st.checkbox("Is your object furnished?", value=False)

        # Prepare data for model
        user_sidebar_data = {
            "Number of rooms renting": rooms,
            "arrondissement": arrondissement,
            "furnished": furnished,
        }

        # ---------------------------------------------------------
        # Run ML prediction
        # ---------------------------------------------------------
        run_computations_renting(user_sidebar_data)
        prediction_rent_price_user = st.session_state.get("user_renting_price_prediction", 0)

    # ---------------------------------------------------------
    # Main Content: KPIs + Visualization
    # ---------------------------------------------------------
    # Card: Suggested Rent
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Suggested Monthly Rent")

    # Quartile-based RMSE interval
    price_low, price_high = renting_confidence_interval(float(prediction_rent_price_user))

    low_price = max(0, int(price_low))
    high_price = max(low_price + 1, int(price_high))  # ensure range is valid


    kpi1, kpi2 = st.columns([1, 1])
    kpi1.metric("Predicted Monthly Rent", f"€{fmt(prediction_rent_price_user)}")
    kpi2.metric("Potential Range", f"€{fmt(low_price)} – €{fmt(high_price)}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # Price Range Chart
    # ---------------------------------------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Price Range Overview")

    rent_data = pd.DataFrame(
        {
            "Price (€)": [low_price, prediction_rent_price_user, high_price],
            "Category": ["Low End", "Suggested Rate", "High End"],
        }
    )

    fig_rent = px.bar(
        rent_data,
        x="Price (€)",
        y="Category",
        orientation="h",
        color="Category",
        color_discrete_map={
            "Low End": "rgba(107, 114, 128, 0.4)",
            "Suggested Rate": "#E57370",
            "High End": "rgba(107, 114, 128, 0.6)",
        },
        title=f"Predicted Rent in {ARRONDISSEMENT_NAMES.get(arrondissement, 'Selected Area')}",
        text="Price (€)",
    )

    fig_rent.update_traces(texttemplate="€%{text:,.0f}", textposition="outside")
    fig_rent.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(color="white"),
        height=300,
    )

    st.plotly_chart(fig_rent, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # Footer
    # ---------------------------------------------------------
    st.divider()
    st.markdown('<span class="pill">Renting Prediction Tab</span>', unsafe_allow_html=True)


# Allow standalone execution (optional)
if __name__ == "__main__":
    renting_page()
