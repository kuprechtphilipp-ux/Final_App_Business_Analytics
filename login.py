"""
Login and Sign-Up Handling

This module is responsible for:
- Loading and saving user profile data from/to profiles.json
- Validating login credentials
- Rendering the Login / Sign-Up UI in Streamlit
- Initializing the basic profile fields on sign-up

Prediction logic is not part of this file.
"""

import json
import os
import streamlit as st
from computations import label_to_amenity_col


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
# Path to the JSON file where user data (profiles) are stored
PROFILES_DATA_PATH = "data/profiles.json"


# -------------------------------------------------------------------
# Data utilities
# -------------------------------------------------------------------
def load_data():
    """
    Load existing user data from the JSON file.

    Returns
    -------
    dict
        A dictionary mapping username -> profile dict.
        Returns an empty dict if file is missing or invalid.
    """
    if os.path.exists(PROFILES_DATA_PATH):
        with open(PROFILES_DATA_PATH, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                # If the file is empty or malformed, start with no users
                return {}
    return {}


def save_data(data: dict):
    """
    Save updated user data to the JSON file.

    Parameters
    ----------
    data : dict
        The full profiles dict to persist.
    """
    with open(PROFILES_DATA_PATH, "w") as file:
        json.dump(data, file, indent=4)


def validate_user(username: str, password: str) -> bool:
    """
    Validate if the username and password are correct.

    Parameters
    ----------
    username : str
        Entered username.
    password : str
        Entered password.

    Returns
    -------
    bool
        True if credentials match an existing user, False otherwise.
    """
    data = load_data()
    return username in data and data[username].get("password") == password


# -------------------------------------------------------------------
# Main UI
# -------------------------------------------------------------------
def login_page():
    """Render the login and sign-up page."""
    st.title("Login Page")

    # Switch between Login and Sign Up modes
    option = st.radio("Choose an option", ["Login", "Sign Up"], index=0)

    # ------------------------------------------------------------------
    # LOGIN MODE
    # ------------------------------------------------------------------
    if option == "Login":
        # Use a form so the login action only triggers on submit
        with st.form(key="login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                if username and password:
                    if validate_user(username, password):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.session_state["page"] = "Airbnb"  # initial dashboard page
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.error("Please fill both username and password fields.")

    # ------------------------------------------------------------------
    # SIGN-UP MODE
    # ------------------------------------------------------------------
    elif option == 'Sign Up':

        st.title("Create Your Account")
        st.write("Please fill out the information below to set up your account.")

        # Use structured accordions to make sign-up cleaner and easier.
        profiles = load_data()

        # ------------------------------------------------------------------
        # Section 1: Account Information
        # ------------------------------------------------------------------
        with st.expander("Account Information", expanded=True):
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            email = st.text_input("Email Address")

        # ------------------------------------------------------------------
        # Section 2: Location
        # ------------------------------------------------------------------
        with st.expander("Location of Your Property"):
            arrondissement = st.number_input(
                "Arrondissement (1 to 20)", 
                min_value=1, max_value=20, step=1
            )

        # ------------------------------------------------------------------
        # Section 3: Property Details
        # ------------------------------------------------------------------
        with st.expander("Property Characteristics"):
            room_type_options = [
                "-- Select property type --",
                "Entire home/apt",
                "Hotel room",
                "Private room",
                "Shared room"
            ]
            room_type = st.selectbox("Object Type", room_type_options)

            if room_type == "Entire home/apt":
                bathrooms = st.number_input(
                    "Number of Bathrooms", min_value=1, value=1
                )
                bedrooms = st.number_input(
                    "Number of Bedrooms", min_value=1, value=1
                )
            elif room_type in ["Hotel room", "Private room", "Shared room"]:
                bathrooms = 1
                bedrooms = 1
            else:
                bathrooms = 1
                bedrooms = 1

            num_rooms = st.number_input(
                "Total number of Rooms", min_value=1, value=1
            )

        # ------------------------------------------------------------------
        # Section 4: Amenities
        # ------------------------------------------------------------------
        with st.expander("Amenities"):
            amenities = st.multiselect(
                "Select Amenities", 
                sorted(list(label_to_amenity_col.keys()))
            )

        # ------------------------------------------------------------------
        # Section 5: Host Information (Optional)
        # ------------------------------------------------------------------
        with st.expander("Airbnb Host Information (Optional)"):
            host_is_superhost = st.checkbox("Superhost")
            host_listings_count = st.number_input(
                "Number of Listings", min_value=0, value=0
            )
            host_identity_verified = st.checkbox("Identity Verified on Airbnb")

        # ------------------------------------------------------------------
        # SIGN-UP BUTTON
        # ------------------------------------------------------------------
        if st.button("Sign Up"):
            # Validation
            if not new_username or not new_password or not email:
                st.error("Please fill in all required fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif room_type == "-- Select property type --":
                st.error("Please choose a valid property type.")
                return
            elif new_username in profiles:
                st.error("Username already exists.")
            else:
                # Create profile entry
                profiles[new_username] = {
                    "email": email,
                    "password": new_password,
                    "host_is_superhost": host_is_superhost,
                    "host_listings_count": host_listings_count,
                    "host_identity_verified": host_identity_verified,
                    "bathrooms": bathrooms,
                    "bedrooms": bedrooms,
                    "arrondissement": arrondissement,
                    "room_type": room_type,
                    "num_rooms": num_rooms,
                    "amenities": amenities,
                }

                # Save profile
                save_data(profiles)

                # Auto-login after sign-up
                st.success(f"Account created for {new_username}!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = new_username
                st.session_state["page"] = "Airbnb"
                st.rerun()

