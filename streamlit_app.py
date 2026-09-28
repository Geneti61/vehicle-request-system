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
# HIDE UN-AUTHORIZED PAGES FROM SIDEBAR
# ============================================================
all_pages = ["requester", "approver", "logistics", "director", "assigned", "reports"]
for page in all_pages:
    if page not in allowed:
        # Hide the page from the sidebar
        try:
            st.navigation  # newer streamlit
        except Exception:
            pass

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🚚 EPSS System")
    st.write(f"**{user['name']}**")
    st.write(f"Role: `{role}`")
    st.divider()

    # Role-based navigation buttons
    for page in allowed:
        if page == "requester":
            st.page_link("pages/requester.py", label="📝 Requester", icon="📝")
        elif page == "approver":
            st.page_link("pages/approver.py", label="✅ Approver", icon="✅")
        elif page == "logistics":
            st.page_link("pages/logistics.py", label="🚗 Logistics", icon="🚗")
        elif page == "director":
            st.page_link("pages/director.py", label="👔 Director", icon="👔")
        elif page == "assigned":
            st.page_link("pages/assigned.py", label="📋 Assigned Log", icon="📋")
        elif page == "reports":
            st.page_link("pages/reports.py", label="📊 Reports", icon="📊")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

# ============================================================
# HOME CONTENT
# ============================================================
st.title("🚛 Vehicle Request and Approval System")
st.success(f"✅ Welcome, **{user['name']}**! You are logged in as **{role}**.")
st.info("👈 Use the sidebar to navigate to your pages.")
