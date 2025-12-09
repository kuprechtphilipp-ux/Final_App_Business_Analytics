"""
Airbnb vs Renting Comparison Page
=================================

This Streamlit module compares the monthly profitability of two strategies:
1) Listing the property on Airbnb
2) Renting it out long-term

The page:
- Loads the user's saved profile defaults
- Allows interactive adjustment of listing parameters
- Runs ML models for nightly Airbnb price and monthly rent
- Computes net income for both strategies
- Visualizes the outcome using KPIs and comparison charts

All prediction and feature-engineering logic lives in computations.py.
This file focuses solely on UI layout, interaction, and visualization.
"""


import pandas as pd
import plotly.express as px
import streamlit as st

from login import load_data
from computations import (
    run_computations_airbnb,
    run_computations_renting,
)

from utils.constants import ARRONDISSEMENT_NAMES


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def fmt(num):
    """Format numbers with thousands separators: 1'000."""
    return f"{num:,.0f}".replace(",", "'")


def _inject_styles():
    """Inject minimal CSS for page styling."""
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
def comparison_page():
    """Render the Airbnb vs Renting comparison dashboard."""
    _inject_styles()

    # ---------------------------------------------------------
    # Load user profile
    # ---------------------------------------------------------
    username = st.session_state.get("username")
    if not username:
        st.error("Please log in to see the comparison.")
        return

    all_users = load_data()
    user_profile = all_users.get(username, {})

    if not user_profile:
        st.error("No profile data found. Please complete your profile first.")
        return

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    st.markdown('<div class="big-title">Airbnb vs Renting</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Compare your monthly profits from Airbnb and long-term renting</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ---------------------------------------------------------
    # Sidebar inputs (Airbnb & Renting)
    # ---------------------------------------------------------
    with st.sidebar:
        st.header("Scenario Inputs")

        st.subheader("General Information")
        city = st.selectbox("City", ["Paris", "Vienna", "Berlin", "Zurich"])

        arrondissement = st.number_input(
            "Arrondissement (1–20)",
            min_value=1,
            max_value=20,
            value=int(user_profile.get("arrondissement", 1)),
        )

        st.subheader("Property Settings")
        room_type_options = ["Entire home/apt", "Private room", "Shared room", "Hotel room"]
        saved_room_type = user_profile.get("room_type", "Entire home/apt")

        room_type = st.selectbox(
            "Property type", room_type_options, index=room_type_options.index(saved_room_type)
        )

        bedrooms = st.number_input(
            "Bedrooms",
            min_value=1,
            max_value=10,
            value=int(user_profile.get("bedrooms", 1)),
        )
        bathrooms = st.number_input(
            "Bathrooms",
            min_value=1,
            max_value=10,
            value=int(user_profile.get("bathrooms", 1)),
        )

        st.caption("Amenities used for Airbnb pricing:")
        amenities_options = [
            "Kitchen", "WiFi", "Bathtub", "Elevator", "Air conditioning",
            "Pets allowed", "TV", "Private entrance", "Balcony", "City skyline view",
        ]

        # Keep only valid saved amenities
        default_amenities = [
            a for a in user_profile.get("amenities", []) if a in amenities_options
        ]
        amenities = st.multiselect("Amenities", amenities_options, default=default_amenities)

        st.subheader("Airbnb Information")
        host_listings_count = st.number_input(
            "Host listings count",
            min_value=0,
            max_value=50,
            value=int(user_profile.get("host_listings_count", 0)),
        )
        host_identity_verified = st.checkbox(
            "Host identity verified", value=bool(user_profile.get("host_identity_verified", False))
        )
        host_is_superhost = st.checkbox(
            "Host is superhost", value=bool(user_profile.get("host_is_superhost", False))
        )

        st.subheader("Occupancy assumption for Airbnb")
        data_occ = pd.read_csv("data/occupancy_arrondissement.csv")
        occ_default = float(
            data_occ.loc[data_occ["Arrondissement"] == int(arrondissement),
                         "Occupancy in percent"].iloc[0]
        )
        occupancy_user = st.slider(
            f"Expected occupancy for arrondissement {arrondissement} (%)",
            min_value=10.0,
            max_value=100.0,
            value=occ_default,
            step=1.0,
        )

        st.subheader("Renting Settings")
        rooms_renting = st.number_input(
            "Number of rooms you rent",
            min_value=bathrooms + bedrooms,
            max_value=10,
            value=bathrooms + bedrooms,
        )
        furnished = st.checkbox("Is the rental furnished?", value=False)

    # ---------------------------------------------------------
    # Run computations
    # ---------------------------------------------------------
    airbnb_data = {
        "host_is_superhost": host_is_superhost,
        "host_listings_count": host_listings_count,
        "host_identity_verified": host_identity_verified,
        "bathrooms": bathrooms,
        "bedrooms": bedrooms,
        "arrondissement": arrondissement,
        "room_type": room_type,
        "amenities": amenities,
    }

    renting_data = {
        "Number of rooms renting": rooms_renting,
        "arrondissement": arrondissement,
        "furnished": furnished,
    }

    # Run models
    run_computations_airbnb(airbnb_data)
    nightly_price = st.session_state.get("user_price_prediction")
    cleaning_cost = st.session_state.get("user_cleaning_cost_prediction")

    run_computations_renting(renting_data)
    monthly_rent_price = st.session_state.get("user_renting_price_prediction")

    # ---------------------------------------------------------
    # Compute monthly incomes
    # ---------------------------------------------------------
    occupancy = occupancy_user / 100.0
    monthly_revenue_airbnb = nightly_price * 30 * occupancy
    num_cleanings = (30 * occupancy) / 4.8
    monthly_cleaning_costs = num_cleanings * cleaning_cost
    net_income_airbnb = monthly_revenue_airbnb - monthly_cleaning_costs

    net_income_rent = monthly_rent_price

    # ---------------------------------------------------------
    # Layout: AirbnB vs Rent cards
    # ---------------------------------------------------------
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Airbnb strategy")
        st.metric("Gross monthly revenue", f"€{fmt(monthly_revenue_airbnb)}")
        st.metric("Monthly cleaning costs", f"€{fmt(monthly_cleaning_costs)}")
        st.metric("Net monthly income", f"€{fmt(net_income_airbnb)}")
        st.caption(f"Assuming {occupancy*100:.0f}% occupancy and avg stay of 4.8 nights.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Renting strategy")
        st.metric("Net monthly income", f"€{fmt(net_income_rent)}")
        st.caption("No operating costs modeled (simplified).")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # Summary comparison
    # ---------------------------------------------------------
    diff = net_income_airbnb - net_income_rent
    better = "Airbnb" if diff > 0 else "Renting" if diff < 0 else "Same"

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Which strategy is more profitable?")

    c1, c2 = st.columns(2)
    c1.metric("Difference (Airbnb - Renting)", f"€{fmt(diff)}")
    c2.metric("More attractive strategy", better)

    # Comparison bar chart
    comp_df = pd.DataFrame(
        {
            "Strategy": ["Airbnb", "Renting"],
            "Net monthly income (€)": [net_income_airbnb, net_income_rent],
            "Color": ["Airbnb", "Renting"],
        }
    )

    fig_comp = px.bar(
        comp_df,
        x="Strategy",
        y="Net monthly income (€)",
        color="Color",
        color_discrete_map={
            "Airbnb": "#E57370",
            "Renting": "#808080",
        },
        text="Net monthly income (€)",
        title="Net Monthly Income Comparison",
    )

    fig_comp.update_traces(texttemplate="€%{text:,.0f}", textposition="outside")
    fig_comp.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=550,
    )

    st.plotly_chart(fig_comp, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown('<span class="pill">Comparison Tab</span>', unsafe_allow_html=True)
