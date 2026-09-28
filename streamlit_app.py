import streamlit as st
from auth import init_session, is_logged_in, show_login_page, current_user, logout

st.set_page_config(
    page_title="EPSS Vehicle System",
    page_icon="🚛",
    layout="wide"
)

init_session()

if not is_logged_in():
    show_login_page()
    st.stop()

user = current_user()
role = user["role"]

# ============================================================
# ROLE → ALLOWED PAGES
# ============================================================
PAGES_BY_ROLE = {
    "Requester": ["requester", "assigned", "reports"],
    "Approver":  ["approver", "assigned", "reports"],
    "Assigner":  ["logistics", "assigned", "reports"],
    "Director":  ["director", "assigned", "reports"],
}
allowed = PAGES_BY_ROLE.get(role, ["reports"])

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
