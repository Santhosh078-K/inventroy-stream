import streamlit as st
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from db_operations import load_users, save_users

def login_page():
    """Renders the login form and handles user authentication."""
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Remember Me")
        submitted = st.form_submit_button("Login")

        if submitted:
            users = load_users()
            user_data = next((u for u in users if u['username'].lower() == username.lower()), None)

            if user_data and check_password_hash(user_data['password'], password):
                st.session_state.logged_in = True
                st.session_state.username = user_data['username']
                st.session_state.role = user_data['role']
                st.session_state.current_page = 'inventory'
                st.success(f"Logged in successfully as {st.session_state.username} ({st.session_state.role.capitalize()})!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    
    st.markdown("Don't have an account? Navigate to **Register** in the sidebar.")

def register_page():
    """Renders the registration form and handles new user creation."""
    st.subheader("Register")
    with st.form("register_form"):
        username = st.text_input("Username", key="reg_username")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        role = st.selectbox("Role", ["user", "admin"], key="reg_role") 
        submitted = st.form_submit_button("Register")

        if submitted:
            if not username or not password or not confirm_password:
                st.error('All fields are required.')
            elif password != confirm_password:
                st.error('Passwords do not match.')
            elif len(password) < 6:
                st.error('Password must be at least 6 characters long.')
            else:
                users = load_users()
                if any(user['username'].lower() == username.lower() for user in users):
                    st.error('Username already exists. Please choose a different one.')
                else:
                    hashed_password = generate_password_hash(password) 
                    new_user = {
                        'id': str(uuid.uuid4()),
                        'username': username,
                        'password': hashed_password,
                        'role': role
                    }
                    users.append(new_user)
                    save_users(users)
                    st.success('Registration successful! You can now log in.')
                    st.session_state.current_page = 'login'
                    st.rerun()
