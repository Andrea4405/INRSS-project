import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_javascript import st_javascript
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database initialization
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT NOT NULL,
         quantity INTEGER NOT NULL,
         expiration_date DATE NOT NULL,
         reminder_frequency INTEGER NOT NULL,
         minimum_stock INTEGER NOT NULL,
         image_url TEXT,
         last_reminder DATE)
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Custom CSS
def load_css():
    st.markdown("""
        <style>
        .main { padding: 2rem; }
        .stButton>button { width: 100%; background-color: #4CAF50; color: white; padding: 0.5rem; border: none; border-radius: 4px; }
        .product-card { border: 1px solid #ddd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; background-color: white; }
        .metric-card { background-color: #f8f9fa; padding: 1rem; border-radius: 8px; text-align: center; }
        .reminder-card { background-color: #fff3cd; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; }
        </style>
    """, unsafe_allow_html=True)

# Database operations
def add_product(name, quantity, expiration_date, reminder_frequency, minimum_stock, image_path):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO products (name, quantity, expiration_date, reminder_frequency, minimum_stock, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, quantity, expiration_date, reminder_frequency, minimum_stock, image_path))
    conn.commit()
    conn.close()


def get_products():
    conn = sqlite3.connect('inventory.db')
    df = pd.read_sql_query('SELECT * FROM products', conn)
    conn.close()
    return df

# Main application
def main():
    st.set_page_config(page_title="Health Product Inventory", layout="wide")
    load_css()
    st.title("Health Product Inventory")
    
    # Dashboard metrics
    df = get_products()
    total_products = df.shape[0]
    low_stock = df[df['quantity'] <= df['minimum_stock']].shape[0]
    expiring_soon = df[pd.to_datetime(df['expiration_date']) <= (datetime.now() + timedelta(days=30))].shape[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><h3>Total Products</h3><h2>{total_products}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h3>Low Stock</h3><h2>{low_stock}</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>Expiring Soon</h3><h2>{expiring_soon}</h2></div>", unsafe_allow_html=True)
    
    # Add new product
    with st.form("add_product_form"):
        name = st.text_input("Product Name")
        quantity = st.number_input("Quantity", min_value=0)
        expiration_date = st.date_input("Expiration Date")
        reminder_frequency = st.number_input("Reminder Frequency (days)", min_value=1)
        minimum_stock = st.number_input("Minimum Stock Level", min_value=0)
        uploaded_file = st.file_uploader("Upload Product Image", type=["jpg", "png", "jpeg"])
        
        image_path = None
        if uploaded_file is not None:
            image_path = os.path.join("images", uploaded_file.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        if st.form_submit_button("Add Product"):
            add_product(name, quantity, expiration_date, reminder_frequency, minimum_stock, image_path)
            st.success("Product added successfully!")
            st.rerun()
    
    # Display inventory
    st.subheader("Current Inventory")
    if not df.empty:
        df['expiration_date'] = pd.to_datetime(df['expiration_date'])
        for _, product in df.iterrows():
            st.markdown(f"""
                <div class="product-card">
                    <h3>{product['name']}</h3>
                    <p>Quantity: {product['quantity']}</p>
                    <p>Expiration: {product['expiration_date'].strftime('%Y-%m-%d')}</p>
                    <p>Minimum Stock: {product['minimum_stock']}</p>
            """, unsafe_allow_html=True)
            
            # Display the image if available
            if "image_url" in product and product["image_url"]:
                st.image(product["image_url"], width=150)
            
            st.markdown(f"""
                <button onclick="updateQuantity({product['id']}, -1)">-</button>
                <button onclick="updateQuantity({product['id']}, 1)">+</button>
                <button onclick="if(confirm('Are you sure?')){{window.location.href='/delete/{product['id']}'}}">
                    Delete
                </button>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No products in inventory. Add some products to get started!")

if __name__ == "__main__":
    main()

