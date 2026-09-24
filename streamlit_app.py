import streamlit as st

st.title("🔍 TEST MODE")
st.write("If you can see this, streamlit_app.py is loading.")

try:
    from auth import USERS, login
    st.success("✅ auth.py loaded successfully")
    st.write("Users found in auth.py:")
    st.write(list(USERS.keys()))
except Exception as e:
    st.error(f"❌ Failed to load auth.py: {e}")
