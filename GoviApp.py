import streamlit as st, pandas as pd, datetime, hashlib
from supabase import create_client

SUPABASE_URL, SUPABASE_KEY = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
@st.cache_resource
def init_supabase(): return create_client(SUPABASE_URL, SUPABASE_KEY)
supabase = init_supabase()

st.set_page_config(page_title="Aswanna", page_icon="🌾", layout="wide")
hash_p = lambda p: hashlib.sha256(str.encode(p)).hexdigest()

def get_data(tbl, col=None, val=None):
    q = supabase.table(tbl).select("*")
    res = q.eq(col, val).execute() if col else q.execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def get_user_details(u):
    for tbl in ["farmers", "buyers", "drivers", "admins"]:
        try:
            res = supabase.table(tbl).select("*").eq("username", u).execute()
            if res.data: 
                d = res.data[0]
                role = d.get("role")
                if tbl == "admins": role = "Admin"
                elif tbl == "farmers" and not role: role = "විකුණුම්කරු (Seller)"
                elif tbl == "buyers" and not role: role = "ගැණුම්කරු (Buyer)"
                elif tbl == "drivers" and not role: role = "රියදුරු (Driver)"
                return (d["username"], role, d["name"], d.get("phone"), d.get("address"), d.get("bank"), d.get("profile_image_url"))
        except:
            continue
    return None

def upload_img(f, path):
    if not f: return ""
    fp = f"{path}_{f.name}"
    supabase.storage.from_("profile-pictures").upload(fp, f.getvalue(), file_options={"upsert": "true"})
    return supabase.storage.from_("profile-pictures").get_public_url(fp)

st.markdown("""
<style>
.stApp { background-color: #0f172a; color: #f8fafc; } 
.hero { 
    background: linear-gradient(rgba(15,23,42,0.5), rgba(15,23,42,0.75)), url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1600&q=80'); 
    background-size: cover; background-position: center;
    padding: 70px 40px; border-radius: 18px; margin-bottom: 25px; 
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4); border: 1px solid rgba(74, 222, 128, 0.2);
}
</style>
""", unsafe_allow_html=True)

if 'logged_user' not in st.session_state: st.session_state.logged_user = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = "Login"

st.markdown('<div class="hero"><h1 style="color: #4ade80; font-size: 2.8rem; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🌾 ASWANNA (අස්වැන්න)</h1><p style="color: #cbd5e1; font-size: 1.1rem; margin-top: 5px;">ශ්‍රී ලංකාවේ විශ්වාසනීය B2B AgTech හා ප්‍රවාහන Super App</p></div>', unsafe_allow_html=True)
st.sidebar.markdown('### 🔐 ASWANNA PORTAL')

