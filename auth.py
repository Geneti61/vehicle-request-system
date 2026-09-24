# ============================================================
# EPSS Vehicle System - Authentication
# Login, logout, and role-based access
# ============================================================

import streamlit as st
from config import USERS


def init_session():
    """Initialize session state on first load."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.user_role = None


def login(email, password):
    """Check credentials and log the user in."""
    email = email.strip().lower()
    if email in USERS and USERS[email]["password"] == password:
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.user_name = USERS[email]["name"]
        st.session_state.user_role = USERS[email]["role"]
        return True
    return False


def logout():
    """Clear session and log out."""
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.user_role = None


def is_logged_in():
    return st.session_state.get("logged_in", False)


def current_user():
    return {
        "email": st.session_state.get("user_email"),
        "name": st.session_state.get("user_name"),
        "role": st.session_state.get("user_role"),
    }


def require_role(role):
    """Stop the page if the user does not have the required role."""
    if not is_logged_in():
        st.error("🔒 Please log in first.")
        st.stop()
    if st.session_state.user_role != role:
        st.error(f"🚫 Access denied. This page is for **{role}** only.")
        st.stop()


def show_login_page():
    """Render the login form."""
    st.title("🚚 EPSS Fleet Management System")
    st.caption("Ethiopian Pharmaceutical Supply Service — Vehicle Request & Approval")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True, type="primary"):
            if login(email, password):
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")

        st.caption("Demo password for all users: **1234**")
