import streamlit as st

USERS = {
    "gutetajenet1@gmail.com":      {"password": "1234", "name": "Gguta",    "role": "Requester"},
    "demekekerebih27@gmail.com": {"password": "1234", "name": "Dkerebih", "role": "Requester"},
    "mergishoh@gmail.com":       {"password": "1234", "name": "Mhabtamu", "role": "Approver"},
    "girmaabdeta@gmail.com":     {"password": "1234", "name": "Gabdeta",  "role": "Assigner"},
    "nahomgem.ethio@gmail.com":  {"password": "1234", "name": "Nahom",    "role": "Director"},
}
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.user_role = None

def login(email, password):
    email_clean = email.strip().lower()
    st.write("🔎 DEBUG - Looking for:", repr(email_clean))
    st.write("🔎 DEBUG - Stored emails:", [repr(k) for k in USERS.keys()])
    st.write("🔎 DEBUG - Match found?", email_clean in USERS)
    
    if email_clean in USERS:
        stored = USERS[email_clean]["password"]
        st.write("🔎 DEBUG - Stored password:", repr(stored))
        st.write("🔎 DEBUG - Entered password:", repr(password))
        st.write("🔎 DEBUG - Passwords equal?", stored == password)
        if stored == password:
            st.session_state.logged_in = True
            st.session_state.user_email = email_clean
            st.session_state.user_name = USERS[email_clean]["name"]
            st.session_state.user_role = USERS[email_clean]["role"]
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
