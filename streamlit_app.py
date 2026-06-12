import streamlit as st
import os
import requests
import json
import uuid
import base64
import sqlite3
import re

# =====================================================================================================
# 🧠 --- AI Brain/Engine කොටස (කිසිදු වෙනසක් කර නොමැත) --- 🧠
# =====================================================================================================
class MockDelta:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.delta = MockDelta(content)
        self.message = MockDelta(content)

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class NativeGeminiCompletions:
    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, model, messages, stream=False, temperature=0.75):
        contents = []
        system_text = ""
        
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
            
        identity_prompt = "ඔබගේ නම 'Pradeep Hacx AI' වේ. ඔබව නිර්මාණය කළේ 'Pradeep Hacx' විසිනි. IMPORTANT: You are an AI assistant that MUST strictly reply in the Sinhala language (සිංහල). Never reply in English."
        
        if system_text:
            system_text = identity_prompt + "\n\n" + system_text
        else:
            system_text = identity_prompt
        
        if "active_parts" in st.session_state and st.session_state.active_parts:
            for item in reversed(contents):
                if item["role"] == "user":
                    item["parts"] = st.session_state.active_parts
                    break
            st.session_state.active_parts = None
        
        payload = {"contents": contents}
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if res.status_code == 503:
            raise Exception("Google සර්වර් මේ වෙලාවේ කාර්යබහුලයි (High Demand). තත්පර කිහිපයකින් නැවත උත්සාහ කරන්න.")
        elif res.status_code != 200:
            raise Exception(f"API Error {res.status_code}: {res.text}")
        
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return [MockResponse(text)] if stream else MockResponse(text)

class NativeClient:
    def __init__(self, api_key, **kwargs):
        class Chat:
            def __init__(self, key):
                self.completions = NativeGeminiCompletions(key)
        self.chat = Chat(api_key)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Pradeep Hacx AI", page_icon="👑", layout="centered", initial_sidebar_state="collapsed")

# 🔥 Secrets වලින් Admin විස්තර ගැනීම (GitHub එකේ පේන්නේ නෑ) 🔥
try:
    ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except KeyError:
    # Secrets දාලා නැත්නම් Default දේවල් ගනී (ආරක්ෂාවට Secrets දාන්නම ඕනේ)
    ADMIN_EMAIL = "admin@hacx.lk"
    ADMIN_PASSWORD = "1234"

