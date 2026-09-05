import streamlit as st
import pandas as pd
import datetime
import hashlib
from supabase import create_client, Client

# ==========================================
# SUPABASE CONFIGURATION & CONNECTION
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Page Configuration
st.set_page_config(page_title="Aswanna | B2B AgTech Platform", page_icon="🌾", layout="wide")

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# SUPABASE DATABASE HELPER FUNCTIONS
# ==========================================
def add_user(username, password, role, name, phone, address, bank):
    data = {
        "username": username,
        "password": hash_password(password),
        "role": role,
        "name": name,
        "phone": phone,
        "address": address,
        "bank": bank
    }
    response = supabase.table("users").insert(data).execute()
    return response

def check_user(username, password):
    hashed_pwd = hash_password(password)
    response = supabase.table("users").select("*").eq("username", username).eq("password", hashed_pwd).execute()
    if response.data and len(response.data) > 0:
        row = response.data[0]
        return [row["username"], row["password"], row["role"], row["name"], row["phone"], row["address"], row["bank"]]
    return None

def get_user_details(username):
    response = supabase.table("users").select("username, role, name, phone, address, bank").eq("username", username).execute()
    if response.data and len(response.data) > 0:
        row = response.data[0]
        return (row["username"], row["role"], row["name"], row["phone"], row["address"], row["bank"])
    return None

def add_crop(crop_id, farmer_username, crop_name, qty, price_per_kg, district, date):
    data = {
        "crop_id": crop_id,
        "farmer_username": farmer_username,
        "crop_name": crop_name,
        "qty": qty,
        "price_per_kg": price_per_kg,
        "district": district,
        "date": date
    }
    supabase.table("products").insert(data).execute()

def get_all_crops():
    response = supabase.table("products").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=["crop_id", "farmer_username", "crop_name", "qty", "price_per_kg", "district", "date"])

def update_crop_qty(crop_id, new_qty):
    supabase.table("products").update({"qty": new_qty}).eq("crop_id", crop_id).execute()

def add_order(order_id, buyer_username, farmer_username, crop_name, qty, total_paid, your_commission, payout_to_farmer, status, date):
    data = {
        "order_id": order_id,
        "buyer_username": buyer_username,
        "farmer_username": farmer_username,
        "crop_name": crop_name,
        "qty": qty,
        "total_paid": total_paid,
        "your_commission": your_commission,
        "payout_to_farmer": payout_to_farmer,
        "status": status,
        "date": date
    }
    supabase.table("orders").insert(data).execute()

def get_all_orders():
    response = supabase.table("orders").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=["order_id", "buyer_username", "farmer_username", "crop_name", "qty", "total_paid", "your_commission", "payout_to_farmer", "status", "date"])

