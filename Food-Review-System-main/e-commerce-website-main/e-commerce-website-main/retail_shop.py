import streamlit as st
import sqlite3
import random
import os
import base64

# ---------- FUNCTION TO SET BACKGROUND IMAGE ----------
def set_bg_image(image_file):
    image_path = os.path.join("static", "images", image_file)
    if not os.path.exists(image_path):
        st.warning(f"Background image not found: {image_path}")
        return
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------- DATABASE ----------
DB_NAME = "store.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER, category TEXT, image TEXT)''')
    
    # Insert initial data if empty
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            ("Laptop", 50000, 10, "Electronics", "laptop.jpg"),
            ("Phone", 20000, 15, "Electronics", "phone.jpg"),
            ("Headphones", 2000, 30, "Electronics", "headphones.jpg"),
            ("Shoes", 3000, 20, "Fashion", "shoes.jpg"),
            ("Watch", 1500, 25, "Fashion", "watch.jpg"),
            ("Backpack", 1200, 18, "Accessories", "backpack.jpg"),
            ("Keyboard", 2500, 12, "Electronics", "keyboard.jpg")
        ]
        c.executemany("INSERT INTO products (name, price, stock, category, image) VALUES (?, ?, ?, ?, ?)", products)
    
    conn.commit()
    conn.close()

# ---------- AI PRICING ----------
def dynamic_price(price, stock):
    demand = random.randint(50, 100)
    if demand > 80:
        price *= 1.25
    if stock < 10:
        price *= 1.3
    return round(price, 2)

# ---------- AI RECOMMEND ----------
def recommend_products(category, current_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE category=? AND id!=?", (category, current_id))
    same_cat = c.fetchall()
    if len(same_cat) < 1:
        c.execute("SELECT * FROM products WHERE id!=?", (current_id,))
        same_cat = c.fetchall()
    conn.close()
    return random.sample(same_cat, min(3, len(same_cat)))

# ---------- PRODUCT OPERATIONS ----------
def get_products(search=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if search:
        c.execute("SELECT * FROM products WHERE name LIKE ?", ('%' + search + '%',))
    else:
        c.execute("SELECT * FROM products")
    items = c.fetchall()
    conn.close()
    return items

def buy_product(pid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (pid,))
    product = c.fetchone()
    if not product:
        conn.close()
        return False, "Product not found", []
    
    stock = product[3]
    category = product[4]
    if stock > 0:
        c.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (pid,))
        conn.commit()
        message = "✅ Order Successful!"
    else:
        message = "❌ Sorry, Out of Stock"
    
    conn.close()
    recs = recommend_products(category, pid)
    return stock > 0, message, recs

# ---------- STREAMLIT UI ----------
init_db()
st.set_page_config(page_title="SmartStore", page_icon="🛒", layout="wide")
set_bg_image("background.jpg")

st.title("🛒 SmartStore - AI Powered Online Shop")

# Search bar
search = st.text_input("Search products...", "")
products = get_products(search)

# Display products
for p in products:
    col1, col2 = st.columns([2,1])
    with col1:
        st.subheader(f"{p[1]}")
        image_path = os.path.join("static", "images", p[5])
        if os.path.exists(image_path):
            st.image(image_path, width=200)
        else:
            st.write("Image not found")
        st.write(f"Category: {p[4]}")
        st.write(f"💰 Price: ₹{dynamic_price(p[2], p[3])}")
        st.write(f"Stock: {p[3]}")
    with col2:
        if st.button(f"Buy {p[1]}", key=p[0]):
            success, message, recs = buy_product(p[0])
            st.success(message)
            if success and recs:
                st.subheader("You may also like:")
                for r in recs:
                    st.write(f"- {r[1]} (₹{dynamic_price(r[2], r[3])}, Stock: {r[3]})")
