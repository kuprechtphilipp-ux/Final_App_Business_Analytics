"""
User Profile Page
=================

A cleaner, modern, user-friendly profile editor for Airbnb & Renting settings.

UX Improvements:
- All fields are editable inline (no more dozens of update buttons)
- Changes are stored locally until the user clicks “Save Changes”
- Profile is structured into clear thematic sections
- Uses accordions for better readability
- No logic change: stored JSON structure stays identical
"""

import streamlit as st
import json
import os
from computations import label_to_amenity_col


# ------------------------------------------------------------
# Data Utilities
# ------------------------------------------------------------
PROFILE_DATA_PATH = "data/profiles.json"

if not os.path.exists("data"):
    os.makedirs("data")


def load_profile_data():
    """Load profile JSON data."""
    if os.path.exists(PROFILE_DATA_PATH):
        try:
            with open(PROFILE_DATA_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.warning("Corrupted profile file. Creating a new one.")
            return {}
    return {}


def save_profile_data(data):
    """Save profile JSON data."""
    with open(PROFILE_DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)


# ------------------------------------------------------------
# Main Profile Page
# ------------------------------------------------------------
def profile_page():
    """Render the user profile editor with a modern, user-friendly UX."""
    st.title("Your Profile")

    if "username" not in st.session_state:
        st.error("No username found. Please log in again.")
        return

    username = st.session_state["username"]
    st.subheader(f"Welcome, {username}!")
    st.write("Update your profile to improve the accuracy of predictions.")

    # Load data
    profile_data = load_profile_data()

    # Ensure user exists in JSON
    if username not in profile_data:
        profile_data[username] = {
            "email": "",
            "password": "",
            "host_is_superhost": False,
            "host_listings_count": 0,
            "host_identity_verified": False,
            "bathrooms": 0,
            "bedrooms": 0,
            "arrondissement": 1,
            "room_type": "Private room",
            "num_rooms": 1,
            "amenities": [],
            "Number of rooms renting": 2,
            "furnished": False,
        }
        save_profile_data(profile_data)

    # Work on a temporary copy (UX improvement)
    temp_profile = profile_data[username].copy()

    # ------------------------------------------------------------
    # SECTION 1 — PERSONAL INFORMATION
    # ------------------------------------------------------------
    with st.expander("👤 Personal Information", expanded=True):
        temp_profile["email"] = st.text_input("Email", temp_profile.get("email", ""))
        temp_profile["password"] = st.text_input(
            "Password", temp_profile.get("password", ""), type="password"
        )

    # ------------------------------------------------------------
    # SECTION 2 — HOST SETTINGS
    # ------------------------------------------------------------
    with st.expander("🏡 Airbnb Host Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            temp_profile["host_is_superhost"] = st.checkbox(
                "Superhost?", value=temp_profile.get("host_is_superhost", False)
            )
            temp_profile["host_identity_verified"] = st.checkbox(
                "Identity Verified?", value=temp_profile.get("host_identity_verified", False)
            )

        with col2:
            temp_profile["host_listings_count"] = st.number_input(
                "Number of Listings",
                min_value=0,
                value=temp_profile.get("host_listings_count", 0),
            )

    # ------------------------------------------------------------
    # SECTION 3 — PROPERTY DETAILS
    # ------------------------------------------------------------
    with st.expander("🏠 Airbnb Property Details", expanded=False):
        colA, colB = st.columns(2)

        with colA:
            temp_profile["bedrooms"] = st.number_input(
                "Bedrooms",
                min_value=0,
                value=temp_profile.get("bedrooms", 0),
            )
            temp_profile["bathrooms"] = st.number_input(
                "Bathrooms",
                min_value=0,
                value=temp_profile.get("bathrooms", 0),
            )

        with colB:
            temp_profile["arrondissement"] = st.number_input(
                "Arrondissement (1–20)",
                min_value=1,
                max_value=20,
                value=temp_profile.get("arrondissement", 1),
            )

            room_types = [
                "Entire home/apt",
                "Private room",
                "Shared room",
                "Hotel room",
            ]
            temp_profile["room_type"] = st.selectbox(
                "Room Type",
                room_types,
                index=room_types.index(temp_profile.get("room_type", "Private room")),
            )

        temp_profile["num_rooms"] = st.number_input(
            "Total Rooms in Property",
            min_value=1,
            value=temp_profile.get("num_rooms", 1),
        )

    # ------------------------------------------------------------
    # SECTION 4 — AMENITIES
    # ------------------------------------------------------------
    with st.expander("✨ Amenities", expanded=False):
        available_amenities = list(label_to_amenity_col.keys())
        saved_amenities = temp_profile.get("amenities", [])

        normalized = []
        for a in saved_amenities:
            if a in available_amenities:
                normalized.append(a)
            else:
                for opt in available_amenities:
                    if a.lower() == opt.lower():
                        normalized.append(opt)
                        break

        temp_profile["amenities"] = st.multiselect(
            "Select amenities", available_amenities, default=normalized
        )

    # ------------------------------------------------------------
    # SECTION 5 — RENTING SETTINGS
    # ------------------------------------------------------------
    with st.expander("📘 Renting Settings", expanded=False):
        temp_profile["Number of rooms renting"] = st.number_input(
            "Number of rooms you rent",
            min_value=0,
            value=temp_profile.get("Number of rooms renting", 0),
        )

        temp_profile["furnished"] = st.checkbox(
            "Is the space furnished?", value=temp_profile.get("furnished", False)
        )

    # ------------------------------------------------------------
    # SAVE CHANGES BUTTON
    # ------------------------------------------------------------
    st.divider()
    if st.button("💾 Save All Changes", type="primary"):
        profile_data[username] = temp_profile
        save_profile_data(profile_data)
        st.success("Your profile has been updated successfully!")

    # ------------------------------------------------------------
    # LOGOUT
    # ------------------------------------------------------------
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["email"] = None
        st.session_state["page"] = "home"
        st.success("You have been logged out.")
        st.rerun()
