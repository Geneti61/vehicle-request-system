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

with st.sidebar:
    st.title("🚚 EPSS System")
    st.write(f"**{user['name']}**")
    st.write(f"Role: `{user['role']}`")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

st.title("🚛 Vehicle Request and Approval System")
st.success(f"✅ Welcome, **{user['name']}**! You are logged in as **{user['role']}**.")
st.info("👈 Use the sidebar to navigate. (More pages coming soon.)")
