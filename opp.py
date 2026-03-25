import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date, timedelta
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
    except Exception:
        return pd.DataFrame()

df = load_data()

# --- 2. PERMANENT BOUTIQUE INFO ---
SHOP_NAME = st.secrets.get("SHOP_NAME", "RAAJASVI SHEEJA'S DESIGNS")
SHOP_ADDRESS = st.secrets.get("SHOP_ADDRESS", "235/1, TCR COMPLEX, S BINGIPURA GATE, BENGALURU")
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
        img.thumbnail((400, 400)) 
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        return base64.b64encode(buffered.getvalue()).decode()
    return ""

# --- 3. BUSINESS ANALYSIS ---
if choice == "📊 Business Analysis":
    st.header("📈 Monthly Order Analysis")
    if not df.empty and 'Order_Date' in df.columns:
        df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')
        df = df.dropna(subset=['Order_Date'])
        df['Month'] = df['Order_Date'].dt.strftime('%b %Y')
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Orders", len(df))
        c2.metric("Pending ⏳", len(df[df['Status'] != 'Delivered']) if 'Status' in df.columns else 0)
        c3.metric("Delivered ✅", len(df[df['Status'] == 'Delivered']) if 'Status' in df.columns else 0)
        st.bar_chart(df.groupby('Month').size())
    else:
        st.info("No data available for analysis yet.")

