"""
style.py

Small collection of UI-related helper functions.
Handles CSS injection for Streamlit and minor authentication helpers.
"""

import streamlit as st


def is_authenticated(username: str, password: str) -> bool:
    """
    Very simple placeholder authentication function.
    Replace with a real credential check if needed.

    Returns
    -------
    bool
        True if the provided username/password match the hardcoded demo credentials.
    """
    return username == "admin" and password == "password"


def import_css(css_file: str = "style.css"):
    """
    Inject external CSS into Streamlit from a file.

    Parameters
    ----------
    css_file : str, optional
        Path to the CSS file to load. Default is 'style.css'.

    Notes
    -----
    If the file is missing, an error is displayed in the UI.
    """
    try:
        with open(css_file, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    except FileNotFoundError:
        st.error(f"CSS file '{css_file}' was not found.")
