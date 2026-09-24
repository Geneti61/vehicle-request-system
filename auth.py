def login(email, password):
    """Check credentials and log the user in."""
    email_clean = email.strip().lower()
    
    # Try exact match first, then fall back to cleaned
    for stored_email, user_data in USERS.items():
        if stored_email.strip().lower() == email_clean:
            if user_data["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_email = stored_email
                st.session_state.user_name = user_data["name"]
                st.session_state.user_role = user_data["role"]
                return True
    return False
