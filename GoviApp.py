import streamlit as st, pandas as pd, datetime, hashlib
import bcrypt
from supabase import create_client

SUPABASE_URL, SUPABASE_KEY = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
@st.cache_resource
def init_supabase(): return create_client(SUPABASE_URL, SUPABASE_KEY)
supabase = init_supabase()

st.set_page_config(page_title="Aswanna", page_icon="🌾", layout="wide")

# bcrypt හරහා මුරපද සුරක්ෂිත කිරීම (Hashing & Verification)
hash_p = lambda p: bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
verify_p = lambda p, hashed: bcrypt.checkpw(p.encode('utf-8'), hashed.encode('utf-8'))

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
                elif tbl == "drivers": role = "රියදුරු (Driver)"
                elif tbl == "farmers" and not role: role = "විකුණුම්කරු (Seller)"
                elif tbl == "buyers" and not role: role = "ගැණුම්කරු (Buyer)"
                return (d["username"], role, d["name"], d.get("phone"), d.get("address"), d.get("bank"), d.get("profile_image_url"))
        except:
            continue
    return None

def upload_img(f, path):
    if not f: return ""
    # ගොනු ප්‍රමාණය 1MB (1,048,576 bytes) ට වඩා වැඩිදැයි පරීක්ෂා කිරීම (File Size Validation)
    if f.size > 1048576:
        st.error("ගොනුවේ ප්‍රමාණය 1MB ට වඩා වැඩි වේ. කරුණාකර කුඩා පින්තූරයක් ඇතුළත් කරන්න.")
        return None
    fp = f"{path}_{f.name}"
    supabase.storage.from_("profile-pictures").upload(fp, f.getvalue(), file_options={"upsert": "true"})
    return supabase.storage.from_("profile-pictures").get_public_url(fp)

# --- අනාගත රිෆන්ඩ් පාලනය සඳහා වන මූලික ලොජික් එක ---
def check_refund_eligibility(user_request_days, refund_policy_limit=3):
    """
    අපේ කොන්දේසි වලට එකඟ නම් පමණක් True ලබා දේ (උදා: දින 3කට වඩා අඩු නම්).
    අනාගතයේදී PayHere Refund API එක සමඟ මේක සම්බන්ධ කළ හැක.
    """
    if user_request_days <= refund_policy_limit:
        return True  # කොන්දේසි වලට එකඟයි, ඔටෝ රිෆන්ඩ් කළ හැක
    return False     # අනුමැතිය සඳහා මැනුවල් රිවිව් වෙත යැවිය යුතුය

st.markdown("""
<style>
.stApp { background-color: #0f172a; color: #f8fafc; } 
.hero { 
    background: linear-gradient(rgba(15,23,42,0.5), rgba(15,23,42,0.75)), url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=1600&q=80'); 
    background-size: cover; 
    background-position: center;
    padding: 70px 40px; 
    border-radius: 18px; 
    margin-bottom: 25px; 
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(74, 222, 128, 0.2);
}
</style>
""", unsafe_allow_html=True)

if 'logged_user' not in st.session_state: st.session_state.logged_user = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = "Login"

st.markdown('<div class="hero"><h1 style="color: #4ade80; font-size: 2.8rem; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🌾 ASWANNA (අස්වැන්න)</h1><p style="color: #cbd5e1; font-size: 1.1rem; margin-top: 5px;">ශ්‍රී ලංකාවේ විශ්වාසනීය B2B AgTech වෙළඳපොළ</p></div>', unsafe_allow_html=True)
st.sidebar.markdown('### 🔐 ASWANNA PORTAL')