# --- 4. NEW ORDER ---
# --- 2. NEW ORDER (FULL 36-COLUMN AUTO-RETRIEVAL) ---
elif choice == "➕ New Order":
    st.subheader(f"➕ Create New Order - {SHOP_NAME}")
    
    # 1. Phone Cleaning & Customer Selection
    if not df.empty and 'Phone' in df.columns:
        df['Phone'] = df['Phone'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')

    customer_list = ["New Customer"] + sorted(df['Name'].unique().tolist()) if not df.empty else ["New Customer"]
    selected_customer = st.selectbox("👤 Select Customer", customer_list)

    # 2. Retrieval Logic
    prev = {}
    if selected_customer != "New Customer":
        prev = df[df['Name'] == selected_customer].iloc[-1].to_dict()
        st.success(f"✅ All measurements retrieved for {selected_customer}")

    with st.form("new_order_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        name = col_a.text_input("Client Name*", value=selected_customer if selected_customer != "New Customer" else "")
        phone = col_b.text_input("Contact Number*", value=str(prev.get('Phone', '')).replace('.0', ''))
        
        c1, c2, c3 = st.columns(3)
        cat_options = ["Chudidhar", "Blouse", "Lehenga", "Kurti", "Gents", "Other"]
        order_type = c1.selectbox("Category", cat_options, 
                                 index=cat_options.index(prev.get('Order_Type', 'Chudidhar')) if prev.get('Order_Type') in cat_options else 0)
        amount = c2.number_input("Total Amount (₹)", value=int(prev.get('Amount', 0)) if prev else 0)
        delivery_date = c3.date_input("Delivery Date")

        # --- DYNAMIC MEASUREMENT SECTIONS (Matches your exact sheet headers) ---
        st.markdown("### 📏 Detailed Measurements")
        
        def get_f(key): return float(prev.get(key, 0.0)) if pd.notna(prev.get(key)) else 0.0

        # Section 1: Top & Upper Body
        m1, m2, m3, m4 = st.columns(4)
        top_len = m1.number_input("Top Len", value=get_f('Top Len'))
        shoulder = m2.number_input("Shoulder", value=get_f('Shoulder'))
        chest = m3.number_input("Chest", value=get_f('Chest'))
        waist_len = m4.number_input("Waist Len", value=get_f('Waist Len'))

        m5, m6, m7, m8 = st.columns(4)
        waist = m5.number_input("Waist", value=get_f('Waist'))
        hip_len = m6.number_input("Hip Len", value=get_f('Hip Len'))
        hip = m7.number_input("Hip", value=get_f('Hip'))
        hip_loose = m8.number_input("Hip Loose", value=get_f('Hip Loose'))

        # Section 2: Neck & Sleeves
        n1, n2, n3, n4 = st.columns(4)
        f_neck = n1.number_input("F-Neck", value=get_f('F-Neck'))
        b_neck = n2.number_input("B-Neck", value=get_f('B-Neck'))
        f_neck_c = n3.number_input("F-Neck (C)", value=get_f('F-Neck (C)'))
        b_neck_c = n4.number_input("B-Neck (C)", value=get_f('B-Neck (C)'))

        s1, s2, s3, s4 = st.columns(4)
        s_len = s1.number_input("S-Len", value=get_f('S-Len'))
        s_open = s2.number_input("S-Open", value=get_f('S-Open'))
        upper_arm = s3.number_input("Upper Arm", value=get_f('Upper Arm'))
        point_c = s4.number_input("Point Centre", value=get_f('Point Centre'))

        # Section 3: Bottom / Trouser Details
        st.markdown("---")
        b1, b2, b3, b4 = st.columns(4)
        bot_len = b1.number_input("Bot-Len", value=get_f('Bot-Len'))
        bot_open = b2.number_input("Bot-Open", value=get_f('Bot-Open'))
        bot_hip = b3.number_input("Bot-Hip", value=get_f('Bot-Hip'))
        thigh = b4.number_input("Thigh", value=get_f('Thigh'))

        t1, t2, t3, t4 = st.columns(4)
        trouser_len = t1.number_input("Trouser Len", value=get_f('Trouser Len'))
        waist_tr = t2.number_input("Waist (Tr)", value=get_f('Waist (Tr)'))
        ankle = t3.number_input("Ankle", value=get_f('Ankle'))
        shirt_len = t4.number_input("Shirt Len", value=get_f('Shirt Len'))

        # Additional Gents/Special
        g1, g2 = st.columns(2)
        collar = g1.number_input("Collar", value=get_f('Collar'))
        # You can add more specific fields here if needed

        notes = st.text_area("Specific Styling Notes (Design details, Lining, etc.)", value=prev.get('Notes', ''))
        img_file = st.file_uploader("📸 Design Reference", type=['jpg', 'png'])

        if st.form_submit_button("📝 Confirm & Save to Cloud"):
            if name and phone:
                img_str = base64.b64encode(img_file.read()).decode() if img_file else prev.get('Image_Data', '')
                
                # Matching dictionary exactly to your 36+ columns
                new_row = {
                    "Order_Date": datetime.now().strftime("%Y-%m-%d"),
                    "Name": name, "Phone": phone, "Order_Type": order_type,
                    "Amount": amount, "Status": "Pending", "Payment": "Unpaid",
                    "Top Len": top_len, "Shoulder": shoulder, "Chest": chest, "Waist Len": waist_len,
                    "Waist": waist, "Hip Len": hip_len, "Hip": hip, "Hip Loose": hip_loose,
                    "F-Neck": f_neck, "B-Neck": b_neck, "F-Neck (C)": f_neck_c, "B-Neck (C)": b_neck_c,
                    "S-Len": s_len, "S-Open": s_open, "Upper Arm": upper_arm, "Point Centre": point_c,
                    "Bot-Len": bot_len, "Bot-Open": bot_open, "Bot-Hip": bot_hip, "Thigh": thigh,
                    "Trouser Len": trouser_len, "Waist (Tr)": waist_tr, "Ankle": ankle,
                    "Shirt Len": shirt_len, "Collar": collar, "Notes": notes, "Image_Data": img_str
                }
                
                # Save to Google Sheets
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"Successfully recorded order for {name}!")
                st.balloons()
                st.rerun()
            else:
                st.error("Client Name and Contact Number are required.")

# --- 5. HISTORY & TRACKER ---
elif choice == "📜 History & Tracker":
    st.subheader("📜 Client History & Order Management")
    if not df.empty:
        search = st.text_input("🔍 Filter by Client Name")
        v_df = df if not search else df[df['Name'].str.contains(search, case=False, na=False)]
        
        # We loop through the data to show each order
        for i, row in v_df.iterrows():
            # Get basic info for the message
            c_name = row.get('Name', 'Customer')
            c_type = row.get('Order_Type', 'Order')
            c_amt = row.get('Amount', 0)
            c_phone = str(row.get('Phone', '')).strip()
            # Clean phone number (remove .0 if it's a float)
            if c_phone.endswith('.0'): c_phone = c_phone[:-2]

            with st.expander(f"👤 {c_name} | {row.get('Status')} | {row.get('Order_Date')}"):
                col_info, col_img = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Category:** {c_type} | **Delivery:** {row.get('Delivery_Date')}")
                    # --- 5. HISTORY & TRACKER ---
elif choice == "📜 History & Tracker":
    st.subheader(f"📜 {SHOP_NAME} - Order Management")
    
    if not df.empty:
        # Search Bar
        search = st.text_input("🔍 Filter by Client Name")
        v_df = df if not search else df[df['Name'].str.contains(search, case=False, na=False)]
        
        # Standard Options
        order_stages = ["Pending", "Cutting", "Stitching", "Ready", "Delivered"]
        payment_stages = ["Unpaid", "Partial Paid", "Paid"]

        for i, row in v_df.iterrows():
            c_name = row.get('Name', 'Customer')
            c_type = row.get('Order_Type', 'Order')
            c_amt = row.get('Amount', 0)
            c_phone = str(row.get('Phone', '')).strip().replace(".0", "")
            
            # --- SAFE DATA RETRIEVAL ---
            curr_status = row.get('Status', 'Pending')
            if curr_status not in order_stages: curr_status = "Pending"
            
            curr_payment = row.get('Payment', 'Unpaid')
            if curr_payment not in payment_stages: curr_payment = "Unpaid"

            with st.expander(f"👤 {c_name} | {curr_status} | {row.get('Order_Date')}"):
                col_info, col_img = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Category:** {c_type} | **Delivery:** {row.get('Delivery_Date')}")
                    
                    # --- UPDATES SECTION ---
                    c1, c2 = st.columns(2)
                    
                    # Dropdown for Order Progress
                    new_status = c1.selectbox("Order Progress", order_stages, 
                                              index=order_stages.index(curr_status),
                                              key=f"stat_{i}")
                    
                    # Dropdown for Payment Progress (Refined Labels)
                    new_payment = c2.selectbox("Payment Status", payment_stages, 
                                               index=payment_stages.index(curr_payment),
                                               key=f"pay_{i}")
                    
                    if st.button("💾 Save All Updates", key=f"save_btn_{i}"):
                        df.at[i, 'Status'] = new_status
                        df.at[i, 'Payment'] = new_payment
                        conn.update(data=df)
                        st.success(f"Changes for {c_name} saved!")
                        st.rerun()

                    # --- WHATSAPP MESSAGES (Updated Brand Name) ---
                    st.markdown("---")
                    st.write("📲 **WhatsApp Reminders:**")
                    w_col1, w_col2 = st.columns(2)
                    
                    # Template 1: Confirmation
                    conf_msg = f"✂️ RAAJASVI SHEEJA'S DESIGNS - INVOICE\nHello {c_name}, your {c_type} order is confirmed! Amt: ₹{c_amt}"
                    w_col1.link_button("📩 Confirmation", f"https://wa.me/{c_phone}?text={conf_msg.replace(' ', '%20')}")
                    
                    # Template 2: Ready for Pickup
                    ready_msg = f"✨ Hello {c_name}, your {c_type} is READY at RAAJASVI SHEEJA'S DESIGNS! Amt: ₹{c_amt}"
                    w_col2.link_button("✅ Ready Notification", f"https://wa.me/{c_phone}?text={ready_msg.replace(' ', '%20')}")

                with col_img:
                    # Show Image if exists
                    if row.get('Image_Data') and pd.notna(row['Image_Data']):
                        try:
                            st.image(base64.b64decode(row['Image_Data']), caption="Design Reference", use_container_width=True)
                        except:
                            st.warning("Could not load image.")
                    
                    # Show all measurement fields dynamically
                    st.info("📏 Measurements")
                    internal_cols = ["Order_Date", "Name", "Phone", "Order_Type", "Amount", "Status", "Delivery_Date", "Notes", "Image_Data", "Payment"]
                    meas_dict = {k: v for k, v in row.to_dict().items() if k not in internal_cols and pd.notna(v)}
                    for k, v in meas_dict.items():
                        st.write(f"**{k}:** {v}")
    else:
        st.info("No orders found in the database.")

# --- 6. DOWNLOAD DATA ---
elif choice == "📥 Download Data":
    st.download_button("📥 Export Database (CSV)", data=df.to_csv(index=False), file_name=f"Boutique_Backup_{date.today()}.csv")