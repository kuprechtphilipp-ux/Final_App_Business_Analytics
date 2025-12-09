"""
Main Application Router
=======================

This file controls the navigation flow of the entire Streamlit app.

Key responsibilities:
- Initialize session state (login status, selected page)
- Route users to Home/Login if not authenticated
- Route authenticated users to the dashboard pages
- Provide global sidebar navigation for logged-in sessions

No business logic is implemented here. Only UI flow control.
"""

import streamlit as st

# Page imports
from home import home_page
from login import login_page
from pages.profile_page import profile_page
from pages.airbnb_page import airbnb_page
from pages.renting_page import renting_page
from pages.comparison_page import comparison_page


# ------------------------------------------------------------
# Initialize Session State
# ------------------------------------------------------------
def _init_session():
    """Initialize required session state keys."""
    defaults = {
        "logged_in": False,
        "page": "home",
        "username": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ------------------------------------------------------------
# Sidebar Navigation (only when logged in)
# ------------------------------------------------------------
def _dashboard_sidebar():
    """Render the sidebar navigation for authenticated users."""
    with st.sidebar:
        LOGO_PATH = "images/app_logo.png"
        try:
            st.image(LOGO_PATH, use_container_width=True)
        except FileNotFoundError:
            st.warning("Logo image not found.")

        st.markdown("---")

        return st.radio(
            "Navigation",
            ["Airbnb", "Renting", "Comparison", "Profile"],
            index=["Airbnb", "Renting", "Comparison", "Profile"].index(
                st.session_state.get("page", "Airbnb")
            ),
        )


# ------------------------------------------------------------
# Main Router
# ------------------------------------------------------------
def main():
    """Application entry point."""
    _init_session()

    # -------------------------------------
    # NOT LOGGED IN → Home or Login
    # -------------------------------------
    if not st.session_state["logged_in"]:
        if st.session_state["page"] == "home":
            home_page()
        elif st.session_state["page"] == "login":
            login_page()
        return  # stop here

    # -------------------------------------
    # LOGGED IN → Dashboard
    # -------------------------------------
    selected_page = _dashboard_sidebar()
    st.session_state["page"] = selected_page

    if selected_page == "Airbnb":
        airbnb_page()
    elif selected_page == "Renting":
        renting_page()
    elif selected_page == "Comparison":
        comparison_page()
    elif selected_page == "Profile":
        profile_page()


# ------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
