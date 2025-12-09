"""
Home Page

This is the public landing page of the application.
It displays a welcome message, the logo, and a clear call-to-action
for users to log in or sign up. No business logic is handled here.
"""

import streamlit as st


def home_page():
    # Top title
    st.title("Welcome to the airbnb pricing app")
    st.markdown("## Find the optimal price for your flat or room")

    # Logo centered
    logo_path = "images/logo.png"

    with st.container():
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            try:
                st.image(logo_path, width=340)
            except:
                st.warning("Logo not found. Please check the path: images/logo.png")

    # Call-to-action button
    if not st.session_state.get("logged_in", False):
        st.markdown("### Get Started")
        if st.button(
            "Login / Sign Up",
            key="login_signup",
            use_container_width=True,
            help="Proceed to login or create an account"
        ):
            st.session_state["page"] = "login"
            st.rerun()

    # About section
    st.markdown(
        """
        ---
        ## About Our Platform

        Our platform helps you determine the most profitable nightly rate for your Airbnb property.  
        By analyzing location, amenities, occupancy expectations, host status, and market factors,  
        you receive data-driven insights for better pricing decisions.

        Whether you manage a single private room or multiple listings,  
        we help you understand your break-even point, estimate monthly revenue,  
        and compare Airbnb earnings with traditional renting strategies.

        Make confident, informed choices using a streamlined and host-friendly pricing assistant.
        """,
        unsafe_allow_html=True,
    )
