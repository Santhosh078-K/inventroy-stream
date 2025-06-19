import streamlit as st
import os
import uuid
import sys

# --- Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title="Inventory Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the base directory to sys.path to allow imports from other modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Import functions from other modules
from db_operations import load_users, save_users, load_inventory
from auth import login_page, register_page
from inventory_pages import show_inventory_page, add_item_page, edit_item_page
from admin_pages import admin_dashboard_page, manage_users_page, edit_user_page
from dashboard_pages import show_dashboard_page # NEW: Import dashboard page
from utils import ensure_dirs, get_image_dir # Import utility functions

# Ensure necessary directories exist at startup
ensure_dirs()

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'inventory' # Default page when app starts

# Create a default admin user if no users exist in users.json
users_data = load_users()
if not users_data:
    from werkzeug.security import generate_password_hash
    initial_admin_username = "admin"
    initial_admin_password = "password" # IMPORTANT: CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!
    
    admin_user = {
        'id': str(uuid.uuid4()),
        'username': initial_admin_username,
        'password': generate_password_hash(initial_admin_password),
        'role': 'admin'
    }
    users_data.append(admin_user)
    save_users(users_data)
    st.success(f"Initial admin user created: Username '{initial_admin_username}' with password '{initial_admin_password}'. Please change it after logging in!")

# Store the current_user's full ID in session state once logged in for checks
if st.session_state.logged_in and 'user_id_obj' not in st.session_state:
    users = load_users()
    current_user_data = next((u for u in users if u['username'] == st.session_state.username), None)
    if current_user_data:
        st.session_state.user_id_obj = current_user_data['id']


# --- Sidebar Navigation ---
with st.sidebar:
    st.header("Navigation")
    if st.session_state.logged_in:
        st.success(f"Logged in as: **{st.session_state.username}** ({st.session_state.role.capitalize()})")
        st.markdown("---")
        
        if st.button("View Inventory", key="nav_inventory"):
            st.session_state.current_page = 'inventory'
            st.rerun()
        
        if st.button("Dashboard", key="nav_dashboard"): # NEW: Dashboard button
            st.session_state.current_page = 'dashboard'
            st.rerun()

        if st.session_state.role == 'admin':
            if st.button("Add New Item", key="nav_add_item"):
                st.session_state.current_page = 'add_item'
                st.rerun()
            if st.button("Admin Panel", key="nav_admin_dashboard"):
                st.session_state.current_page = 'admin_dashboard'
                st.rerun()
        st.markdown("---")
        
        if st.button("Logout", key="nav_logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            if 'user_id_obj' in st.session_state:
                del st.session_state.user_id_obj
            st.session_state.current_page = 'login'
            st.rerun()
    else:
        if st.button("Login", key="nav_login"):
            st.session_state.current_page = 'login'
            st.rerun()
        if st.button("Register", key="nav_register"):
            st.session_state.current_page = 'register'
            st.rerun()

# --- Main Content Area ---
if not st.session_state.logged_in:
    if st.session_state.current_page == 'register':
        register_page()
    else:
        login_page()
else:
    if st.session_state.current_page == 'inventory':
        show_inventory_page()
    elif st.session_state.current_page == 'dashboard': # NEW: Dashboard routing
        show_dashboard_page()
    elif st.session_state.current_page == 'add_item':
        add_item_page()
    elif st.session_state.current_page == 'edit_item':
        edit_item_page()
    elif st.session_state.current_page == 'admin_dashboard':
        admin_dashboard_page()
    elif st.session_state.current_page == 'manage_users':
        manage_users_page()
    elif st.session_state.current_page == 'edit_user':
        edit_user_page()
    else:
        st.write("Page not found. Please use the navigation.")
        st.session_state.current_page = 'inventory'
        st.rerun()

# --- Custom CSS for minor aesthetic tweaks ---
st.markdown("""
<style>
    /* Streamlit's built-in themes handle most background and text colors. */
    .css-1d391kg { 
        background-color: #2c3e50; 
        color: white;
    }
    .stButton>button {
        background-color: #3498db; 
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 15px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2980b9; 
    }
    .stMarkdown h3, .stMarkdown h2, .stMarkdown h4 {
        color: #34495e; 
        border-bottom: 2px solid #ddd; 
        padding-bottom: 10px;
        margin-top: 25px;
    }
    .stForm {
        background-color: var(--background-color); 
        padding: 25px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    div.stAlert {
        border-radius: 8px;
        font-weight: bold;
    }
    .stAlert.stAlert--success { background-color: #d4edda; color: #155724; border-left: 5px solid #28a745; }
    .stAlert.stAlert--error { background-color: #f8d7da; color: #721c24; border-left: 5px solid #dc3545; }
    .stAlert.stAlert--warning { background-color: #fff3cd; color: #856404; border-left: 5px solid #ffc107; }

</style>
""", unsafe_allow_html=True)
