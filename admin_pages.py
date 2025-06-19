import streamlit as st
import pandas as pd
from db_operations import load_users, save_users, load_inventory
from werkzeug.security import generate_password_hash

def admin_dashboard_page():
    """Renders the administrative dashboard."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    st.subheader("Admin Dashboard")
    users = load_users()
    inventory = load_inventory()

    st.write(f"Welcome to the admin panel, **{st.session_state.username}**!")

    st.markdown("---")
    st.markdown("#### User Management")
    st.write("View, edit, and delete user accounts.")
    if st.button("Manage Users", key="btn_manage_users"):
        st.session_state.current_page = 'manage_users'
        st.rerun()

    st.markdown("---")
    st.markdown("#### Inventory Overview")
    st.write(f"Total Inventory Items: **{len(inventory)}**")
    if st.button("Add New Inventory Item", key="btn_add_inventory_item"):
        st.session_state.current_page = 'add_item'
        st.rerun()

    st.markdown("---")
    st.markdown("#### System Information")
    st.write(f"Total Registered Users: **{len(users)}**")

def manage_users_page():
    """Renders the page for managing user accounts."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    st.subheader("Manage Users")
    users = load_users()

    if users:
        users_df = pd.DataFrame(users)
        users_df['id_display'] = users_df['id'].apply(lambda x: x[:8] + '...') 
        users_df['role_display'] = users_df['role'].apply(lambda x: x.capitalize())

        display_cols = ['id_display', 'username', 'role_display']
        st.dataframe(users_df[display_cols], hide_index=True, use_container_width=True, 
                     column_order=['id_display', 'username', 'role_display'],
                     column_config={
                         "id_display": "User ID",
                         "username": "Username",
                         "role_display": "Role"
                     })

        st.markdown("---")
        st.markdown("#### User Actions")
        
        user_options_map = {u['username']: u['id'] for u in users}
        user_display_names = ["-- Select a user --"] + sorted(list(user_options_map.keys()))
        selected_username = st.selectbox("Select a user for action:", options=user_display_names, key="user_select_for_action")
        
        selected_user_id = user_options_map.get(selected_username)

        if selected_user_id:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit {selected_username}", key="edit_selected_user"):
                    st.session_state.current_page = 'edit_user'
                    st.session_state.edit_user_id = selected_user_id
                    st.rerun()
            with col2:
                if selected_user_id != st.session_state.user_id_obj:
                    if st.button(f"Delete {selected_username}", key="delete_selected_user"):
                        st.warning(f"Are you sure you want to delete user {selected_username}? This action cannot be undone.")
                        if st.button("Confirm Delete", key=f"confirm_delete_{selected_user_id}"):
                            delete_user_from_db(selected_user_id)
                            st.success(f"User '{selected_username}' deleted successfully!")
                            st.rerun()
                else:
                    st.warning("You cannot delete your own account.")
    else:
        st.info("No users registered yet.")

def delete_user_from_db(user_id):
    """Deletes a user from the users database."""
    users = load_users()
    
    if user_id == st.session_state.user_id_obj:
        st.error("Cannot delete your own account while logged in.")
        return

    user_to_delete = next((u for u in users if u['id'] == user_id), None)
    if user_to_delete:
        if user_to_delete['role'] == 'admin':
            admin_count_after_deletion = sum(1 for u in users if u['role'] == 'admin' and u['id'] != user_id)
            if admin_count_after_deletion == 0:
                st.error("Cannot delete the last administrator account.")
                return

        users = [u for u in users if u['id'] != user_id]
        save_users(users)
    else:
        st.error('User not found.')

def edit_user_page():
    """Renders the form to edit an existing user's details."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    user_id = st.session_state.get('edit_user_id')
    if not user_id:
        st.warning("No user selected for editing. Please select a user from 'Manage Users'.")
        if st.button("Go to Manage Users"):
            st.session_state.current_page = 'manage_users'
            st.rerun()
        return

    users = load_users()
    user_to_edit = next((u for u in users if u['id'] == user_id), None)

    if not user_to_edit:
        st.error("User not found.")
        st.session_state.current_page = 'manage_users'
        st.rerun()
        return

    st.subheader(f"Edit User: {user_to_edit['username']}")
    with st.form("edit_user_form"):
        new_username = st.text_input("Username", value=user_to_edit['username'])
        
        current_role_index = ["user", "admin"].index(user_to_edit['role'])
        new_role = st.selectbox("Role", ["user", "admin"], index=current_role_index)
        
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        
        submitted = st.form_submit_button("Update User")

        if submitted:
            if not new_username:
                st.error('Username is required.')
            else:
                if user_id == st.session_state.user_id_obj:
                    if new_role != 'admin':
                        admin_count = sum(1 for u in users if u['role'] == 'admin')
                        if admin_count == 1:
                            st.error("You cannot demote the only administrator account.")
                            st.stop()
                
                if new_username.lower() != user_to_edit['username'].lower():
                    if any(u['username'].lower() == new_username.lower() for u in users if u['id'] != user_id):
                        st.error('Username already exists. Please choose a different one.')
                        st.stop()
                
                user_to_edit['username'] = new_username
                user_to_edit['role'] = new_role
                if new_password:
                    if len(new_password) < 6:
                        st.error('New password must be at least 6 characters long.')
                        st.stop()
                    user_to_edit['password'] = generate_password_hash(new_password)
                
                save_users(users)
                st.success(f'User "{user_to_edit["username"]}" updated successfully!')
                st.session_state.current_page = 'manage_users'
                st.rerun()
