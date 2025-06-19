import streamlit as st
import pandas as pd
from db_operations import load_inventory # Import function to load inventory data

def show_dashboard_page():
    """
    Renders the dashboard page showing summary statistics of the inventory.
    Includes total items, total value, and items broken down by category.
    """
    st.subheader("Inventory Dashboard")

    inventory = load_inventory()

    if not inventory:
        st.info("No items in inventory to display dashboard statistics. Add some items first!")
        return

    # Convert inventory list to a Pandas DataFrame for easy aggregation
    df = pd.DataFrame(inventory)

    # --- Overall Statistics ---
    total_items = df['quantity'].sum()
    total_value = (df['quantity'] * df['price']).sum()

    st.markdown("### Overall Inventory Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Unique Items", value=len(df))
    with col2:
        st.metric(label="Total Quantity of All Items", value=total_items)
    st.metric(label="Total Inventory Value", value=f"${total_value:,.2f}")

    st.markdown("---")

    # --- Breakdown by Category ---
    st.markdown("### Inventory Breakdown by Category")

    if 'category' in df.columns:
        # Fill NaN categories with 'Uncategorized' for grouping
        df['category'] = df['category'].fillna('Uncategorized')
        
        category_summary = df.groupby('category').agg(
            unique_items=('id', 'nunique'),
            total_quantity=('quantity', 'sum'),
            total_value=('price', lambda x: (x * df.loc[x.index, 'quantity']).sum())
        ).reset_index()

        category_summary.columns = ['Category', 'Unique Items', 'Total Quantity', 'Total Value']
        category_summary['Total Value'] = category_summary['Total Value'].map('${:,.2f}'.format)
        
        st.dataframe(category_summary, hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("### Item Details by Category")
        
        # Expanders to show items within each category
        for category in sorted(df['category'].unique()):
            with st.expander(f"Items in {category} (Click to expand)"):
                category_items = df[df['category'] == category][['name', 'quantity', 'price', 'id']].copy()
                category_items['price'] = category_items['price'].map('${:,.2f}'.format)
                category_items['id_short'] = category_items['id'].apply(lambda x: x[:8] + '...')
                st.dataframe(category_items[['name', 'quantity', 'price', 'id_short']], hide_index=True, use_container_width=True)

    else:
        st.info("No 'category' field found in inventory items. Add categories to your items to see this breakdown.")

    st.markdown("---")
    st.markdown("### Raw Inventory Data")
    
    # Dynamically build the list of columns to display,
    # ensuring 'category' is only included if it exists.
    raw_data_columns = ['name']
    if 'category' in df.columns:
        raw_data_columns.append('category')
    raw_data_columns.extend(['quantity', 'price', 'id', 'pdf_filename', 'image_filename'])

    st.dataframe(df[raw_data_columns], use_container_width=True)