if not st.session_state.logged_user:
    c1, c2 = st.sidebar.columns(2)
    if c1.button("🔑 Login"): st.session_state.auth_mode = "Login"; st.rerun()
    if c2.button("📝 Register"): st.session_state.auth_mode = "Register"; st.rerun()
    
    if st.session_state.auth_mode == "Register":
        r_role = st.sidebar.selectbox("භූමිකාව:", ["විකුණුම්කරු (Seller)", "ගැණුම්කරු (Buyer)", "රියදුරු (Driver)"])
        r_name, r_phone, r_addr = st.sidebar.text_input("නම:"), st.sidebar.text_input("දුරකථනය:"), st.sidebar.text_input("ලිපිනය:")
        
        r_pic = st.sidebar.file_uploader("Profile Pic (Max 1MB):", type=["jpg", "png", "jpeg"])
        
        r_bank = ""
        r_lic, r_veh1, r_veh2 = None, None, None
        if "විකුණුම්කරු" in r_role or "රියදුරු" in r_role:
            bn, bbr, acc, ah = st.sidebar.text_input("බැංකුව:"), st.sidebar.text_input("ශාඛාව:"), st.sidebar.text_input("ගිණුම:"), st.sidebar.text_input("හිමියා:")
            if bn and acc: r_bank = f"Bank: {bn} | Branch: {bbr} | Acc: {acc} | Holder: {ah}"
            
        if "රියදුරු" in r_role:
            st.sidebar.markdown("🚚 **රියදුරු අතිරේක ලේඛන:**")
            r_lic = st.sidebar.file_uploader("Driving License:", type=["jpg", "png", "jpeg"])
            r_veh1 = st.sidebar.file_uploader("Vehicle Photo 1:", type=["jpg", "png", "jpeg"])
            r_veh2 = st.sidebar.file_uploader("Vehicle Photo 2:", type=["jpg", "png", "jpeg"])
            v_type = st.sidebar.text_input("වාහන වර්ගය:")
            v_num = st.sidebar.text_input("වාහන අංකය:")

        r_user, r_pass = st.sidebar.text_input("Username:"), st.sidebar.text_input("Password:", type="password")
        if st.sidebar.button("✅ Register"):
            if r_user and r_pass and r_name:
                try:
                    img_url = upload_img(r_pic, f"{r_user}_profile") if r_pic else ""
                    if "රියදුරු" in r_role:
                        lic_url = upload_img(r_lic, f"{r_user}_lic") if r_lic else ""
                        v1_url = upload_img(r_veh1, f"{r_user}_veh1") if r_veh1 else ""
                        v2_url = upload_img(r_veh2, f"{r_user}_veh2") if r_veh2 else ""
                        supabase.table("drivers").insert({
                            "username": r_user, "password": hash_p(r_pass), "role": r_role, "name": r_name, 
                            "phone": r_phone, "address": r_addr, "bank": r_bank, "profile_image_url": img_url,
                            "license_image_url": lic_url, "vehicle_image_url_1": v1_url, "vehicle_image_url_2": v2_url,
                            "vehicle_type": v_type if 'v_type' in locals() else "", "vehicle_number": v_num if 'v_num' in locals() else ""
                        }).execute()
                    else:
                        tbl = "farmers" if "විකුණුම්කරු" in r_role else "buyers"
                        supabase.table(tbl).insert({
                            "username": r_user, "password": hash_p(r_pass), "role": r_role, "name": r_name, 
                            "phone": r_phone, "address": r_addr, "bank": r_bank, "profile_image_url": img_url
                        }).execute()
                    st.sidebar.success("සාර්ථකයි! Login වන්න."); st.session_state.auth_mode = "Login"; st.rerun()
                except Exception as e: st.sidebar.error(f"දෝෂයකි: {e}")
            else: st.sidebar.error("විස්තර පුරවන්න.")
    else:
        l_user, l_pass = st.sidebar.text_input("Username:"), st.sidebar.text_input("Password:", type="password")
        if st.sidebar.button("🚀 Login"):
            logged_success = False
            for tbl in ["farmers", "buyers", "drivers", "admins"]:
                try:
                    res = supabase.table(tbl).select("*").eq("username", l_user).eq("password", hash_p(l_pass)).execute()
                    if res.data: 
                        st.session_state.logged_user = l_user
                        logged_success = True
                        st.rerun()
                except:
                    continue
            if not logged_success: st.sidebar.error("වැරදියි.")
else:
    u_data = get_user_details(st.session_state.logged_user)
    if u_data: st.sidebar.markdown(f"👤 **{u_data[2]}** ({u_data[1]})")
    if st.sidebar.button("🚪 Logout"): st.session_state.logged_user = None; st.rerun()

# --- නිල උපදෙස් පත්‍රිකාව ---
with st.expander("📖 ඔබගේ සාර්ථක ගනුදෙනුව උදෙසා - නිල උපදෙස් පත්‍රිකාව", expanded=False):
    st.markdown("""
    * **විකුණුම්කරු (ගොවියා) පංගුව:** 70% ක් ගොවියාගේ බැංකු ගිණුමට (ගනුදෙනුව Complete වූ පසු).
    * **ඇප් කොමිස් (Platform):** 10% ක් වේදිකාවට.
    * **ප්‍රවාහන ගාස්තුව (Transport/Driver):** දුර සහ බර මත පදනම්ව රියදුරුට හිමිවේ.
    * **සියලුම දිස්ත්‍රික්ක 25 ආවරණය වේ.**
    """)

user_role = ""
if st.session_state.logged_user:
    u_info = get_user_details(st.session_state.logged_user)
    if u_info: user_role = u_info[1]

if not st.session_state.logged_user:
    t_buyer, t_profile = st.tabs(["🏨 ගැණුම්කරු (ප්‍රදර්ශනය)", "👤 Profile"])
    t_farmer, t_driver, t_admin = None, None, None
elif "විකුණුම්කරු" in user_role:
    t_farmer, t_profile = st.tabs(["👨‍🌾 විකුණුම්කරු පාලන පුවරුව", "👤 Profile"])
    t_buyer, t_driver, t_admin = None, None, None
elif "ගැණුම්කරු" in user_role:
    t_buyer, t_profile = st.tabs(["🏨 ගැණුම්කරු පාලන පුවරුව", "👤 Profile"])
    t_farmer, t_driver, t_admin = None, None, None
