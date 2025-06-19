import os
# Removed: import streamlit as st here to avoid any potential Streamlit context issues during initial module load.

# --- Base Directory Retrieval ---
# Define BASE_DIR as a module-level variable that is guaranteed to be a string.
# It prioritizes the script's directory but falls back to the current working directory.
def _get_base_dir_robust():
    """
    Robustly determines the base directory of the application.
    Always returns a string path, falling back to os.getcwd() if necessary.
    """
    try:
        # os.path.abspath(__file__) gives the full path to the current script (utils.py)
        current_file_path = os.path.abspath(__file__)
        # os.path.dirname gets the directory of that script
        if current_file_path and os.path.exists(current_file_path):
            return os.path.dirname(current_file_path)
        else:
            # Fallback if __file__ is not useful (e.g., in some interactive environments)
            return os.getcwd()
    except Exception as e:
        # Fallback to current working directory and print an error for debugging.
        print(f"Error determining script path: {e}. Falling back to os.getcwd().")
        return os.getcwd()

BASE_DIR = _get_base_dir_robust()

# --- Image Directory Retrieval Function ---
def get_image_dir():
    """
    Returns the absolute path to the 'static/images' directory.
    This function ensures the path is always computed correctly and returned as a string.
    Includes fallback for robustness.
    """
    try:
        images_path = os.path.join(BASE_DIR, 'static', 'images')
        # Add a final sanity check, though BASE_DIR should prevent None
        if not isinstance(images_path, str) or not images_path:
            raise ValueError(f"Computed image path is invalid: {images_path}")
        return images_path
    except Exception as e:
        print(f"Error computing image directory path: {e}. Falling back to default image path.")
        # Guaranteed fallback path if primary method fails
        fallback_path = os.path.join(os.getcwd(), 'static', 'images')
        os.makedirs(fallback_path, exist_ok=True) # Ensure fallback directory exists
        return fallback_path

# --- PDF Directory Retrieval Function ---
def get_pdf_dir():
    """
    Returns the absolute path to the 'static/pdfs' directory.
    This function ensures the path is always computed correctly and returned as a string.
    Includes fallback for robustness.
    """
    try:
        pdfs_path = os.path.join(BASE_DIR, 'static', 'pdfs')
        if not isinstance(pdfs_path, str) or not pdfs_path:
            raise ValueError(f"Computed PDF path is invalid: {pdfs_path}")
        return pdfs_path
    except Exception as e:
        print(f"Error computing PDF directory path: {e}. Falling back to default PDF path.")
        fallback_path = os.path.join(os.getcwd(), 'static', 'pdfs')
        os.makedirs(fallback_path, exist_ok=True) # Ensure fallback directory exists
        return fallback_path

# --- Image Placeholder Path (still needed for display) ---
def get_placeholder_image_path():
    """Returns the path to the placeholder image."""
    # Uses get_image_dir to ensure the base path is robustly obtained
    return os.path.join(get_image_dir(), 'placeholder.png')

# --- File Type Configuration (for uploads - if any) ---
# Now allows common image formats in addition to PDF
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'} 

def allowed_file(filename):
    """Checks if a file's extension is in the list of allowed extensions."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_dirs():
    """
    Ensures that necessary directories (like the PDFs directory and static/images for placeholder and uploads) exist.
    Creates them if they don't.
    """
    # Ensure PDFs directory exists
    pdfs_dir_path = get_pdf_dir()
    os.makedirs(pdfs_dir_path, exist_ok=True) # os.makedirs handles errors internally, ok_exist=True prevents re-raise

    # Ensure static/images directory exists for both placeholder and uploaded images
    images_static_path = get_image_dir() # Use get_image_dir for consistency
    os.makedirs(images_static_path, exist_ok=True)

    # Check for the existence of a placeholder image
    placeholder_path = get_placeholder_image_path()
    if not os.path.exists(placeholder_path):
        print(f"INFO: Please consider placing a 'placeholder.png' image in '{images_static_path}' for items without specific images. A blank image will be shown otherwise.")
