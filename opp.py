import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import urllib.parse
import os

st.set_page_config(page_title="Boutique Master Cloud", page_icon="✂️", layout="wide")

# --- 1. SETUP & CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)
IMAGE_DIR = "reference_images" 
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def load_data():
    try:
        # Pulls data from Google Sheets
        return conn.read(ttl="0s") 
    except:
        return pd.DataFrame()

df = load_data()

# --- 2. SIDEBAR: BRANDING & GST ---
st.sidebar.header("🏢 Boutique Branding")
shop_name = st.sidebar.text_input("Boutique Name", "My Designer Boutique")
shop_address = st.sidebar.text_area("Shop Address", "123 Fashion Street")
gst_info = st.sidebar.text_input("GST Number", "22AAAAA0000A1Z5")
shop_logo = st.sidebar.file_uploader("Upload Logo", type=['png', 'jpg', 'jpeg'])

menu = ["➕ New Order", "📜 History & Tracker", "📥 Download Data"]
choice = st.sidebar.radio("Navigation", menu)

if choice == "➕ New Order":
    order_type = st.selectbox("Select Dress Type", ["Chudidhar", "Blouse", "Gents"])
    
    with st.form("main_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Customer Name*")
        phone = c2.text_input("WhatsApp Number (Include 91)")
        amount = st.number_input("Stitching Fee (₹)", min_value=0)
        status = st.selectbox("Status", ["Pending", "Ready", "Delivered"])

        st.markdown("---")
        col_l, col_r = st.columns(2)
        m = {} # Dictionary to capture all specific measurement headers

        with col_l:
            st.subheader(f"📏 {order_type} Upper Body")
            if order_type == "Chudidhar":
                # THE 14 CHUDIDHAR MEASUREMENTS
                m['Top Length'] = st.text_input("Top Length")
                m['Shoulder'] = st.text_input("Shoulder")
                m['Chest'] = st.text_input("Chest")
                m['Waist Length'] = st.text_input("Waist Length")
                m['Waist'] = st.text_input("Waist")
                m['Hip Length'] = st.text_input("Hip Length")
                m['Hip'] = st.text_input("Hip")
            elif order_type == "Blouse":
                # THE 10 BLOUSE MEASUREMENTS
                m['Length'] = st.text_input("Length")
                m['Shoulder'] = st.text_input("Shoulder")
                m['Chest'] = st.text_input("Chest")
                m['Front Neck'] = st.text_input("Front Neck")
                m['Back Neck'] = st.text_input("Back Neck")
            elif order_type == "Gents":
                m['Shirt Length'] = st.text_input("Shirt Length")
                m['G_Shoulder'] = st.text_input("Shoulder")
                m['G_Chest'] = st.text_input("Chest")

        with col_r:
            st.subheader(f"✂️ {order_type} Sleeves & Lower")
            if order_type == "Chudidhar":
                m['F_Neck'] = st.text_input("Front Neck (C)")
                m['B_Neck'] = st.text_input("Back Neck (C)")
                m['S_Length'] = st.text_input("Sleeve Length")
                m['S_Open'] = st.text_input("Sleeve Open")
                m['Bot_Length'] = st.text_input("Bottom Length")
                m['Bot_Open'] = st.text_input("Bottom Open")
                m['Bot_Hip'] = st.text_input("Bottom Hip")
            elif order_type == "Blouse":
                m['Point Centre'] = st.text_input("Point Centre")
                m['S_Length'] = st.text_input("Sleeve Length")
                m['S_Open'] = st.text_input("Sleeve Open")
                m['Upper Arm'] = st.text_input("Upper Arm")
                m['Hip Loose'] = st.text_input("Hip Loose")
            elif order_type == "Gents":
                m['Tr_Length'] = st.text_input("Trouser Length")
                m['Tr_Waist'] = st.text_input("Waist (Trouser)")
                m['Thigh'] = st.text_input("Thigh")
                m['Knee'] = st.text_input("Knee")
                m['Ankle'] = st.text_input("Ankle")

        st.markdown("---")
        ref_image = st.file_uploader("📸 Reference Design", type=['png', 'jpg', 'jpeg'])
        notes = st.text_area("📝 Design Notes")
        
        if st.form_submit_button("Save Order"):
            if name and phone:
                img_name = f"{name}_{date.today()}.jpg" if ref_image else ""
                if ref_image:
                    with open(os.path.join(IMAGE_DIR, img_name), "wb") as f:
                        f.write(ref_image.getbuffer())
                
                # PUSHING TO CLOUD
                new_row = pd.DataFrame([{
                    "Date": str(date.today()), "Name": name, "Phone": phone, 
                    "Type": order_type, "Amount": amount, "Status": status, 
                    "Notes": notes, "Image_Name": img_name, 
                    "Measurements": str(m) # All 14 or 10 headers saved inside here
                }])
                
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("✅ Order & Measurements Saved!")
                st.rerun()

elif choice == "📜 History & Tracker":
    st.subheader("📜 Customer Ledger")
    search = st.text_input("🔍 Search Name")
    v_df = df if not search else df[df['Name'].str.contains(search, case=False, na=False)]
    
    for i, row in v_df.iterrows():
        with st.expander(f"👤 {row.get('Name')} - {row.get('Type')}"):
            st.write(f"**Measurements:** {row.get('Measurements')}")
            if row.get('Status') == "Ready":
                msg = f"Hello {row.get('Name')}, your {row.get('Type')} is READY at {shop_name}! Amt: ₹{row.get('Amount')}"
                st.link_button("📲 Send WhatsApp", f"https://wa.me/{row.get('Phone')}?text={urllib.parse.quote(msg)}")