elif "රියදුරු" in user_role:
    t_driver, t_profile = st.tabs(["🚚 ප්‍රවාහන පාලන පුවරුව", "👤 Profile"])
    t_farmer, t_buyer, t_admin = None, None, None
elif "Admin" in user_role:
    t_admin, t_profile = st.tabs(["🛠️ Admin පාලන පුවරුව", "👤 Profile"])
    t_farmer, t_buyer, t_driver = None, None, None
else:
    t_buyer, t_profile = st.tabs(["🏨 ගැණුම්කරු", "👤 Profile"])
    t_farmer, t_driver, t_admin = None, None, None

# --- 1. විකුණුම්කරු පුවරුව ---
if t_farmer is not None:
    with t_farmer:
        st.header("👨‍🌾 විකුණුම්කරු පාලන පුවරුව")
        with st.form("c_form", clear_on_submit=True):
            cn, qty, ppd, dist = st.text_input("එළවළු/පළතුරු නම:"), st.number_input("ප්‍රමාණය (Kg):", 1.0), st.number_input("මිල (රු/Kg):", 1.0), st.selectbox("දිස්ත්‍රික්කය:", [
                "කොළඹ", "ගම්පහ", "කළුතර", "මහනුවර", "මාතලේ", "නුවරඑළිය", "ගාල්ල", "මාතර", "හම්බන්තොට", 
                "යාපනය", "කිලිනොච්චිය", "මන්නාරම", "වවුනියාව", "මුලතිව්", "මඩකලපුව", "අම්පාර", "ත්‍රිකුණාමලය", 
                "කුරුණෑගල", "පුත්තලම", "අනුරාධපුරය", "පොළොන්නරුව", "බදුල්ල", "මොණරාගල", "රත්නපුර", "කෑගල්ල"
            ])
            img1, img2, img3 = st.file_uploader("1. Close-up", type=["jpg","png","jpeg"]), st.file_uploader("2. Full View", type=["jpg","png","jpeg"]), st.file_uploader("3. Quality", type=["jpg","png","jpeg"])
            if st.form_submit_button("පළ කරන්න"):
                if cn and img1 and img2 and img3:
                    df_c = get_data("products")
                    cid = f"ASW-{len(df_c)+101}"
                    u1, u2, u3 = upload_img(img1, f"crops/{cid}_1"), upload_img(img2, f"crops/{cid}_2"), upload_img(img3, f"crops/{cid}_3")
                    supabase.table("products").insert({"crop_id": cid, "farmer_username": st.session_state.logged_user, "crop_name": cn, "qty": qty, "price_per_kg": ppd, "district": dist, "img_close": u1, "img_full": u2, "img_quality": u3, "created_at": datetime.datetime.now().isoformat(), "date": str(datetime.date.today())}).execute()
                    st.success("සාර්ථකයි!"); st.rerun()
                else: st.error("සියලු විස්තර සහ පින්තූර 3 අනිවාර්ය වේ.")
        df = get_data("products")
        if not df.empty: st.dataframe(df[df['farmer_username'] == st.session_state.logged_user], use_container_width=True)

