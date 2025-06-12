# app/auth.py

import streamlit as st
import os

def show_login_ui():
    """Displays the login form and handles authentication."""
    # Updated title
    st.title("Welcome To Kangenx")
    st.markdown("Please log in to continue.")

    # Get correct credentials from environment variables
    correct_username = os.getenv("APP_USERNAME")
    correct_password = os.getenv("APP_PASSWORD")

    if not correct_username or not correct_password:
        st.error("Authentication credentials are not set in the environment. Please contact the administrator.")
        return

    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

        if submitted:
            if username == correct_username and password == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid username or password.")