
import streamlit as st
from auth import init_session, is_logged_in, show_login_page, current_user, logout
from persistence import load_requests, save_requests

st.set_page_config(
    page_title="EPSS Vehicle System",
    page_icon="🚛",
    layout="wide"
)

init_session()

# ============================================================
# LOAD REQUESTS FROM GOOGLE SHEET (only once per session)
# ============================================================
if "requests_loaded" not in st.session_state:
    st.session_state.requests = load_requests()
    st.session_state.requests_loaded = True

if not is_logged_in():
    show_login_page()
    st.stop()

user = current_user()
role = user["role"]

# ============================================================
# HIDE UNWANTED PAGES BY ROLE
# ============================================================
HIDE_BY_ROLE = {
    "Requester": ["approver", "logistics", "director"],
    "Approver":  ["requester", "logistics", "director"],
    "Assigner":  ["requester", "approver", "director"],
    "Director":  ["requester", "approver", "logistics"],
}

to_hide = HIDE_BY_ROLE.get(role, [])

if to_hide:
    css_rules = ""
    for page in to_hide:
        css_rules += f"""
        [data-testid="stSidebarNav"] a[href*="{page}"] {{ display: none !important; }}
        """
    st.markdown(f"<style>{css_rules}</style>", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🚚 EPSS System")
    st.write(f"**{user['name']}**")
    st.write(f"Role: `{role}`")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

# ============================================================
# HOME
# ============================================================
st.title("🚛 Vehicle Request and Approval System")
st.success(f"✅ Welcome, **{user['name']}**! You are logged in as **{role}**.")
st.info("👈 Use the sidebar to navigate to your pages.")