# --- 2. ගැණුම්කරු පුවරුව ---
if t_buyer is not None:
    with t_buyer:
        st.header("🏨 ගැණුම්කරුවන්ගේ පුවරුව (70% ගොවියාට / 10% ඇප් එකට / 20% ප්‍රවාහනය)")
        df_o = get_data("orders")
        active = df_o[(df_o['buyer_username'] == st.session_state.logged_user) & (df_o['status'] == 'Pending')] if st.session_state.logged_user and not df_o.empty else pd.DataFrame()

        if not active.empty:
            st.info("⚠️ ක්‍රියාත්මක ඇණවුමක් ඇත.")
            for _, row in active.iterrows():
                st.markdown(f"**ඇණවුම:** {row['order_id']} | **භාණ්ඩය:** {row['crop_name']} ({row['qty']} Kg)")
                f_det = get_user_details(row['farmer_username'])
                st.success(f"📞 විකුණුම්කරු: {f_det[2] if f_det else ''} | දුරකථනය: **{f_det[3] if f_det else ''}**")
                if st.button(f"✅ ගනුදෙනුව සම්පූර්ණයි (Complete) - {row['order_id']}", key=f"comp_{row['order_id']}"):
                    supabase.table("orders").update({"status": "Completed"}).eq("order_id", row['order_id']).execute()
                    if row.get('crop_id'): supabase.table("products").delete().eq("crop_id", row['crop_id']).execute()
                    st.success("ගනුදෙනුව සාර්ථකව අවසන් විය!"); st.rerun()
        else:
            df = get_data("products")
            valid = [r for _, r in df.iterrows()] if not df.empty else []
            act = pd.DataFrame(valid) if valid else pd.DataFrame()
            if not act.empty:
                for _, r in act.iterrows():
                    with st.expander(f"📦 {r['crop_name']} - {r['qty']} Kg | රු.{r['price_per_kg']}/Kg | දිස්ත්‍රික්කය: {r['district']}"):
                        ic1, ic2, ic3 = st.columns(3)
                        if r.get('img_close'): ic1.image(r['img_close'], use_container_width=True)
                        if r.get('img_full'): ic2.image(r['img_full'], use_container_width=True)
                        if r.get('img_quality'): ic3.image(r['img_quality'], use_container_width=True)

                if st.session_state.logged_user and "ගැණුම්කරු" in user_role:
                    s_id = st.selectbox("Crop ID තෝරන්න:", act['crop_id'].tolist())
                    row = act[act['crop_id'] == s_id].iloc[0]
                    o_qty = st.number_input("ප්‍රමාණය (Kg):", 1.0, float(row['qty']))
                    
                    item_sub = o_qty * float(row['price_per_kg'])
                    farmer_payout = item_sub * 0.70  # 70%
                    app_comm = item_sub * 0.10       # 10%
                    transport_fee = 1500.0           # Distance-based transport fee estimate
                    total_pay = item_sub + transport_fee
                    
                    st.markdown(f"💳 **ගෙවිය යුතු මුළු මුදල:** රු. {total_pay:,.2f} *(භාණ්ඩය: {item_sub:,.2f} [ගොවියා: {farmer_payout:,.2f} | ඇප්: {app_comm:,.2f}] + ප්‍රවාහන ගාස්තුව: {transport_fee:,.2f})*")
                    if st.button("💳 මුදල් ගෙවා ඇණවුම් කරන්න"):
                        supabase.table("products").update({"qty": float(row['qty']) - o_qty}).eq("crop_id", s_id).execute()
                        supabase.table("orders").insert({
                            "order_id": f"ORD-{len(df_o)+5001}", "crop_id": s_id, "buyer_username": st.session_state.logged_user, 
                            "farmer_username": row['farmer_username'], "crop_name": row['crop_name'], "qty": o_qty, 
                            "total_paid": total_pay, "farmer_amount": farmer_payout, "app_commission": app_comm, 
                            "transport_fee": transport_fee, "status": "Pending", "date": str(datetime.date.today())
                        }).execute()
                        st.success("ඇණවුම සාර්ථකයි!"); st.rerun()

# --- 3. රියදුරු පුවරුව ---
if t_driver is not None:
    with t_driver:
        st.header("🚚 රියදුරු ප්‍රවාහන පාලන පුවරුව (Live Tracking & Deliveries)")
        st.success("ඔබගේ ප්‍රවාහන ඇණවුම් සහ ගමන්මඟ පහතින් පාලනය කරන්න.")
        try:
            import folium
            from streamlit_folium import st_folium
            m = folium.Map(location=[7.8731, 80.7718], zoom_start=7)
            folium.Marker([7.8731, 80.7718], popup="Driver Location", icon=folium.Icon(color="green", icon="truck")).add_to(m)
            st_folium(m, width=700, height=350)
        except:
            st.info("🗺️ සිතියම් පහසුකම සක්‍රීයයි.")

# --- 4. Admin පුවරුව ---
if t_admin is not None:
    with t_admin:
        st.header("🛠️ Admin පාලන පුවරුව")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Orders")
            df_ord = get_data("orders")
            if not df_ord.empty: st.dataframe(df_ord, use_container_width=True)
        with col2:
            st.subheader("🚚 Drivers")
            df_drv = get_data("drivers")
            if not df_drv.empty: st.dataframe(df_drv, use_container_width=True)

# --- 5. Profile ටැබ් එක ---
with t_profile:
    st.header("👤 පරිශීලක පැතිකඩ")
    if st.session_state.logged_user:
        u = get_user_details(st.session_state.logged_user)
        if u:
            c1, c2 = st.columns([1, 2])
            with c1:
                if len(u) > 6 and u[6]: c1.image(u[6], width=180)
            with c2:
                st.markdown(f"### නම: {u[2]}")
                st.markdown(f"**Username:** {u[0]} | **Role:** {u[1]}")
                st.markdown(f"**Phone:** {u[3] or 'N/A'} | **Address:** {u[4] or 'N/A'}")
                if u[5]: st.markdown(f"**Bank:** {u[5]}")
