import json
import os
import streamlit as st # Used for st.warning to display messages

# --- File Paths (Relative to the module's location) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'db.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')

# --- Helper Functions for JSON DBs ---
def load_data(filepath):
    """
    Loads data from a JSON file.
    If the file does not exist, it creates an empty JSON array file.
    Handles JSONDecodeError for empty or malformed files.
    """
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump([], f)
        return []
    with open(filepath, 'r') as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                st.warning(f"Warning: {filepath} contains non-list data or is malformed. Initializing as empty list.")
                return []
            return data
        except json.JSONDecodeError:
            st.warning(f"Warning: {filepath} is empty or contains invalid JSON. Initializing as empty list.")
            return []

def save_data(filepath, data):
    """Saves data (a Python list of dicts) to a JSON file with pretty-printing."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_users():
    """Loads user data from users.json."""
    return load_data(USERS_FILE)

def save_users(users):
    """Saves user data to users.json."""
    save_data(USERS_FILE, users)

def load_inventory():
    """Loads inventory data from db.json."""
    return load_data(DB_FILE)

def save_inventory(inventory):
    """Saves inventory data to db.json."""
    save_data(DB_FILE, inventory)
