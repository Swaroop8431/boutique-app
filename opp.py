import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date, timedelta
import urllib.parse
import base64
from io import BytesIO
from PIL import Image
import ast

st.set_page_config(page_title="Boutique Master Pro", page_icon="✂️", layout="wide")

# --- 1. CLOUD CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(ttl="0s") 
    except:
        return pd.DataFrame(columns=["Order_Date", "Name", "Phone", "Type", "Amount", "Status", "Delivery_Date", "Measurements", "Notes", "Image_Data"])

df = load_data()

# --- 2. PERMANENT BOUTIQUE INFO ---
SHOP_NAME = st.secrets.get("SHOP_NAME", "SHEEJA'S DESIGNS")
SHOP_ADDRESS = st.secrets.get("SHOP_ADDRESS", "Your Address")
SHOP_GST = st.secrets.get("SHOP_GST", "29AAAAA0000A1Z5")

st.sidebar.title(f"🏢 {SHOP_NAME}")
st.sidebar.info(f"📍 {SHOP_ADDRESS}\n\n🆔 GST: {SHOP_GST}")

menu = ["➕ New Order", "📊 Business Analysis", "📜 History & Tracker", "📥 Download Data"]
choice = st.sidebar.radio("Navigation", menu)

# --- HELPER: CONVERT IMAGE TO TEXT ---
def img_to_base64(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img = img.convert("RGB")
        img.thumbnail((400, 400)) # Resize to keep Google Sheet fast
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        return base64.b64encode(buffered.getvalue()).decode()
    return ""

# --- 3. BUSINESS ANALYSIS ---
if choice == "📊 Business Analysis":
    st.header("📈 Monthly Order Analysis")
    if not df.empty:
        df['Order_Date'] = pd.to_datetime(df['Order_Date'])
        df['Month'] = df['Order_Date'].dt.strftime('%b %Y')
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Orders", len(df))
        c2.metric("Pending ⏳", len(df[df['Status'] != 'Delivered']))
        c3.metric("Delivered ✅", len(df[df['Status'] == 'Delivered']))
        st.bar_chart(df.groupby('Month').size())

# --- 4. NEW ORDER (Professional Phrasing & Auto-Fill) ---
elif choice == "➕ New Order":
    st.subheader("📝 Customer Order Entry")
    
    existing_names = df['Name'].unique().tolist() if not df.empty else []
    selected_name = st.selectbox("Search Existing Client Database", [""] + existing_names)
    new_client_name = st.text_input("New Client Registration")
    final_name = new_client_name if new_client_name else selected_name
    
    prev_phone, prev_m = "", {}
    if final_name and not df.empty:
        cust_match = df[df['Name'] == final_name].iloc[-1:]
        if not cust_match.empty:
            prev_phone = cust_match['Phone'].values[0]
            try: prev_m = ast.literal_eval(cust_match['Measurements'].values[0])
            except: prev_m = {}

    order_type = st.selectbox("Select Garment Category", ["Chudidhar", "Blouse", "Gents"])
    
    with st.form("main_form", clear_on_submit=True):
        d_col1, d_col2 = st.columns(2)
        order_placed_date = d_col1.date_input("Order Date (Placement)", date.today())
        delivery_target_date = d_col2.date_input("Target Delivery Date", date.today() + timedelta(days=7))

        c1, c2 = st.columns(2)
        phone = c1.text_input("Contact Number (WhatsApp)", value=prev_phone)
        amount = c2.number_input("Stitching Charges (₹)", min_value=0)

        st.markdown("---")
        m = {} 
        col_l, col_r = st.columns(2)
        def get_v(key): return str(prev_m.get(key, ""))

        with col_l:
            st.subheader("📏 Upper Body")
            if order_type == "Chudidhar":
                for k in ["Top Len", "Shoulder", "Chest", "Waist Len", "Waist", "Hip Len", "Hip"]:
                    m[k] = st.text_input(k, value=get_v(k))
            elif order_type == "Blouse":
                for k in ["Length", "Shoulder", "Chest", "F-Neck", "B-Neck"]:
                    m[k] = st.text_input(k, value=get_v(k))
            elif order_type == "Gents":
                for k in ["Shirt Len", "Shoulder", "Chest", "Collar"]:
                    m[k] = st.text_input(k, value=get_v(k))
        
        with col_r:
            st.subheader("✂️ Sleeves & Lower")
            if order_type == "Chudidhar":
                for k in ["F-Neck (C)", "B-Neck (C)", "S-Len", "S-Open", "Bot-Len", "Bot-Open", "Bot-Hip"]:
                    m[k] = st.text_input(k, value=get_v(k))
            elif order_type == "Blouse":
                for k in ["Point Centre", "S-Len", "S-Open", "Upper Arm", "Hip Loose"]:
                    m[k] = st.text_input(k, value=get_v(k))
            elif order_type == "Gents":
                for k in ["Sleeve Len", "Sleeve Open", "Trouser Len", "Waist (Tr)", "Thigh", "Ankle"]:
                    m[k] = st.text_input(k, value=get_v(k))

        st.markdown("---")
        ref_image = st.file_uploader("📸 Reference Design (Saved Forever)", type=['png', 'jpg', 'jpeg'])
        notes = st.text_area("📝 Customization Notes")
        
        if st.form_submit_button("Confirm and Save Order"):
            if final_name and phone:
                encoded_image = img_to_base64(ref_image)
                
                new_row = pd.DataFrame([{
                    "Order_Date": str(order_placed_date), "Name": final_name, "Phone": phone, 
                    "Type": order_type, "Amount": amount, "Status": "Pending", 
                    "Delivery_Date": str(delivery_target_date), "Measurements": str(m), 
                    "Notes": notes, "Image_Data": encoded_image
                }])
                conn.update(data=pd.concat([df, new_row], ignore_index=True))
                st.success(f"Order recorded! Image saved permanently to Cloud.")
                st.rerun()

# --- 5. HISTORY & TRACKER ---
elif choice == "📜 History & Tracker":
    st.subheader("📜 Client History")
    search = st.text_input("🔍 Filter by Client Name")
    v_df = df if not search else df[df['Name'].str.contains(search, case=False, na=False)]
    
    for i, row in v_df.iterrows():
        with st.expander(f"👤 {row.get('Name')} | Ordered: {row.get('Order_Date')}"):
            col_t, col_i = st.columns([2, 1])
            with col_t:
                st.write(f"**Delivery:** {row.get('Delivery_Date')} | **Fee:** ₹{row.get('Amount')}")
                st.write(f"**Details:** {row.get('Measurements')}")
            with col_i:
                img_str = row.get('Image_Data')
                if img_str:
                    st.image(base64.b64decode(img_str), width=200)

# --- 6. DOWNLOAD DATA ---
elif choice == "📥 Download Data":
    st.download_button("📥 Export Database (CSV)", data=df.to_csv(index=False), file_name=f"Boutique_{date.today()}.csv")