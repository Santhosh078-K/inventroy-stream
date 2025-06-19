import streamlit as st
import os
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from db_operations import load_inventory, save_inventory
from utils import ALLOWED_EXTENSIONS, allowed_file, BASE_DIR, get_pdf_dir, get_image_dir, get_placeholder_image_path

# Predefined list of categories for consistency
ITEM_CATEGORIES = ["Electronics", "Books", "Clothing", "Home Goods", "Food", "Office Supplies", "Other"]

def generate_item_pdf(item_data, item_image_filename=None):
    """
    Generates a PDF for a given item, optionally including an image,
    and saves it to the static/pdfs directory.
    Returns the filename of the generated PDF.
    """
    pdf_dir = get_pdf_dir()
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    # Use item name and part of ID for a unique filename
    pdf_filename = f"{item_data['name'].replace(' ', '_').replace('/', '-')}_{item_data['id'][:8]}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Inventory Item: {item_data['name']}", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Image (if provided and exists)
    if item_image_filename:
        images_dir = get_image_dir()
        image_full_path = os.path.join(images_dir, item_image_filename)
        if os.path.exists(image_full_path):
            try:
                img = Image(image_full_path)
                max_width = 4 * inch
                aspect_ratio = img.drawHeight / img.drawWidth
                if img.drawWidth > max_width:
                    img.drawWidth = max_width
                    img.drawHeight = max_width * aspect_ratio
                
                story.append(img)
                story.append(Spacer(1, 0.1 * inch))
            except Exception as e:
                print(f"Warning: Could not embed image '{item_image_filename}' into PDF: {e}")
                story.append(Paragraph(f"<i>(Image could not be embedded: {item_image_filename})</i>", styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))
        else:
            story.append(Paragraph(f"<i>(Image file not found: {item_image_filename})</i>", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
    else:
        story.append(Paragraph("<i>(No image provided for this item)</i>", styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))

    # Details
    story.append(Paragraph(f"<b>Item ID:</b> {item_data['id']}", styles['Normal']))
    story.append(Paragraph(f"<b>Category:</b> {item_data.get('category', 'N/A')}", styles['Normal'])) # NEW: Category in PDF
    story.append(Paragraph(f"<b>Quantity:</b> {item_data['quantity']}", styles['Normal']))
    story.append(Paragraph(f"<b>Price:</b> ${item_data['price']:.2f}", styles['Normal']))
    story.append(Spacer(1, 0.4 * inch))

    story.append(Paragraph("This document provides details for the inventory item, including an embedded image if available.", styles['Normal']))

    doc.build(story)
    return pdf_filename


def show_inventory_page():
    """Renders the main inventory display page with search, image display, and PDF download buttons."""
    st.subheader("Current Inventory")
    inventory = load_inventory()
    
    pdf_dir = get_pdf_dir()
    images_dir = get_image_dir()

    # Filters and Search
    col1, col2 = st.columns([3,1])
    with col1:
        search_term = st.text_input("Search by name:", key="inventory_search").lower()
    with col2:
        # Add category filter
        selected_category = st.selectbox("Filter by category:", ["All"] + ITEM_CATEGORIES, key="category_filter")

    filtered_inventory = [item for item in inventory if search_term in item['name'].lower()]
    if selected_category != "All":
        filtered_inventory = [item for item in filtered_inventory if item.get('category') == selected_category]


    if filtered_inventory:
        num_columns = 3 
        cols = st.columns(num_columns)
        
        col_idx = 0 
        for item in filtered_inventory:
            with cols[col_idx]:
                st.markdown(f"**{item['name']}**")
                
                # Display item image or placeholder
                item_image_filename = item.get('image_filename')
                if item_image_filename:
                    image_path = os.path.join(images_dir, item_image_filename)
                    if os.path.exists(image_path):
                        st.image(image_path, caption=item['name'], use_column_width=True)
                    else:
                        st.image(get_placeholder_image_path(), caption="Image not found", use_column_width=True)
                else:
                    st.image(get_placeholder_image_path(), caption="No image", use_column_width=True)


                st.write(f"ID: `{item['id'][:8]}...`")
                st.write(f"Category: **{item.get('category', 'N/A')}**") # NEW: Display category
                st.write(f"Quantity: {item['quantity']}")
                st.write(f"Price: **${item['price']:.2f}**")
                
                # PDF Download button
                pdf_filename = item.get('pdf_filename')
                if pdf_filename:
                    pdf_path = os.path.join(pdf_dir, pdf_filename)
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_file,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                key=f"download_pdf_{item['id']}"
                            )
                    else:
                        st.info("PDF not found (might need to edit & re-save item).")
                else:
                    st.info("No PDF available for this item.")
                
                if st.session_state.role == 'admin':
                    if st.button(f"Edit {item['name']}", key=f"edit_btn_{item['id']}"):
                        st.session_state.current_page = 'edit_item' 
                        st.session_state.edit_item_id = item['id'] 
                        st.rerun() 
                    
                    if st.button(f"Delete {item['name']}", key=f"del_btn_{item['id']}"):
                        if st.session_state.get(f'confirm_delete_item_{item["id"]}', False):
                            delete_item_from_db(item['id'])
                            st.success("Item deleted successfully!")
                            st.session_state[f'confirm_delete_item_{item["id"]}'] = False 
                            st.rerun() 
                        else:
                            st.warning(f"Are you sure you want to delete {item['name']}? Click 'Confirm Delete' below to proceed.")
                            st.session_state[f'confirm_delete_item_{item["id"]}'] = True 
                            if st.button("Confirm Delete", key=f"confirm_del_action_btn_{item['id']}"):
                                delete_item_from_db(item['id'])
                                st.success("Item deleted successfully!")
                                st.session_state[f'confirm_delete_item_{item["id"]}'] = False
                                st.rerun()

            col_idx = (col_idx + 1) % num_columns 
    else:
        st.info("No items in inventory matching your search or filters.")
        if st.session_state.role == 'admin':
            if st.button("Add New Item"):
                st.session_state.current_page = 'add_item'
                st.rerun()

def delete_item_from_db(item_id):
    """Deletes an item from the inventory and its associated PDF/image files."""
    inventory = load_inventory()
    pdf_dir = get_pdf_dir()
    images_dir = get_image_dir()
    
    item_to_delete = next((item for item in inventory if item['id'] == item_id), None)
    
    if item_to_delete:
        # Delete associated PDF file
        if item_to_delete.get('pdf_filename'):
            pdf_path = os.path.join(pdf_dir, item_to_delete['pdf_filename'])
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    print(f"Deleted PDF: {pdf_path}")
                except OSError as e:
                    st.error(f"Error deleting PDF file: {e}")
        
        # Delete associated image file
        if item_to_delete.get('image_filename'):
            image_path = os.path.join(images_dir, item_to_delete['image_filename'])
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"Deleted image: {image_path}")
                except OSError as e:
                    st.error(f"Error deleting image file: {e}")

        inventory = [item for item in inventory if item['id'] != item_id]
        save_inventory(inventory) 
    else:
        st.error("Item not found.")


