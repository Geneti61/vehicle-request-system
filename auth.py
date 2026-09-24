import streamlit as st

st.write("DEBUG: auth.py loaded")
from config import USERS
st.write("DEBUG: USERS found:", list(USERS.keys()))

def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.user_role = None

def login(email, password):
    email_clean = email.strip().lower()
    st.write("DEBUG: looking for:", email_clean)
    for stored_email, user_data in USERS.items():
        st.write("DEBUG: comparing to:", stored_email.strip().lower())
        if stored_email.strip().lower() == email_clean:
            st.write("DEBUG: email match! password in file:", user_data["password"], "| password entered:", password)
            if user_data["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = stored_email
                st.session_state.user_name = user_data["name"]
                st.session_state.user_role = user_data["role"]
                return True
    return False

def logout():
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
    if not is_logged_in():
        st.error("🔒 Please log in first.")
        st.stop()
    if st.session_state.user_role != role:
        st.error(f"🚫 Access denied. This page is for **{role}** only.")
        st.stop()

def show_login_page():
    st.title("🚚 EPSS Fleet Management System")
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
        st.caption("Demo password: **1234**")