if not st.session_state.logged_user:
    c1, c2 = st.sidebar.columns(2)
    if c1.button("🔑 Login"): st.session_state.auth_mode = "Login"; st.rerun()
    if c2.button("📝 Register"): st.session_state.auth_mode = "Register"; st.rerun()
    
    if st.session_state.auth_mode == "Register":
        r_role = st.sidebar.selectbox("භූමිකාව:", ["විකුණුම්කරු (Seller)", "ගැණුම්කරු (Buyer)", "රියදුරු (Driver)"])
        r_name, r_phone, r_addr = st.sidebar.text_input("නම:"), st.sidebar.text_input("දුරකථනය:"), st.sidebar.text_input("ලිපිනය:")
        
        r_pic = st.sidebar.file_uploader("Profile Pic (Maximum 1MB):", type=["jpg", "png", "jpeg"])
        st.sidebar.caption("⚠️ Maximum file size: 1MB | JPG, PNG")
        
        r_bank = ""
        if "විකුණුම්කරු" in r_role or "රියදුරු" in r_role:
            bn, bbr, acc, ah = st.sidebar.text_input("බැංකුව:"), st.sidebar.text_input("ශාඛාව:"), st.sidebar.text_input("ගිණුම:"), st.sidebar.text_input("හිමියා:")
            if bn and acc: r_bank = f"Bank: {bn} | Branch: {bbr} | Acc: {acc} | Holder: {ah}"
            r_v_type, r_v_no, r_max_load, r_license = "", "", "", ""
        if "රියදුරු" in r_role:
            r_district = st.sidebar.selectbox("සේවය කරන දිස්ත්‍රික්කය:", [
                "කොළඹ", "ගම්පහ", "කළුතර", 
                "මහනුවර", "මාතලේ", "නුවරඑළිය", 
                "ගාල්ල", "මාතර", "හම්බන්තොට", 
                "යාපනය", "කිලිනොච්චිය", "මන්නාරම", "වවුනියාව", "මුලතිව්", 
                "මඩකලපුව", "අම්පාර", "ත්‍රිකුණාමලය", 
                "කුරුණෑගල", "පුත්තලම", 
                "අනුරාධපුරය", "පොළොන්නරුව", 
                "බදුල්ල", "මොණරාගල", 
                "රත්නපුර", "කෑගල්ල"
            ], key="driver_reg_district")
            r_v_type = st.sidebar.selectbox("වාහන වර්ගය:", [
                "ත්‍රීරෝද රථ (Three-Wheeler)",
                "ඩීමෝ බට්ටා / කුඩා ලොරි (Mini Truck/Dimo Batta)",
                "මධ්‍යම ප්‍රමාණයේ ලොරි (Medium Lorry)",
                "සිසිල් කළ වාහන (Refrigerated Truck)"
            ])
            r_v_no = st.sidebar.text_input("වාහන අංකය (උදා: WP-ABC-1234):")
            r_max_load = st.sidebar.text_input("රැගෙන යා හැකි උපරිම බර (උදා: 1000 kg):")
            r_license = st.sidebar.text_input("රියදුරු බලපත්‍ර අංකය:")
        r_user, r_pass = st.sidebar.text_input("Username:"), st.sidebar.text_input("Password:", type="password")
        if st.sidebar.button("✅ Register"):
            if r_user and r_pass and r_name:
                try:
                    img_url = upload_img(r_pic, f"{r_user}_profile") if r_pic else ""
                    if r_pic and img_url == "":
                        st.stop()
                    tbl = "farmers" if "විකුණුම්කරු" in r_role else ("drivers" if "රියදුරු" in r_role else "buyers")
                    
                    supabase.table(tbl).insert({
                        "username": r_user, 
                        "password": hash_p(r_pass), 
                        "role": r_role, 
                        "name": r_name, 
                        "phone": r_phone, 
                        "address": r_addr, 
                        "bank": r_bank, 
                        "profile_image_url": img_url,
                        "v_type": r_v_type,
                        "v_number": r_v_no,
                        "max_load": r_max_load,
                        "license_no": r_license
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
                    res = supabase.table(tbl).select("*").eq("username", l_user).execute()
                    if res.data: 
                        db_pass = res.data[0].get("password")
                        if db_pass and verify_p(l_pass, db_pass):
                            st.session_state.logged_user = l_user
                            logged_success = True
                            st.rerun()
                except:
                    continue
            if not logged_success:
                st.sidebar.error("වැරදියි.")
else:
    u_data = get_user_details(st.session_state.logged_user)
    if u_data: st.sidebar.markdown(f"👤 **{u_data[2]}** ({u_data[1]})")
    if st.sidebar.button("🚪 Logout"): st.session_state.logged_user = None; st.rerun()

st.sidebar.markdown("---")
page = st.sidebar.selectbox("📖 නීති සහ ප්‍රතිපත්ති (Policies)", ["Home", "Terms & Conditions", "Privacy Policy"])

with st.expander("📖 ඔබගේ සාර්ථක ගනුදෙනුව උදෙසා - නිල උපදෙස් පත්‍රිකාව (කරුණාකර කියවා අවබෝධ කරගන්න)", expanded=False):
    st.markdown("""
    > **ඔබගේ සාර්ථක ගනුදෙනුව උදෙසා, ගනුදෙනුවට පෙර පහත උපදෙස් පත්‍රිකාව අවධානයෙන් කියවා අවබෝධ කරගන්න.**
    
    ---
    
    #### **1. විකුණුම්කරුවන් (ගොවීන්) සඳහා විශේෂ උපදෙස්:**
    * **මුදල් නිදහස් වීම (Payout Process):** ඔබ අලෙවි කළ නිෂ්පාදනයට අදාළ 70% ක මුදල ඔබගේ බැංකු ගිණුමට බැර වන්නේ, ගැණුම්කරු විසින් භාණ්ඩය ලබාගෙන මුළු ගනුදෙනුවම සාර්ථකව අවසන් කළ **පසු** පද්ධතියේ ඇති **"Complete" (සම්පූර්ණයි)** බොත්තම එබීමෙන් පසුව පමණි.
    * **ගැණුම්කරු සක්‍රීයව තබා ගැනීම:** යම් හෙයකින් නිෂ්පාදනය ලබා දී මුදල් ලැබීම ප්‍රමාද වන්නේ නම්, පද්ධතිය හරහා ලැබී ඇති ගැණුම්කරුගේ දුරකථන අංකයට ඇමතුමක් ලබා දී අදාළ ගනුදෙනුව පද්ධතිය තුළ **"Complete"** කරන ලෙස සුහදව මතක් කර දෙන්න.
    * **නිෂ්පාදනවල ගුණාත්මකභාවය සහ විශ්වාසනීයත්වය:** විකුණුම්කරුවන් සහ පද්ධතිය අතර පවතින අන්యోන්‍ය විශ්වාසය රැකගැමීමේ අරමුණින්, සෑම විටම උසස් ප්‍රමිතියෙන් යුත්, නැවුම් සහ පරිශීලනයට සුදුසු නියමිත තත්ත්වයේ පවතින භාණ්ඩ පමණක් පද්ධතියට එකතු කිරීම අනිවාර්ය වේ.
    * **භාණ්ඩ ලැයිස්තුගත කිරීමේ කාල සීමාව (Auto-Expiry):** ගැණුම්කරුවන්ට සැමවිටම නැවුම් සහ උසස් තත්ත්වයේ භාණ්ඩ ලබා දීම තහවුරු කිරීම සඳහා, ඔබ විසින් පද්ධතියට එකතු කරනු ලබන සෑම භාණ්ඩයක්ම පැය 48 ක කාලයක් ඇතුළත ස්වයංක්‍රීයව පද්ධතියෙන් ඉවත් වී යනු ඇත.

    #### **2. ගැණුම්කරුවන් සඳහා විශේෂ උපදෙස්:**
    * **ගනුදෙනුව අවසන් කර තහවුරු කිරීම:** ඔබට අදාළ අස්වැන්න ලැබී, ගනුදෙනුව සම්පූර්ණයෙන්ම අවසන් වූ පසු පද්ධතියේ ඇති **"Complete"** බොත්තම ඔබන්න. ඔබ එම බොත්තම එබූ සැනින් පද්ධතිය හරහා ගොවියාට හිමි මුදල් ස්වයංක්‍රීයව නිදහස් වේ.
    * **නව මිලදී ගැනීම් සඳහා සීමාව:** ගැණුම්කරුවෙකු ලෙස කටයුතු කරන ඔබට තවත් නව මිලදී ගැනීමක් සිදු කිරීමට හැකි වන්නේ, ඔබ දැනට නිරතව සිටින සක්‍රීය ගනුදෙනුව **"Complete"** කර අවසන් කිරීමෙන් පසුව පමණි.

    #### **3. පොදු උපදෙස් (දෙපාර්ශ්වයටම):**
    * **සන්නිවේදනය සහ පද්ධතියේ වගකීම් සීමාව:** ඇණවුමක් "Pending" තත්ත්වයේ පවතින අවස්ථාවන්හිදී පමණක් ගැණුම්කරු සහ විකුණුම්කරු අතර අදාළ දුරකථන අංක එකිනෙකට දර්ශනය වේ. මෙම පද්ධතිය මඟින් සිදු කරනු ලබන්නේ දිවයින පුරා සිටින විකුණුම්කරුවන් සහ ගැණුම්කරුවන් එකිනෙකට සම්බන්ධ කර දීම (Connecting Platform) පමණක් වන අතර, භාණ්ඩ ප්‍රවාහනය (Transport), බෙදාහැරීම හෝ එහි ගුණාත්මකභාවය සම්බන්ධයෙන් පද්ධතිය කිසිදු වගකීමක් දරනු නොලැබේ. ඒ නිසා, ප්‍රවාහන කටයුතු සහ අනෙකුත් අවශ්‍ය තොරතුරු සාකච්ඡා කර එකඟතාවකට පැමිණීම සඳහා ඉහත දුරකථන අංක භාවිත කරන මෙන් ඉල්ලා සිටිමු.
    """)

if page == "Terms & Conditions":
    st.title("📜 Terms & Conditions (භාවිතයේ කොන්දේසි)")
    st.write("""
    **භාවිතයේ කොන්දේසි:**
    * **සේවාව:** කෘෂිකාර්මික තොරතුරු සහ තාක්ෂණික සහය ලබා දීම.
    * **ගිණුම් ආරක්ෂාව:** පරිශීලක තොරතුරු නිවැරදි විය යුතු අතර ගිණුමේ ආරක්ෂාවට පරිශීලකයා වගකිව යුතුය.
    * **ගෙවීම් සහ රිෆන්ඩ්:** PayHere හරහා කරන ගෙවීම් ආරක්ෂිත වන අතර, මුදල් ආපසු ගෙවීම් (Refunds) අපගේ කොන්දේසි සහ ආයතනික ප්‍රතිපත්ති යටතේ ස්වයංක්‍රීයව හෝ මැනුවල් පරීක්ෂාවකින් පසු සලකා බලනු ලැබේ.
    * **වගකීම:** හදිසි තාක්ෂණික බාධාවකදී වේදිකාව වගකීමක් දරනු නොලැබේ.
    """)

elif page == "Privacy Policy":
    st.title("🔒 Privacy Policy (පෞද්ගලිකත්ව ප්‍රතිපත්තිය)")
    st.write("""
    **පෞද්ගලිකත්ව ප්‍රතිපත්තිය:**
    * **රැස්කරන දත්ත:** නම, දුරකථන අංකය, ඊමේල් සහ ගනුදෙනු විස්තර පමණි.
    * **භාවිතය:** සේවාවන් දියුණු කිරීමට සහ පාරිභෝගික සහය සඳහා පමණක් භාවිත කෙරේ. බාහිර පාර්ශ්වයන්ට ලබා නොදේ.
    * **ගෙවීම් ආරක්ෂාව:** PayHere හරහා සංකේතනය (Encrypted) කර සිදු කෙරේ; කාඩ්පත් අංක ගබඩා නොකෙරේ.
    * **සුරක්ෂිතභාවය:** දත්ත ආරක්ෂාවට නවීන තාක්ෂණික ක්‍රමවේද අනුගමනය කෙරේ.
    """)

else:
    user_role = ""
    if st.session_state.logged_user:
        u_info = get_user_details(st.session_state.logged_user)
        if u_info: user_role = u_info[1]

    if not st.session_state.logged_user:
        tab_list = ["🏨 ගැණුම්කරු (ප්‍රදර්ශනය)", "👤 Profile"]
        t_buyer, t_profile = st.tabs(tab_list)
        t_farmer, t_driver, t_admin = None, None, None
    elif "විකුණුම්කරු" in user_role:
        t_farmer, t_profile = st.tabs(["👨‍🌾 විකුණුම්කරු පාලන පුවරුව", "👤 Profile"])
        t_buyer, t_driver, t_admin = None, None, None
    elif "ගැණුම්කරු" in user_role:
        t_buyer, t_profile = st.tabs(["🏨 ගැණුම්කරු පාලන පුවරුව", "👤 Profile"])
        t_farmer, t_driver, t_admin = None, None, None
    elif "රියදුරු" in user_role:
        t_driver, t_profile = st.tabs(["🚗 රියදුරු පාලන පුවරුව", "👤 Profile"])
        t_farmer, t_buyer, t_admin = None, None, None
    elif "Admin" in user_role:
        t_admin, t_profile = st.tabs(["🛠️ Admin පාලන පුවරුව", "👤 Profile"])
        t_farmer, t_buyer, t_driver = None, None, None
    else:
        t_buyer, t_profile = st.tabs(["🏨 ගැණුම්කරු", "👤 Profile"])
        t_farmer, t_driver, t_admin = None, None, None

    if 't_farmer' in locals() and t_farmer is not None:
        with t_farmer:
            st.header("👨‍🌾 විකුණුම්කරු පාලන පුවරුව")
            with st.form("c_form", clear_on_submit=True):
                cn, qty, ppd, dist = st.text_input("එළවළු/පළතුරු නම:"), st.number_input("ප්‍රමාණය (Kg):", 1.0), st.number_input("මිල (රු/Kg):", 1.0), st.selectbox("දිස්ත්‍රික්කය:", [
                    "කොළඹ", "ගම්පහ", "කළුතර", 
                    "මහනුවර", "මාතලේ", "නුවරඑළිය", 
                    "ගාල්ල", "මාතර", "හම්බන්තොට", 
                    "යාපනය", "කිලිනොච්චිය", "මන්නාරම", "වවුනියාව", "මුලතිව්", 
                    "මඩකලපුව", "අම්පාර", "ත්‍රිකුණාමලය", 
                    "කුරුණෑගල", "පුත්තලම", 
                    "අනුරාධපුරය", "පොළොන්නරුව", 
                    "බදුල්ල", "මොණරාගල", 
                    "රත්නපුර", "කෑගල්ල"
                ])
                st.markdown("📸 **අනිවාර්ය ඡායාරූප 3ක් ඇතුළත් කරන්න:**")
                img1, img2, img3 = st.file_uploader("1. ළඟින් ගත් පින්තූරය (Close-up)", type=["jpg","png","jpeg"]), st.file_uploader("2. සම්පූර්ණ ප්‍රමාණය (Full View)", type=["jpg","png","jpeg"]), st.file_uploader("3. ගුණාත්මකභාවය (Freshness)", type=["jpg","png","jpeg"])
                if st.form_submit_button("පළ කරන්න"):
                    if cn and img1 and img2 and img3:
                        u1 = upload_img(img1, "crops_1")
                        u2 = upload_img(img2, "crops_2")
                        u3 = upload_img(img3, "crops_3")
                        if not u1 or not u2 or not u3:
                            st.stop()
                        df_c = get_data("products")
                        cid = f"ASW-{len(df_c)+101}"
                        supabase.table("products").insert({"crop_id": cid, "farmer_username": st.session_state.logged_user, "crop_name": cn, "qty": qty, "price_per_kg": ppd, "district": dist, "img_close": u1, "img_full": u2, "img_quality": u3, "created_at": datetime.datetime.now().isoformat(), "date": str(datetime.date.today())}).execute()
                        st.success("සාර්ථකයි!")
                        st.rerun()
                    else: st.error("සියලු විස්තර සහ පින්තූර 3 අනිවාර්ය වේ.")
            df = get_data("products")
            if not df.empty: st.dataframe(df[df['farmer_username'] == st.session_state.logged_user], use_container_width=True)

    if 't_buyer' in locals() and t_buyer is not None:
        with t_buyer:
            st.header("🏨 ගැණුම්කරුවන්ගේ පුවරුව (Escrow & Quality Verified)")
            df_o = get_data("orders")
            active = df_o[(df_o['buyer_username'] == st.session_state.logged_user) & (df_o['status'] == 'Pending')] if st.session_state.logged_user and not df_o.empty else pd.DataFrame()

            if not active.empty:
                st.info("⚠️ ක්‍රියාත්මක ඇණවුමක් ඇත. එය අවසන් කරන තෙක් නව ඇණවුම් සීමා කර ඇත.")
                for _, row in active.iterrows():
                    st.markdown(f"**ඇණවුම:** {row['order_id']} | **භාණ්ඩය:** {row['crop_name']} ({row['qty']} Kg)")
                    f_det = get_user_details(row['farmer_username'])
                    st.success(f"📞 විකුණුම්කරු: {f_det[2] if f_det else ''} | දුරකථනය: **{f_det[3] if f_det else ''}**")
                    if st.button(f"✅ ගනුදෙනුව සම්පූර්ණයි (Complete) - {row['order_id']}", key=f"comp_{row['order_id']}"):
                        supabase.table("orders").update({"status": "Completed"}).eq("order_id", row['order_id']).execute()
                        if row.get('crop_id'): supabase.table("products").delete().eq("crop_id", row['crop_id']).execute()
                        st.success("ගනුදෙනුව සාර්ථකව අවසන් විය!")
                        st.rerun()
            else:
                df = get_data("products")
                valid = []
                if not df.empty:
                    now = datetime.datetime.now()
                    for _, r in df.iterrows():
                        try:
                            if not r.get('created_at') or (now - datetime.datetime.fromisoformat(r['created_at'])).total_seconds() <= 172800: valid.append(r)
                        except: valid.append(r)
                act = pd.DataFrame(valid) if valid else pd.DataFrame()
                act = act[act['qty'] > 0] if not act.empty else pd.DataFrame()

                if not act.empty:
                    for _, r in act.iterrows():
                        with st.expander(f"📦 {r['crop_name']} - {r['qty']} Kg | රු.{r['price_per_kg']}/Kg | දිස්ත්‍රික්කය: {r['district']} (ID: {r['crop_id']})"):
                            ic1, ic2, ic3 = st.columns(3)
                            with ic1: 
                                if r.get('img_close'): st.image(r['img_close'], caption="1. Close-up", use_container_width=True)
                            with ic2: 
                                if r.get('img_full'): st.image(r['img_full'], caption="2. Full View", use_container_width=True)
                            with ic3: 
                                if r.get('img_quality'): st.image(r['img_quality'], caption="3. Quality", use_container_width=True)

                    if st.session_state.logged_user and "ගැණුම්කරු" in user_role:
                        s_id = st.selectbox("Crop ID තෝරන්න:", act['crop_id'].tolist(), key="buyer_crop_select")
                        row = act[act['crop_id'] == s_id].iloc[0]
                        o_qty = st.number_input("ප්‍රමාණය (Kg):", 1.0, float(row['qty']), key="buyer_qty_input")
                        sub = o_qty * float(row['price_per_kg'])
                        app_comm = sub * 0.10
                        driver_payout = sub * 0.20
                        farmer_payout = sub * 0.70

                        st.markdown(f"💳 **ගෙවිය යුතු මුළු මුදල (Escrow):** රු. {sub:,.2f} *(App (10%): {app_comm:,.2f} | Driver (20%): {driver_payout:,.2f} | විකුණුම්කරුට (70%): {farmer_payout:,.2f})*")

                        if st.button("💳 මුදල් ගෙවා ඇණවුම් කරන්න", key="buyer_pay_btn"):
                            import random
                            
                            # 1. අදාළ දිස්ත්‍රික්කයේ සහ අවශ්‍ය බර රැගෙන යා හැකි රියදුරන් සෙවීම
                            drivers_df = get_data("drivers")
                            assigned_driver = ""
                            
                            if not drivers_df.empty and 'district' in drivers_df.columns:
                                # අදාළ දිස්ත්‍රික්කයට ගැලපෙන රියදුරන් ෆිල්ටර් කිරීම
                                matching_drivers = drivers_df[drivers_df['district'] == row['district']]
                                
                                # වාහනයේ උපරිම බර (max_load) සමඟ ඇණවුමේ බර (o_qty) සැසඳීම
                                valid_load_drivers = []
                                for _, drv in matching_drivers.iterrows():
                                    try:
                                        # drivers වගුවේ max_load එක "1000 kg" හෝ "1000" වැනි අගයක් විය හැකි නිසා අංකය පමණක් වෙන් කර ගැනීම
                                        max_l = float(''.join(filter(str.isdigit, str(drv.get('max_load', '0')))))
                                        
                                        # රියදුරුගේ උපරිම බර, ගැණුම්කරු ඇණවුම් කළ ප්‍රමාණයට වඩා වැඩි හෝ සමාන විය යුතුය
                                        if max_l >= o_qty:
                                            valid_load_drivers.append(drv['username'])
                                    except:
                                        # max_load එක අංකයකට හැරවීමේ ගැටළුවක් වුවහොත් ආරක්ෂිතව ලැයිස්තුවට එකතු කිරීම
                                        valid_load_drivers.append(drv['username'])
                                
                                if valid_load_drivers:
                                    # සුදුසු රියදුරන් ලැයිස්තුවෙන් කෙනෙකු අහඹු ලෙස (Randomly) තෝරා ගැනීම
                                    assigned_driver = random.choice(valid_load_drivers)
                                    
                            # 2. නිෂ්පාදන ප්‍රමාණය අඩු කිරීම
                            supabase.table("products").update({"qty": float(row['qty']) - o_qty}).eq("crop_id", s_id).execute()
                            
                            # 3. නව ඇණවුම ඇතුළත් කිරීම (ස්වයංක්‍රීයව තෝරාගත් රියදුරු සමඟ)
                            supabase.table("orders").insert({
                                "order_id": f"ORD-{len(df_o)+5001}", 
                                "crop_id": s_id, 
                                "buyer_username": st.session_state.logged_user, 
                                "farmer_username": row['farmer_username'], 
                                "crop_name": row['crop_name'], 
                                "qty": o_qty, 
                                "total_paid": sub, 
                                "your_commission": app_comm,      
                                "driver_payout": driver_payout,    
                                "payout_to_farmer": farmer_payout, 
                                "status": "Pending Driver Acceptance" if assigned_driver else "Pending", 
                                "driver_username": assigned_driver,
                                "date": str(datetime.date.today())
                            }).execute()
                            
                            if assigned_driver:
                                st.success(f"මුදල් Escrow වෙත ලැබුණි! අදාළ දිස්ත්‍රික්කයේ රියදුරු ({assigned_driver}) වෙත ඇණවුම යොමු කරන ලදී.")
                            else:
                                st.warning("මුදල් Escrow වෙත ලැබුණි! නමුත් එම දිස්ත්‍රික්කයේ රියදුරන් නොමැති බැවින් සාමාන්‍ය ක්‍රමයට ඇණවුම යොමු විය.")
                            st.rerun()
                    else: 
                        st.info("💡 ඇණවුම් කිරීමට කරුණාකර 'ගැණුම්කරු' ගිණුමකින් Login වන්න.")
                else: st.info("දැනට ඇණවුම් කිරීමට නැවුම් අස්වැන්නක් නැත.")            

    if 't_driver' in locals() and t_driver is not None:
        with t_driver:
            st.header("🚗 රියදුරු පාලන පුවරුව (Delivery Tracking)")
            
            # 1. driver_username == logged_user සහ status == 'Pending Driver Acceptance' වන ඇණවුම් ලබා ගැනීම
            df_orders = get_data("orders")
            pending_orders = pd.DataFrame()
            if not df_orders.empty and 'driver_username' in df_orders.columns and 'status' in df_orders.columns:
                pending_orders = df_orders[(df_orders['driver_username'] == st.session_state.logged_user) & (df_orders['status'] == 'Pending Driver Acceptance')]

            st.subheader("📦 ඔබට ලැබී ඇති නව ඇණවුම්")
            
            if pending_orders.empty:
                st.info("ඔබට දැනට ලැබී ඇති නව ඇණවුම් නොමැත.")
            else:
                for _, order in pending_orders.iterrows():
                    order_id = order["order_id"]
                    st.write("---")
                    st.write(f"**ඇණවුම් අංකය:** {order_id} | **නිෂ්පාදනය:** {order['crop_name']} | **දිස්ත්‍රික්කය:** {order.get('district', 'N/A')}")
                    
                    col1, col2 = st.columns(2)
                    
                    # "Accept" (භාර ගන්න) බොත්තම
                    with col1:
                        if st.button("භාර ගන්න (Accept)", key=f"accept_{order_id}"):
                            supabase.table("orders").update({"status": "Out for Delivery"}).eq("order_id", order_id).execute()
                            st.success("ඇණවුම භාර ගන්නා ලදී!")
                            st.rerun()
                    
                    # "Cancel / Reject" (ප්‍රතික්ෂේප කරන්න) බොත්තම
                    with col2:
                        if st.button("ප්‍රතික්ෂේප කරන්න (Reject)", key=f"reject_{order_id}"):
                            current_declined = order.get("declined_drivers") or []
                            if isinstance(current_declined, str):
                                import json
                                try:
                                    current_declined = json.loads(current_declined)
                                except:
                                    current_declined = []
                            
                            current_declined.append(st.session_state.logged_user)
                            
                            # එම දිස්ත්‍රික්කයේම වෙනත් රියදුරෙකුට ස්වයංක්‍රීයව යොමු කිරීම (Re-assign Logic)
                            # (නිෂ්පාදන වගුවෙන් හෝ ඇණවුමෙන් දිස්ත්‍රික්කය ලබා ගැනීම)
                            district = order.get("district")
                            if not district:
                                # නිෂ්පාදන වගුවෙන් දිස්ත්‍රික්කය සෙවීම
                                p_res = supabase.table("products").select("district").eq("crop_id", order.get("crop_id")).execute()
                                if p_res.data:
                                    district = p_res.data[0].get("district")
                            
                            drivers_res = supabase.table("drivers").select("username").eq("district", district).execute() if district else supabase.table("drivers").select("username").execute()
                            available_drivers = [d["username"] for d in drivers_res.data if d["username"] not in current_declined]
                            
                            update_data = {"declined_drivers": current_declined}
                            
                            if available_drivers:
                                next_driver = random.choice(available_drivers)
                                update_data["driver_username"] = next_driver
                                update_data["status"] = "Pending Driver Acceptance"
                                st.warning("ඇණවුම ප්‍රතික්ෂේප කළ අතර, එය වෙනත් රියදුරෙකු වෙත යොමු කරන ලදී.")
                            else:
                                update_data["driver_username"] = None
                                update_data["status"] = "No Drivers Available"
                                st.error("මෙම දිස්ත්‍රික්කයේ වෙනත් නිදහස් රියදුරන් නොමැත.")
                            
                            supabase.table("orders").update(update_data).eq("order_id", order_id).execute()
                            st.rerun()

            st.markdown("---")
            st.info("📍 විකුණුම්කරුගේ සිට ගැණුම්කරු වෙත භාණ්ඩ රැගෙන යාමේ මාර්ග සිතියම")

            import folium
            from streamlit_folium import st_folium

            farmer_loc = [6.9271, 79.8612]  
            buyer_loc = [7.2906, 80.6337]

            st.markdown("### 🗺️ ගමන් මාර්ග සිතියම (Live Route Map)")
            m = folium.Map(location=[6.9271, 79.8612], zoom_start=8)

            folium.Marker(location=farmer_loc, popup="<b>විකුණුම්කරු (Pickup)</b>", icon=folium.Icon(color="red", icon="shopping-cart")).add_to(m)
            folium.Marker(location=buyer_loc, popup="<b>ගැණුම්කරු (Dropoff)</b>", icon=folium.Icon(color="green", icon="user")).add_to(m)

            folium.plugins.AntPath(locations=[farmer_loc, buyer_loc], weight=5, color='blue', delay=400, dash_array=[10, 20]).add_to(m)
            st_folium(m, width=700, height=500)

    if 't_admin' in locals() and t_admin is not None:
        with t_admin:
            st.header("🛠️ Admin පාලන පුවරුව")
            st.success("ඔබ පද්ධති පරිපාලක (Admin) ලෙස සාර්ථකව පිවිස ඇත.")
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.subheader("📋 සියලුම ඇණවුම් (Orders)")
                df_all_orders = get_data("orders")
                if not df_all_orders.empty:
                    st.dataframe(df_all_orders, use_container_width=True)
                else:
                    st.info("ඇණවුම් කිසිවක් නොමැත.")
            with col_a2:
                st.subheader("📦 පවතින අස්වැන්න (Products)")
                df_all_prod = get_data("products")
                if not df_all_prod.empty:
                    st.dataframe(df_all_prod, use_container_width=True)
                else:
                    st.info("අස්වැන්න ලැයිස්තුගත කර නැත.")

    if 't_profile' in locals() and t_profile is not None:
        with t_profile:
            st.header("👤 පරිශීලක පැතිකඩ")
            if st.session_state.logged_user:
                u = get_user_details(st.session_state.logged_user)
                if u:
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if len(u) > 6 and u[6]: st.image(u[6], width=180)
                    with c2:
                        st.markdown(f"### නම: {u[2]}")
                        st.markdown(f"**Username:** {u[0]} | **Role:** {u[1]}")
                        st.markdown(f"**Phone:** {u[3] or 'N/A'} | **Address:** {u[4] or 'N/A'}")
                        if u[5]: st.markdown(f"**Bank:** {u[5]}")
            else: 
                st.warning("පැතිකඩ බැලීමට කරුණාකර Login වන්න.")