def add_item_page():
    """Renders the form to add a new inventory item and handles its submission, generating PDF and saving image."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return

    st.subheader("Add New Inventory Item")
    with st.form("add_item_form"): 
        name = st.text_input("Item Name")
        category = st.selectbox("Category", ITEM_CATEGORIES, key="add_category") # NEW: Category input
        quantity = st.number_input("Quantity", min_value=1, value=1)
        price = st.number_input("Price", min_value=0.01, value=0.01, format="%.2f")
        uploaded_image_file = st.file_uploader("Upload Item Image (Optional)", type=['png', 'jpg', 'jpeg', 'gif']) 
        
        submitted = st.form_submit_button("Add Item")

        if submitted:
            if not name:
                st.error('Item Name is required.')
            else:
                item_image_filename = None
                if uploaded_image_file:
                    if allowed_file(uploaded_image_file.name):
                        images_dir = get_image_dir()
                        image_uuid = str(uuid.uuid4().hex)
                        file_extension = os.path.splitext(uploaded_image_file.name)[1]
                        item_image_filename = f"{image_uuid}{file_extension}"
                        
                        image_path_full = os.path.join(images_dir, item_image_filename)
                        with open(image_path_full, "wb") as f:
                            f.write(uploaded_image_file.getbuffer())
                        st.success(f"Image uploaded: {item_image_filename}")
                    else:
                        st.warning('Invalid image file type. Allowed: png, jpg, jpeg, gif. Item added without image.')


                new_item = {
                    'id': str(uuid.uuid4()), 
                    'name': name,
                    'category': category, # NEW: Save category
                    'quantity': quantity,
                    'price': price,
                    'pdf_filename': None,
                    'image_filename': item_image_filename
                }
                
                try:
                    pdf_filename = generate_item_pdf(new_item, item_image_filename)
                    new_item['pdf_filename'] = pdf_filename
                    st.success(f"PDF generated: {pdf_filename}")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}. Item added without PDF.")

                inventory = load_inventory() 
                inventory.append(new_item) 
                save_inventory(inventory) 
                st.success('Item added successfully!')
                st.session_state.current_page = 'inventory' 
                st.rerun() 

def edit_item_page():
    """Renders the form to edit an existing inventory item and handles its submission, regenerating PDF and updating image."""
    if st.session_state.role != 'admin':
        st.error("You do not have permission to access this page.")
        return
    
    item_id = st.session_state.get('edit_item_id')
    if not item_id:
        st.warning("No item selected for editing. Please select an item from the inventory.")
        if st.button("Go to Inventory"):
            st.session_state.current_page = 'inventory'
            st.rerun()
        return

    inventory = load_inventory() 
    item_to_edit = next((item for item in inventory if item['id'] == item_id), None)

    if not item_to_edit:
        st.error("Item not found.")
        st.session_state.current_page = 'inventory'
        st.rerun()
        return

    st.subheader(f"Edit Inventory Item: {item_to_edit['name']}")
    with st.form("edit_item_form"): 
        name = st.text_input("Item Name", value=item_to_edit['name'])
        
        # Determine current category index for selectbox
        current_category = item_to_edit.get('category', 'Other')
        if current_category not in ITEM_CATEGORIES:
            ITEM_CATEGORIES.append(current_category) # Add existing unknown category for display
            
        current_category_index = ITEM_CATEGORIES.index(current_category) if current_category in ITEM_CATEGORIES else len(ITEM_CATEGORIES) - 1 # Fallback to 'Other' or last
        
        category = st.selectbox("Category", ITEM_CATEGORIES, index=current_category_index, key="edit_category") # NEW: Edit category
        
        quantity = st.number_input("Quantity", min_value=1, value=item_to_edit['quantity'])
        price = st.number_input("Price", min_value=0.01, value=item_to_edit['price'], format="%.2f")
        
        st.write("---")
        st.markdown("##### Current Image:")
        current_image_filename = item_to_edit.get('image_filename')
        images_dir = get_image_dir()

        if current_image_filename:
            image_path = os.path.join(images_dir, current_image_filename)
            if os.path.exists(image_path):
                st.image(image_path, caption="Current Image", width=150)
                st.write(f"Filename: `{current_image_filename}`")
            else:
                st.info("Current image file not found.")
                st.image(get_placeholder_image_path(), caption="Image Missing", width=100)
        else:
            st.info("No current image.")
            st.image(get_placeholder_image_path(), caption="No Image", width=100)


        uploaded_image_file = st.file_uploader("Upload New Item Image (Optional)", type=['png', 'jpg', 'jpeg', 'gif'], key="edit_image_uploader")
        
        submitted = st.form_submit_button("Update Item")

        if submitted:
            if not name:
                st.error('Item Name is required.')
            else:
                old_pdf_filename = item_to_edit.get('pdf_filename')
                old_image_filename = item_to_edit.get('image_filename')

                # Update core item details
                item_to_edit['name'] = name
                item_to_edit['category'] = category # NEW: Update category
                item_to_edit['quantity'] = quantity
                item_to_edit['price'] = price

                # Handle new image upload
                new_image_filename = old_image_filename 
                if uploaded_image_file:
                    if allowed_file(uploaded_image_file.name):
                        if old_image_filename:
                            old_image_path = os.path.join(images_dir, old_image_filename)
                            if os.path.exists(old_image_path):
                                try:
                                    os.remove(old_image_path)
                                    st.info(f"Old image '{old_image_filename}' deleted.")
                                except OSError as e:
                                    st.error(f"Error deleting old image file '{old_image_filename}': {e}")
                        
                        image_uuid = str(uuid.uuid4().hex)
                        file_extension = os.path.splitext(uploaded_image_file.name)[1]
                        new_image_filename = f"{image_uuid}{file_extension}"
                        
                        new_image_path_full = os.path.join(images_dir, new_image_filename)
                        with open(new_image_path_full, "wb") as f:
                            f.write(uploaded_image_file.getbuffer())
                        st.success(f"New image uploaded: {new_image_filename}")
                    else:
                        st.warning('Invalid image file type for new upload. Allowed: png, jpg, jpeg, gif. Keeping old image (if any).')
                item_to_edit['image_filename'] = new_image_filename

                try:
                    pdf_filename = generate_item_pdf(item_to_edit, item_to_edit['image_filename'])
                    item_to_edit['pdf_filename'] = pdf_filename
                    st.success(f"PDF regenerated: {pdf_filename}")

                    if old_pdf_filename and old_pdf_filename != pdf_filename:
                        old_pdf_path = os.path.join(get_pdf_dir(), old_pdf_filename)
                        if os.path.exists(old_pdf_path):
                            try:
                                os.remove(old_pdf_path)
                                st.info(f"Old PDF '{old_pdf_filename}' deleted.")
                            except OSError as e:
                                st.error(f"Error deleting old PDF file '{old_pdf_filename}': {e}")

                except Exception as e:
                    st.error(f"Error regenerating PDF: {e}. Item updated, but PDF might be outdated.")
                    item_to_edit['pdf_filename'] = old_pdf_filename 

                save_inventory(inventory) 
                st.success('Item updated successfully!')
                st.session_state.current_page = 'inventory'
                st.rerun()