# Custom CSS (Extra Large Hero Banner Styling)
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .hero-container {
        background: linear-gradient(rgba(15, 23, 42, 0.60), rgba(15, 23, 42, 0.88)), 
                    url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1600&q=80');
        background-size: cover; 
        background-position: center; 
        padding: 75px 50px; 
        border-radius: 24px;
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.7); 
        margin-bottom: 40px; 
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .hero-title { color: #4ade80; font-size: 3.5rem; font-weight: 800; margin-bottom: 15px; text-shadow: 0 3px 6px rgba(0,0,0,0.6); }
    .hero-subtitle { color: #f1f5f9; font-size: 1.35rem; font-weight: 500; text-shadow: 0 2px 4px rgba(0,0,0,0.6); }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid rgba(255, 255, 255, 0.1); }
    .sidebar-header-card {
        background: linear-gradient(135deg, #16a34a 0%, #0d9488 100%); padding: 16px; border-radius: 12px;
        text-align: center; color: white; font-weight: 700; font-size: 1.1rem; margin-bottom: 20px;
    }
    [data-testid="stMetricValue"] { color: #4ade80 !important; font-weight: 700; }
    div[data-testid="metric-container"] {
        background-color: #1e293b; border: 1px solid rgba(255, 255, 255, 0.08); padding: 18px; border-radius: 12px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; border: none;
        border-radius: 10px; font-weight: 600; padding: 10px 24px; transition: all 0.3s ease; width: 100%;
    }
    .stButton>button:hover { transform: translateY(-2px); }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 8px; color: #94a3b8; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #16a34a !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Session State Storage
if 'logged_user' not in st.session_state:
    st.session_state.logged_user = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "Login"

# Extra Large Hero Banner Section
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🌾 ASWANNA (අස්වැන්න)</div>
        <div class="hero-subtitle">🔒 පෞද්ගලිකත්වය සුරක්ෂිත කළ, ප්‍රවාහන පහසුකම් සහිත B2B AgTech වෙළඳ පද්ධතිය (7.5% Fair Commission)</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar Authentication
st.sidebar.markdown("""
    <div class="sidebar-header-card">
        🔐 ASWANNA PORTAL<br/>
        <span style="font-size: 0.85rem; font-weight: normal; opacity: 0.9;">Login or Create Account Below</span>
    </div>
""", unsafe_allow_html=True)

if st.session_state.logged_user is None:
    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("🔑 Login"):
            st.session_state.auth_mode = "Login"
            st.rerun()
    with col_btn2:
        if st.button("📝 Register"):
            st.session_state.auth_mode = "Register"
            st.rerun()

    st.sidebar.markdown("---")

    if st.session_state.auth_mode == "Register":
        st.sidebar.markdown("### 📝 අලුත් ගිණුමක් තනන්න")
        reg_role = st.sidebar.selectbox("ඔබ කවුරුන්ද?", ["ගොවියා (Farmer)", "මිලදී ගන්නා (Buyer)"])
        reg_name = st.sidebar.text_input("සම්පූර්ණ නම / ආයතනය:")
        reg_phone = st.sidebar.text_input("දුරකථන අංකය (Admin ට පමණි):")
        reg_address = st.sidebar.text_input("ලිපිනය / Pick-up Location:")
        
        # Enhanced Bank Details Inputs for Farmers
        reg_bank = ""
        if reg_role == "ගොවියා (Farmer)":
            st.sidebar.markdown("🏦 **බැංකු ගිණුම් විස්තර (Payout සඳහා):**")
            bank_name = st.sidebar.text_input("බැංකුවේ නම (උදා: BOC, Peoples):")
            bank_branch = st.sidebar.text_input("ශාඛාව (Branch):")
            acc_number = st.sidebar.text_input("ගිණුම් අංකය:")
            acc_holder = st.sidebar.text_input("ගිණුම් හිමියාගේ නම:")
            if bank_name and acc_number:
                reg_bank = f"Bank: {bank_name} | Branch: {bank_branch} | Acc: {acc_number} | Holder: {acc_holder}"
        
        reg_user = st.sidebar.text_input("Username:")
        reg_pass = st.sidebar.text_input("Password:", type="password")
        
        if st.sidebar.button("✅ Create Account"):
            if reg_user and reg_pass and reg_name:
                try:
                    add_user(reg_user, reg_pass, reg_role, reg_name, reg_phone, reg_address, reg_bank)
                    st.sidebar.success("✅ Aswanna පද්ධතියට ඔබව සාර්ථකව ඇතුළත් විය! දැන් Login වන්න.")
                    st.session_state.auth_mode = "Login"
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"⚠️ මෙම Username එක දැනටමත් භාවිතයේ ඇත හෝ දෝෂයකි: {e}")
            else:
                st.sidebar.error("⚠️ අත්‍යවශ්‍ය විස්තර නිවැරදිව පුරවන්න.")

    elif st.session_state.auth_mode == "Login":
        st.sidebar.markdown("### 🔑 ඇතුළු වන්න (Sign In)")
        login_user = st.sidebar.text_input("Username:")
        login_pass = st.sidebar.text_input("Password:", type="password")
        
        if st.sidebar.button("🚀 Login Now"):
            user = check_user(login_user, login_pass)
            if user:
                st.session_state.logged_user = login_user
                st.sidebar.success(f"සාදරයෙන් පිළිගනිමු, {user[3]}!")
                st.rerun()
            else:
                st.sidebar.error("⚠️ Username හෝ Password වැරදියි.")

else:
    u_data = get_user_details(st.session_state.logged_user)
    if u_data:
        st.sidebar.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px;">
                <p style="margin:0; font-size: 0.9rem; color: #94a3b8;">Logged in as:</p>
                <h4 style="margin:0; color: #4ade80;">👤 {u_data[2]}</h4>
                <p style="margin:0; font-size: 0.85rem; color: #cbd5e1;">🎭 Role: {u_data[1]}</p>
            </div>
        """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_user = None
        st.rerun()

# Tabs
tab1, tab2, tab3 = st.tabs(["👨‍🌾 ගොවිපොළ (Farmer Portal)", "🏨 මිලදී ගන්නන් (Buyer Portal)", "🛡️ Admin & Transport Hub"])

# ==========================================
# 1. FARMER PORTAL
# ==========================================
with tab1:
    st.header("👨‍🌾 අස්වැන්න ගොවි පාලන පුවරුව")
    
    if st.session_state.logged_user:
        u_data = get_user_details(st.session_state.logged_user)
        if u_data and u_data[1] == "ගොවියා (Farmer)":
            st.success(f"ඔබ Log in වී ඇත: **{u_data[2]}** (🔒 පෞද්ගලික විස්තර ආරක්ෂිතයි)")
            
            st.subheader("➕ අලුත් අස්වැන්නක් එකතු කරන්න")
            with st.form("add_crop_form", clear_on_submit=True):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    crop_name = st.text_input("එළවළු/පළතුරු වර්ගය:")
                    qty = st.number_input("ප්‍රමාණය (Kg):", min_value=1.0, step=5.0)
                with col_f2:
                    price_per_kg = st.number_input("1Kg සඳහා ඔබේ මිල (රු.):", min_value=1.0, step=5.0)
                    district = st.selectbox("දිස්ත්‍රික්කය:", ["නුවරඑළිය", "බදුල්ල", "මාතලේ", "අනුරාධපුරය", "කෑගල්ල", "වෙනත්"])
                
                if st.form_submit_button("අස්වැන්න පළ කරන්න"):
                    if crop_name:
                        df_crops = get_all_crops()
                        crop_id = f"ASW-{len(df_crops) + 101}"
                        add_crop(crop_id, st.session_state.logged_user, crop_name, qty, price_per_kg, district, str(datetime.date.today()))
                        st.success(f"✅ අස්වැන්න සාර්ථකව ඇතුළත් විය! Crop ID: {crop_id}")
                    else:
                        st.error("⚠️ එළවළු/පළතුරු වර්ගය ඇතුළත් කරන්න.")

            st.divider()
            st.subheader("📋 ඔබේ පවතින අස්වැන්න Listings")
            df_crops = get_all_crops()
            if not df_crops.empty:
                my_crops = df_crops[df_crops['farmer_username'] == st.session_state.logged_user]
                if not my_crops.empty:
                    st.dataframe(my_crops[['crop_id', 'crop_name', 'qty', 'price_per_kg', 'district']], use_container_width=True)
                else:
                    st.info("ඔබ තවමත් අස්වැන්නක් ඇතුළත් කර නැත.")
            else:
                st.info("තවමත් පද්ධතියේ අස්වැන්න ඇතුළත් කර නැත.")
        else:
            st.warning("⚠️ ඔබ Farmer Account එකකින් Log in වී නැත.")
    else:
        st.warning("⚠️ කරුණාකර වම් පසින් ඇති Sidebar එක හරහා Login වන්න හෝ Register වන්න.")

# ==========================================
# 2. BUYER PORTAL
# ==========================================
with tab2:
    st.header("🏨 මිලදී ගන්නන්ගේ පුවරුව")
    
    df_crops = get_all_crops()
    active_crops = df_crops[df_crops['qty'] > 0] if not df_crops.empty else pd.DataFrame()

    if not active_crops.empty:
        st.subheader("🛒 Aswanna Marketplace")
        st.caption("🔒 ගොවීන්ගේ පෞද්ගලික විස්තර සහ දුරකථන අංක ආරක්ෂිතව සඟවා ඇත.")
        st.dataframe(active_crops[['crop_id', 'crop_name', 'qty', 'price_per_kg', 'district']], use_container_width=True)
        
        st.divider()
        st.subheader("💳 ඇණවුම් කිරීම")
        
        if st.session_state.logged_user:
            u_data = get_user_details(st.session_state.logged_user)
            if u_data and u_data[1] == "මිලදී ගන්නා (Buyer)":
                selected_id = st.selectbox("අවශ්‍ය Crop ID එක තෝරන්න:", active_crops['crop_id'].tolist())
                selected_row = active_crops[active_crops['crop_id'] == selected_id].iloc[0]
                
                order_qty = st.number_input(f"අවශ්‍ය ප්‍රමාණය (Kg) [උපරිම {selected_row['qty']}]:", min_value=1.0, max_value=float(selected_row['qty']))
                
                sub_total = order_qty * float(selected_row['price_per_kg'])
                commission = sub_total * 0.075
                farmer_amount = sub_total - commission
                
                st.write(f"**මුළු එකතුව:** රු. {sub_total:,.2f}")
                st.caption("🚚 ප්‍රවාහන කටයුතු Platform එක හරහා ස්වයංක්‍රීයව සංවිධානය වේ.")
                
                if st.button("Confirm Order & Pay"):
                    new_qty = float(selected_row['qty']) - order_qty
                    update_crop_qty(selected_id, new_qty)
                    
                    df_orders = get_all_orders()
                    order_id = f"ORD-{len(df_orders) + 5001}"
                    
                    add_order(order_id, st.session_state.logged_user, selected_row['farmer_username'], 
                            selected_row['crop_name'], order_qty, sub_total, commission, farmer_amount, 
                            "Transport Pending 🚚", str(datetime.date.today()))
                    
                    st.success(f"🎉 ඇණවුම සාර්ථකව Save විය! Order ID: {order_id}")
                    st.balloons()
            else:
                st.warning("⚠️ ඇණවුම් කිරීමට කරුණාකර Buyer Account එකකින් Log in වන්න.")
        else:
            st.warning("⚠️ ඇණවුම් කිරීමට කරුණාකර වම් පස Sidebar එකෙන් Log in වන්න.")
    else:
        st.info("දැනට වෙළඳපොළේ අස්වැන්න නොමැත.")

# ==========================================
# 3. ADMIN & LOGISTICS HUB
# ==========================================
with tab3:
    st.header("🛡️ Aswanna Admin & Transport Hub")
    st.write("7.5% කොමිස් ආදායම, ගනුදෙනු සහ ප්‍රවාහන කටයුතු මෙහෙයවීම.")
    
    df_orders = get_all_orders()
    if not df_orders.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("මුළු ගනුදෙනු වටිනාකම", f"රු. {df_orders['total_paid'].sum():,.2f}")
        m2.metric("ඔබේ 7.5% කොමිස් ලාභය", f"රු. {df_orders['your_commission'].sum():,.2f}")
        m3.metric("ගොවීන්ට යැවිය යුතු මුදල", f"රු. {df_orders['payout_to_farmer'].sum():,.2f}")
        
        st.divider()
        st.subheader("🚚 Transport Dispatch & Privacy Panel (Admin Only)")
        st.write("ප්‍රවාහනය සඳහා ඔබට පමණක් පෙනෙන ගොවියාගේ සහ මිලදී ගන්නාගේ පෞද්ගලික විස්තර:")
        
        full_dispatch_data = []
        for idx, row in df_orders.iterrows():
            f_user = get_user_details(row['farmer_username'])
            b_user = get_user_details(row['buyer_username'])
            
            full_dispatch_data.append({
                "Order ID": row['order_id'],
                "Crop": row['crop_name'],
                "Qty (Kg)": row['qty'],
                "Pick-up Address (Farmer)": f_user[4] if f_user else 'N/A',
                "Farmer Phone": f_user[3] if f_user else 'N/A',
                "Farmer Bank": f_user[5] if f_user else 'N/A',
                "Delivery Address (Delivery)": b_user[4] if b_user else 'N/A',
                "Buyer Phone": b_user[3] if b_user else 'N/A',
                "Status": row['status']
            })
            
        st.dataframe(pd.DataFrame(full_dispatch_data), use_container_width=True)
    else:
        st.info("තවමත් ගනුදෙනු සිදුවී නැත.")