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
SHOP_NAME = st.secrets.get("SHOP_NAME", "SHEEJA'S DESIGNS")
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
elif choice == "➕ New Order":
    st.subheader("📝 Customer Order Entry")
    
    existing_names = df['Name'].unique().tolist() if not df.empty and 'Name' in df.columns else []
    selected_name = st.selectbox("Search Existing Client Database", [""] + existing_names)
    new_client_name = st.text_input("New Client Registration")
    final_name = new_client_name if new_client_name else selected_name
    
    prev_phone, prev_m = "", {}
    if final_name and not df.empty:
        cust_match = df[df['Name'] == final_name].iloc[-1:]
        if not cust_match.empty:
            prev_phone = cust_match['Phone'].values[0]
            # Attempt to reconstruct measurements if they were saved as a dict previously
            try: prev_m = ast.literal_eval(str(cust_match.to_dict('records')[0]))
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
        ref_image = st.file_uploader("📸 Reference Design", type=['png', 'jpg', 'jpeg'])
        notes = st.text_area("📝 Customization Notes")
        
        if st.form_submit_button("Confirm and Save Order"):
            if final_name and phone:
                encoded_image = img_to_base64(ref_image)
                
                # Create the data row with your specific headers
                data_to_save = {
                    "Order_Date": str(order_placed_date), 
                    "Name": final_name, 
                    "Phone": str(phone), 
                    "Order_Type": order_type, 
                    "Amount": amount, 
                    "Status": "Pending", 
                    "Delivery_Date": str(delivery_target_date), 
                    "Notes": notes, 
                    "Image_Data": encoded_image
                }
                
                # Update with individual measurements
                data_to_save.update(m)
                
                new_row = pd.DataFrame([data_to_save])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                
                # Save to Google Sheets
                conn.update(data=updated_df)
                st.success(f"✅ Order for {final_name} saved successfully!")
                st.rerun()
            else:
                st.error("⚠️ Please provide a Name and Phone Number.")

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
                    
                    # --- STATUS & PAYMENT UPDATES ---
                    c1, c2 = st.columns(2)
                    new_status = c1.selectbox("Order Progress", ["Pending", "Cutting", "Stitching", "Ready", "Delivered"], 
                                              index=["Pending", "Cutting", "Stitching", "Ready", "Delivered"].index(row.get('Status', 'Pending')),
                                              key=f"stat_{i}")
                    
                    new_payment = c2.selectbox("Payment", ["Unpaid", "Partial", "Paid"], 
                                               index=["Unpaid", "Partial", "Paid"].index(row.get('Payment', 'Unpaid')) if 'Payment' in df.columns else 0,
                                               key=f"pay_{i}")
                    
                    if st.button("💾 Save Updates", key=f"btn_{i}"):
                        df.at[i, 'Status'] = new_status
                        if 'Payment' not in df.columns: df['Payment'] = "Unpaid"
                        df.at[i, 'Payment'] = new_payment
                        conn.update(data=df)
                        st.success("Order Updated!")
                        st.rerun()

                    # --- WHATSAPP REMINDERS ---
                    st.markdown("---")
                    st.write("📲 **Send WhatsApp Reminder:**")
                    w_col1, w_col2 = st.columns(2)
                    
                    # Template 1: Confirmation
                    conf_msg = f"✂️ SHEEJA'S DESIGNS - INVOICE\nHello {c_name}, your {c_type} order is confirmed! Amt: ₹{c_amt}"
                    w_col1.link_button("📩 Confirmation", f"https://wa.me/{c_phone}?text={conf_msg.replace(' ', '%20')}")
                    
                    # Template 2: Ready for Pickup
                    ready_msg = f"✨ Hello {c_name}, your {c_type} is READY at SHEEJA'S DESIGNS! Amt: ₹{c_amt}"
                    w_col2.link_button("✅ Ready Notification", f"https://wa.me/{c_phone}?text={ready_msg.replace(' ', '%20')}")

                with col_img:
                    if row.get('Image_Data'):
                        st.image(base64.b64decode(row['Image_Data']), caption="Design Reference", use_container_width=True)
                    
                    # Show measurements
                    st.info("📏 Measurements")
                    meas_dict = {k: v for k, v in row.to_dict().items() if k not in ["Order_Date", "Name", "Phone", "Order_Type", "Amount", "Status", "Delivery_Date", "Notes", "Image_Data", "Payment"] and pd.notna(v)}
                    for k, v in meas_dict.items():
                        st.write(f"**{k}:** {v}")
    else:
        st.info("No orders found in the database.")

# --- 6. DOWNLOAD DATA ---
elif choice == "📥 Download Data":
    st.download_button("📥 Export Database (CSV)", data=df.to_csv(index=False), file_name=f"Boutique_Backup_{date.today()}.csv")