# --- 🔥 UI CSS (අභ්‍යන්තර මෙනු සැඟවීම පමණක් සිදු කරයි) 🔥 ---
st.markdown("""
<style>
/* Main Streamlit internal elements */
header { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; visibility: hidden !important; }

/* Spacing Fix */
.block-container { padding-top: 1.5rem !important; padding-bottom: 5rem !important; }
code { font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; }

/* Title Styling */
.hacx-title {
    text-align: center;
    background: linear-gradient(90deg, #ff4b4b, #ff904f, #ff4b4b);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.2em;
    font-weight: 900;
    margin-bottom: 0px;
    padding-bottom: 0px;
    animation: shine 3s linear infinite;
}
@keyframes shine { to { background-position: 200% center; } }
.hacx-subtitle { text-align: center; color: #a0a0a0; font-size: 14px; margin-top: -5px; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

try:
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
    from hacxgpt.utils.security import Security
    import hacxgpt.core.brain as brain_module
    from dotenv import set_key
    Security.encrypt = lambda text: text
    Security.decrypt = lambda text: text
    brain_module.Client = NativeClient
except ImportError:
    pass

# =====================================================================================================
# 🔐 --- දත්ත සමුදාය (Database) --- 🔐
# =====================================================================================================

DB_FILE = "users.db"
CHAT_DIR = "user_chats"

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0 
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_user(email, phone, password):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, phone, password) VALUES (?, ?, ?)", (email.lower(), phone, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def verify_user(email, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, password, is_admin FROM users WHERE email=?", (email.lower(),))
    result = cursor.fetchone()
    conn.close()
    if result and result[1] == password:
        return {"email": result[0], "role_int": result[2]}
    return None

def find_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, phone FROM users WHERE email=?", (email.lower(),))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_users_for_admin():
    if st.session_state.user_role == 0:
        return []
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, phone, password, is_admin FROM users")
    result = cursor.fetchall()
    conn.close()
    return result

def delete_user_by_id(user_id):
    if st.session_state.user_role != 1: 
        return False
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id=?", (user_id,))
    email_res = cursor.fetchone()
    if email_res:
        email = email_res[0]
        safe_email = email.strip().lower().replace("@", "_at_").replace(".", "_dot_")
        user_dir = os.path.join(CHAT_DIR, safe_email)
        import shutil
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True

def update_user_password(user_id, new_password):
    if st.session_state.user_role == 0:
        return False
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    conn.commit()
    conn.close()
    return True

def update_user_role(user_id, role_int):
    if st.session_state.user_role != 1: 
        return False
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin=? WHERE id=?", (role_int, user_id))
    conn.commit()
    conn.close()
    return True

# --- 📩 Inbox/Notification System ---
def add_notification(target_email, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notifications (email, message) VALUES (?, ?)", (target_email.lower(), message))
    conn.commit()
    conn.close()

def get_admin_notifications():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, message FROM notifications WHERE email='admin' ORDER BY id DESC")
    result = cursor.fetchall()
    conn.close()
    return result

def get_user_notifications(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, message FROM notifications WHERE email=? ORDER BY id DESC", (email.lower(),))
    result = cursor.fetchall()
    conn.close()
    return result

def delete_notification(notif_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications WHERE id=?", (notif_id,))
    conn.commit()
    conn.close()

# --- Chat Memory ---
def get_user_dir(email):
    safe_email = email.strip().lower().replace("@", "_at_").replace(".", "_dot_")
    user_dir = os.path.join(CHAT_DIR, safe_email)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def load_chat(email, chat_id):
    file_path = os.path.join(get_user_dir(email), f"{chat_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_chat(email, chat_id, messages):
    file_path = os.path.join(get_user_dir(email), f"{chat_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_role = 0 
    st.session_state.saved_api_key = ""

# =====================================================================================================
# 🚪 --- UI: පිවිසුම් ද්වාරය --- 🚪
# =====================================================================================================

if not st.session_state.logged_in:
    st.markdown("<h1 class='hacx-title'>👑 Pradeep Hacx AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hacx-subtitle'>HacxGPT Secure Portal - ද්වාරය</p>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔐 පිවිසෙන්න", "➕ ලියාපදිංචි වන්න", "❓ මුරපදය අමතක නම්"])

    with tab1:
        st.subheader("ඇප් එකට පිවිසෙන්න")
        with st.form("login_form"):
            login_email = st.text_input("Email ලිපිනය", placeholder="example@mail.com")
            login_password = st.text_input("මුරපදය (Password)", type="password")
            submitted = st.form_submit_button("ඇතුලත් වන්න", use_container_width=True)
            
            if submitted:
                if login_email and login_password:
                    # 🔥 Secrets වලින් ගත්තු Admin ලොගින් එක 🔥
                    if login_email.lower() == ADMIN_EMAIL.lower() and login_password == ADMIN_PASSWORD:
                         st.session_state.logged_in = True
                         st.session_state.user_email = login_email
                         st.session_state.user_role = 1
                         st.session_state.current_chat_id = str(uuid.uuid4())
                         st.session_state.messages = []
                         st.rerun()
                    
                    user = verify_user(login_email, login_password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_email = user["email"]
                        st.session_state.user_role = user["role_int"]
                        st.session_state.current_chat_id = str(uuid.uuid4())
                        st.session_state.messages = []
                        st.rerun()
                    else:
                        st.error("⚠️ ඔබගේ Email ලිපිනය හෝ මුරපදය වැරදියි.")
                else:
                    st.warning("⚠️ කරුණාකර සියලුම තොරතුරු ඇතුලත් කරන්න.")

    with tab2:
        st.subheader("අලුත් එකවුන්ට් එකක් සාදන්න")
        with st.form("reg_form"):
            reg_email = st.text_input("ඔබගේ Email ලිපිනය")
            reg_phone = st.text_input("දුරකථන අංකය")
            reg_password = st.text_input("නව මුරපදය (Password)", type="password")
            confirm_password = st.text_input("මුරපදය නැවත ඇතුලත් කරන්න", type="password")
            submitted_reg = st.form_submit_button("ලියාපදිංචි වන්න", use_container_width=True)
            
            if submitted_reg:
                if reg_email and reg_phone and reg_password and confirm_password:
                    if reg_password != confirm_password:
                        st.error("⚠️ මුරපද දෙක නොගැලපේ.")
                    elif "@" not in reg_email or "." not in reg_email:
                        st.error("⚠️ වලංගු Email ලිපිනයක් ඇතුලත් කරන්න.")
                    else:
                        if add_user(reg_email, reg_phone, reg_password):
                            st.success("✅ ලියාපදිංචි වීම සාර්ථකයි. දැන් පිවිසුම් ටැබ් එකට ගොස් ඇතුලත් වන්න.")
                        else:
                            st.error("⚠️ මෙම Email ලිපිනය දැනටමත් ලියාපදිංචි වී ඇත.")
                else:
                    st.warning("⚠️ කරුණාකර සියලුම විස්තර පුරවන්න.")

    with tab3:
        st.subheader("මුරපදය අමතක වී ඇත්නම්...")
        st.info("කරුණාකර ඔබගේ ඊමේල් ලිපිනය ඇතුලත් කරන්න. අපි ඔබගේ ඉල්ලීම ඇඩ්මින් වෙත යොමු කරන්නෙමු.")
        with st.form("forgot_form"):
            check_email = st.text_input("ඔබ ලියාපදිංචි වූ Email ලිපිනය ඇතුලත් කරන්න")
            submitted_check = st.form_submit_button("ඇඩ්මින්ට දැනුම් දෙන්න")
            
            if submitted_check:
                user_info = find_user_by_email(check_email)
                if user_info:
                    st.success(f"ඔබගේ Phone අංකය: {user_info[1]}")
                    add_notification("admin", f"🔑 මුරපදය අමතක වීම: පරිශීලකයා ({check_email} | {user_info[1]}) හට මුරපදය අමතක වී ඇත.")
                    st.success("✅ ඇඩ්මින් වෙත පණිවිඩයක් යවන ලදී!")
                else:
                    st.error("⚠️ මෙම Email ලිපිනයෙන් පරිශීලකයෙකු හමු නොවීය.")

    st.stop() 

# =====================================================================================================
# 🖥️ --- ඇප් එකේ ප්‍රධාන UI (Login වුණාට පසු) --- 🖥️
# =====================================================================================================

st.markdown("<h1 class='hacx-title'>👑 Pradeep Hacx AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='hacx-subtitle'>© 2026 Owned & Developed by Pradeep Hacx. All Rights Reserved.</p>", unsafe_allow_html=True)

my_notifications = []
if st.session_state.user_role in [1, 2]:
    my_notifications = get_admin_notifications()
else:
    my_notifications = get_user_notifications(st.session_state.user_email)

if my_notifications:
    st.warning(f"🔔 **ඔබට කියවීමට අලුත් පණිවිඩ {len(my_notifications)} ක් ඇත!** කරුණාකර ඔබගේ පණිවිඩ ටැබ් එක පරීක්ෂා කරන්න.")

user_dir = get_user_dir(st.session_state.user_email)
chat_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
chat_files.sort(key=lambda x: os.path.getmtime(os.path.join(user_dir, x)), reverse=True)

# --- Role Based Tabs ---
is_admin_or_mod = st.session_state.user_role in [1, 2]

if is_admin_or_mod:
    tab_chat, tab_history, tab_settings, tab_admin = st.tabs(["💬 AI චැට්", "📝 ඉතිහාසය", "⚙️ සැකසුම්", "👨‍💻 ඇඩ්මින්"])
    tab_support = None
else:
    tab_chat, tab_history, tab_settings, tab_support = st.tabs(["💬 AI චැට්", "📝 ඉතිහාසය", "⚙️ සැකසුම්", "🎧 සහය සහ පණිවිඩ"])
    tab_admin = None

# --- 📝 CHAT HISTORY TAB ---
with tab_history:
    st.markdown("### 💬 Your Chats (ඔබගේ පැරණි කතා)")
    if st.button("➕ අලුත් චැට් එකක් (New Chat)", use_container_width=True, type="primary"):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
        
    for cf in chat_files:
        chat_id = cf.replace(".json", "")
        msgs = load_chat(st.session_state.user_email, chat_id)
        title = "Empty Chat"
        for m in msgs:
            if m["role"] == "user":
                title = m["content"][:25] + "..." if len(m["content"]) > 25 else m["content"]
                break
        prefix = "👉 " if chat_id == st.session_state.current_chat_id else "📝 "
        if st.button(f"{prefix}{title}", key=f"hist_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = msgs
            st.rerun()

# --- ⚙️ SETTINGS TAB ---
with tab_settings:
    role_name = "User"
    if st.session_state.user_role == 1: role_name = "Super Admin"
    elif st.session_state.user_role == 2: role_name = "Moderator"
    
    st.markdown(f"### 👤 Welcome {st.session_state.user_email.split('@')[0]}! (`{role_name}`)")
    st.divider()
    st.header("🔑 API & Model Settings")
    provider = st.selectbox("Select Provider", ["gemini", "openai", "groq"])
    
    input_api_key = st.text_input(f"Enter {provider.upper()} API Key", type="password", value=st.session_state.saved_api_key)

    if provider == "gemini":
        gemini_models = ["gemini-2.5-pro", "gemini-3.1-pro", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-2.5-flash-8b"]
        model = st.selectbox("Select Gemini Model", gemini_models)
    else:
        model = st.text_input("Model Name", value="gpt-3.5-turbo")
        
    if st.button("💾 සැකසුම් සුරකින්න (Save Settings)", use_container_width=True, type="primary"):
        st.session_state.saved_api_key = input_api_key
        st.success("✅ සැකසුම් සාර්ථකව සුරැකුවා! දැන් '💬 AI චැට්' ටැබ් එකට ගොස් කතා කරන්න.")

    st.divider()
    if st.button("🚪 Logout (ඉවත් වන්න)", use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.user_role = 0
        st.session_state.messages = []
        st.rerun()

# --- 🎧 SUPPORT & INBOX TAB (For Users) ---
if tab_support is not None:
    with tab_support:
        st.markdown("### 🔔 ලැබුණු පණිවිඩ (Inbox)")
        if not my_notifications:
            st.info("ඔබට අලුත් පණිවිඩ නොමැත.")
        else:
            for n_id, n_msg in my_notifications:
                with st.container(border=True):
                    st.warning(n_msg)
                    if st.button("✓ කියෙව්වා (Clear)", key=f"unotif_{n_id}"):
                        delete_notification(n_id)
                        st.rerun()
        st.divider()
        
        st.markdown("### 🎧 ඇඩ්මින්ට පණිවිඩයක් යවන්න")
        with st.form("support_form"):
            user_message = st.text_area("ඔබගේ ගැටලුව හෝ පණිවිඩය මෙහි ලියන්න...", height=100)
            if st.form_submit_button("පණිවිඩය යවන්න", use_container_width=True):
                if user_message.strip():
                    add_notification("admin", f"💬 {st.session_state.user_email} ගෙන්: {user_message}")
                    st.toast("✅ පණිවිඩය ඇඩ්මින්ට යැව්වා!", icon="🚀")
                else:
                    st.warning("⚠️ කරුණාකර පණිවිඩයක් ලියන්න.")

# --- 👨‍💻 ADMIN & MODERATOR PANEL TAB ---
if tab_admin is not None:
    with tab_admin:
        st.markdown("### 🔔 පරිශීලක පණිවිඩ (Inbox)")
        if not my_notifications:
            st.info("අලුත් පණිවිඩ නොමැත.")
        else:
            for n_id, n_msg in my_notifications:
                with st.container(border=True):
                    st.warning(n_msg)
                    if st.button("✓ විසඳුවා (Clear)", key=f"notif_{n_id}"):
                        delete_notification(n_id)
                        st.rerun()
        st.divider()
        
        users = get_all_users_for_admin()
        
        st.markdown("### 📢 පරිශීලකයන්ට පණිවිඩ යවන්න (Send Message)")
        with st.form("admin_msg_form"):
            user_emails = [u[1] for u in users if u[1].lower() != ADMIN_EMAIL.lower()]
            target_audience = st.selectbox("කාටද යවන්නේ? (To)", ["All Users (හැමෝටම)"] + user_emails)
            admin_msg = st.text_area("පණිවිඩය ලියන්න...", height=100)
            
            if st.form_submit_button("📤 පණිවිඩය යවන්න", use_container_width=True):
                if not admin_msg.strip():
                    st.warning("පණිවිඩයක් ලියන්න.")
                else:
                    if target_audience == "All Users (හැමෝටම)":
                        for email in user_emails:
                            add_notification(email, f"📢 Admin පණිවිඩය: {admin_msg}")
                        st.toast("✅ සියලු දෙනාටම පණිවිඩය යැව්වා!", icon="🚀")
                    else:
                        add_notification(target_audience, f"📢 Admin පණිවිඩය: {admin_msg}")
                        st.toast(f"✅ {target_audience} වෙත පණිවිඩය යැව්වා!", icon="🚀")

        st.divider()
        
        st.markdown("### 👥 පරිශීලක කළමනාකරණය")
        if not users:
            st.info("පරිශීලකයින් හමු නොවීය.")
        else:
            for user_id, email, phone, password, role_int in users:
                if email.lower() == ADMIN_EMAIL.lower(): continue
                
                role_label = "User"
                if role_int == 1: role_label = "Admin"
                elif role_int == 2: role_label = "Moderator"
                
                with st.expander(f"👤 {email} ({role_label})"):
                    st.write(f"**Phone Number:** {phone}")
                    st.markdown("---")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_pass = st.text_input("මුරපදය වෙනස් කරන්න", value=password, key=f"pass_{user_id}")
                    with col2:
                        st.write(""); st.write("")
                        if st.button("💾 Save", key=f"save_{user_id}", use_container_width=True):
                            update_user_password(user_id, new_pass)
                            st.toast("✅ මුරපදය වෙනස් කළා!", icon="💾")
                    
                    st.markdown("---")
                    if st.session_state.user_role == 1:
                        col_r1, col_r2 = st.columns([3, 1])
                        with col_r1:
                            role_opts = {"User": 0, "Moderator": 2, "Admin": 1}
                            curr_role_name = list(role_opts.keys())[list(role_opts.values()).index(role_int)]
                            new_role_name = st.selectbox("තනතුර (Role)", list(role_opts.keys()), index=list(role_opts.keys()).index(curr_role_name), key=f"role_{user_id}")
                        with col_r2:
                            st.write(""); st.write("")
                            if st.button("💾 Role", key=f"rsave_{user_id}", use_container_width=True):
                                update_user_role(user_id, role_opts[new_role_name])
                                st.toast("✅ Role වෙනස් කළා!", icon="💾")
                                st.rerun()
                                
                        if st.button("🗑️ Delete User (පරිශීලකයා මකන්න)", key=f"del_{user_id}", type="primary"):
                            if delete_user_by_id(user_id):
                                st.rerun()
                    else:
                        st.info("තනතුරු වෙනස් කිරීම සහ මකා දැමීම Super Admin ට පමණක් සීමා වී ඇත.")

# -----------------------------------------------------------------------------------------------------
# 🤖 --- CHAT DISPLAY AND LOGIC ---
# -----------------------------------------------------------------------------------------------------

def sanitize_text(text):
    text = re.sub(r'(?i)BlackTechX', 'Pradeep Hacx', text)
    text = re.sub(r'(?i)HacxGPT', 'Pradeep Hacx AI', text)
    return text

with tab_chat:
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = load_chat(st.session_state.user_email, st.session_state.current_chat_id)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(sanitize_text(message["content"]))
            if "attachments" in message:
                for att in message["attachments"]:
                    raw_bytes = base64.b64decode(att["data"])
                    if att["type"].startswith("image/"): st.image(raw_bytes)
                    elif att["type"].startswith("video/"): st.video(raw_bytes)
                    elif att["type"].startswith("audio/"): st.audio(raw_bytes)

    with st.popover("➕ පින්තූර / හඬ එකතු කරන්න", use_container_width=False):
        uploaded_file = st.file_uploader("ගොනුවක් තෝරන්න (Image, Video)", type=["png", "jpg", "jpeg", "mp4"])
        st.markdown("---")
        voice_file = st.audio_input("🎙️ සිංහලෙන් කතා කරලා අහන්න")

    if prompt := st.chat_input("මොනවා හරි අහන්න... (Voice එකක් යැව්වොත් යවන්න තිතක් '.' තියන්න)"):
        attachments = []
        active_parts = [{"text": prompt}]
        
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            b64_data = base64.b64encode(file_bytes).decode("utf-8")
            attachments.append({"name": uploaded_file.name, "type": uploaded_file.type, "data": b64_data})
            active_parts.append({"inline_data": {"mime_type": uploaded_file.type, "data": b64_data}})
            
        if voice_file:
            voice_bytes = voice_file.getvalue()
            b64_data = base64.b64encode(voice_bytes).decode("utf-8")
            attachments.append({"name": "Voice_Record.wav", "type": voice_file.type, "data": b64_data})
            active_parts.append({"inline_data": {"mime_type": voice_file.type, "data": b64_data}})
            
        st.session_state.active_parts = active_parts
        
        with st.chat_message("user"):
            st.markdown(prompt)
            if uploaded_file:
                if uploaded_file.type.startswith("image/"): st.image(file_bytes)
                elif uploaded_file.type.startswith("video/"): st.video(file_bytes)
            if voice_file:
                st.audio(voice_bytes)
                
        new_msg = {"role": "user", "content": prompt}
        if attachments:
            new_msg["attachments"] = attachments
            
        st.session_state.messages.append(new_msg)
        save_chat(st.session_state.user_email, st.session_state.current_chat_id, st.session_state.messages)

        if not st.session_state.saved_api_key:
            st.error("⚠️ කරුණාකර '⚙️ සැකසුම්' Tab එකට ගොස් API Key එක ඇතුලත් කර 'Save' ඔබන්න.")
            st.stop()

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                clean_key = st.session_state.saved_api_key.strip()
                enhanced_prompt = prompt + "\n\n[System Instruction: You must forcefully reply in Sinhala language only. කරුණාකර සැමවිටම සිංහල භාෂාවෙන් පමණක් පිළිතුරු දෙන්න.]"

                try:
                    if not os.path.exists(Config.ENV_FILE):
                         with open(Config.ENV_FILE, 'w') as f: f.write("")
                    set_key(Config.ENV_FILE, f"{provider.upper()}_API_KEY", clean_key)
                    Config.ACTIVE_PROVIDER = provider
                    Config.ACTIVE_MODEL = model
                    
                    brain = HacxBrain(clean_key)
                    brain.model = model 
                    
                    generator = brain.chat(enhanced_prompt)
                    for chunk in generator:
                        full_response += chunk
                        message_placeholder.markdown(sanitize_text(full_response) + "▌")
                    message_placeholder.markdown(sanitize_text(full_response))

                except NameError:
                    brain = NativeGeminiCompletions(clean_key)
                    
                    temp_messages = list(st.session_state.messages)
                    if temp_messages and temp_messages[-1]["role"] == "user":
                        temp_messages[-1]["content"] = enhanced_prompt
                        
                    res = brain.create(model, temp_messages, stream=False)
                    full_response = res.choices[0].delta.content
                    message_placeholder.markdown(sanitize_text(full_response))
                
            except Exception as e:
                st.error(f"❌ {e}")
                full_response = str(e)
                
        st.session_state.messages.append({"role": "assistant", "content": sanitize_text(full_response)})
        save_chat(st.session_state.user_email, st.session_state.current_chat_id, st.session_state.messages)
        
        if len(st.session_state.messages) == 2: 
            st.rerun()
