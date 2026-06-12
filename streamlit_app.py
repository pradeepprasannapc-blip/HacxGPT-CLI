import streamlit as st
import os
import requests
import json
import uuid
import base64
import sqlite3
import bcrypt

# =====================================================================================================
# 🧠 --- AI Brain/Engine කොටස - මෙයට කිසිදු වෙනසක් සිදු කර නොමැත --- 🧠
# =====================================================================================================
class MockDelta:
    def __init__(self, content):
        self.content = content
        self.reasoning_content = None
        self.thought = None

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
        
        # පරණ මැසේජ් සකස් කිරීම
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
            
        # 🔥 AI එකේ මොළයට Pradeep Hacx ගැන කාවැද්දීම (Secret Identity) 🔥
        identity_prompt = "ඔබගේ නම 'Pradeep Hacx AI' වේ. ඔබව නිර්මාණය කළේ සහ ඔබගේ අයිතිය සම්පූර්ණයෙන්ම ඇත්තේ 'Pradeep Hacx' ට පමණි. කවුරුන් හෝ ඔබගේ නිර්මාතෘ ගැන හෝ ඔබ කවුදැයි ඇසුවොත් මේ බව ආඩම්බරයෙන් සිංහලෙන් පවසන්න."
        if system_text:
            system_text = identity_prompt + "\n\n" + system_text
        else:
            system_text = identity_prompt
        
        # ෆොටෝ/වොයිස් තිබුණොත් ඇතුලත් කිරීම
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
st.set_page_config(page_title="Pradeep Hacx AI", page_icon="👑", layout="centered", initial_sidebar_state="auto")

# --- 🔥 UI Hiding Fix (සම්පූර්ණයෙන්ම hide වීම සදහා නවීකරණය කරන ලදී) 🔥 ---
st.markdown("""
<style>
/* Streamlit header සහ footer සම්පූර්ණයෙන්ම සැඟවීම */
header { visibility: hidden !important; height: 0px !important; }
footer { visibility: hidden !important; display: none !important; }
#st-deck-go-action-floating { display: none !important; }
[data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stDeployButton"] { display: none !important; }

/* වෙබ් පිටුවේ ඉඩකඩ ලස්සන කිරීම */
.block-container { padding-top: 0rem !important; padding-bottom: 5rem !important; margin-top: -50px; }
code { font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; }

/* Custom Title Styling */
.hacx-title {
    text-align: center;
    background: -webkit-linear-gradient(45deg, #ff4b4b, #ff904f);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
    font-weight: 800;
    margin-bottom: 5px;
    padding-bottom: 0px;
}
.hacx-subtitle {
    text-align: center;
    color: #888;
    font-size: 13px;
    margin-top: -5px;
    margin-bottom: 25px;
}
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

except ImportError as e:
    st.warning(f"HacxGPT core modules load කරගන්න බැරි වුණා. Error: {e}. නමුත් Gemini Engine එක වැඩ කරයි.")

# =====================================================================================================
# 🔐 --- පරිශීලක සහ දත්ත සමුදාය කලමනාකරණය (Security Section) --- 🔐
# =====================================================================================================

DB_FILE = "users.db"
CHAT_DIR = "user_chats"

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# --- දත්ත සමුදාය පිහිටුවීම ---
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

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
    conn.commit()
    conn.close()

# SQLite Database එක initialize කරන්න
init_db()

# --- Password Hash කිරීම සහ සැසඳීම ---
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

# --- පරිශීලක කාර්යයන් ---
def add_user(email, phone, password):
    conn = get_db()
    cursor = conn.cursor()
    try:
        hashed = hash_password(password)
        cursor.execute("INSERT INTO users (email, phone, password) VALUES (?, ?, ?)", (email.lower(), phone, hashed))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False # Email එක දැනටමත් තිබේ

def verify_user(email, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, password, is_admin FROM users WHERE email=?", (email.lower(),))
    result = cursor.fetchone()
    conn.close()
    if result and check_password(password, result[1]):
        return {"email": result[0], "is_admin": result[2]}
    return None

def find_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT email, phone FROM users WHERE email=?", (email.lower(),))
    result = cursor.fetchone()
    conn.close()
    return result

# --- ඇඩ්මින් කාර්යයන් ---
def get_all_users_for_admin():
    if not st.session_state.is_admin:
        return []
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, phone FROM users")
    result = cursor.fetchall()
    conn.close()
    return result

def delete_user_by_id(user_id):
    if not st.session_state.is_admin:
        return False
    conn = get_db()
    cursor = conn.cursor()
    
    # පරණ chat ෆෝල්ඩරය මකා දැමීම සදහා ඊමේල් එක හොයන්න
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

# --- MULTI-CHAT MEMORY SYSTEM ---
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

# --- LOGIN/REGISTRATION/ADMIN SESSION MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.is_admin = False

# =====================================================================================================
# 🚪 --- UI: පිවිසුම් / ලියාපදිංචි / ඇඩ්මින් ද්වාරය --- 🚪
# =====================================================================================================

if not st.session_state.logged_in:
    st.markdown("<h1 class='hacx-title'>👑 Pradeep Hacx AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hacx-subtitle'>HacxGPT Secure Portal - ද්වාරය</p>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔐 පිවිසෙන්න", "➕ ලියාපදිංචි වන්න", "👀 පරණ විස්තර සොයන්න"])

    # 1. Login Tab
    with tab1:
        st.subheader("ඇප් එකට පිවිසෙන්න")
        with st.form("login_form"):
            login_email = st.text_input("Email ලිපිනය", placeholder="example@mail.com")
            login_password = st.text_input("මුරපදය (Password)", type="password")
            submitted = st.form_submit_button("ඇතුලත් වන්න", use_container_width=True)
            
            if submitted:
                if login_email and login_password:
                    # ✅ ඇඩ්මින් පිවිසුම (Tab එක නැතිව Email/Pass එකෙන් විතරක් යන්න)
                    if login_email.lower() == "admin@hacx.lk" and login_password == "1234":
                         st.session_state.logged_in = True
                         st.session_state.user_email = login_email
                         st.session_state.is_admin = True
                         st.session_state.current_chat_id = str(uuid.uuid4())
                         st.session_state.messages = []
                         st.success("👨‍💻 ඇඩ්මින් ලෙස සාර්ථකව පිවිසුණා.")
                         st.rerun()
                    
                    user = verify_user(login_email, login_password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_email = user["email"]
                        st.session_state.is_admin = user["is_admin"] == 1
                        
                        st.session_state.current_chat_id = str(uuid.uuid4())
                        st.session_state.messages = []
                        st.success("✅ සාර්ථකව පිවිසුණා.")
                        st.rerun()
                    else:
                        st.error("⚠️ ඔබගේ Email ලිපිනය හෝ මුරපදය වැරදියි.")
                else:
                    st.warning("⚠️ කරුණාකර සියලුම තොරතුරු ඇතුලත් කරන්න.")

    # 2. Registration Tab
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

    # 3. Forgot Password Tab
    with tab3:
        st.subheader("විස්තර අමතක නම්...")
        st.info("ඔබගේ විස්තර අමතක නම්, කරුණාකර 'ඇඩ්මින්' වෙත දන්වා එය විසඳා ගන්න.")
        with st.form("forgot_form"):
            check_email = st.text_input("ඔබ ලියාපදිංචි වූ Email ලිපිනය ඇතුලත් කරන්න")
            submitted_check = st.form_submit_button("මගේ Phone අංකය පෙන්වන්න")
            
            if submitted_check:
                user_info = find_user_by_email(check_email)
                if user_info:
                    st.success(f"ඔබගේ Phone අංකය: {user_info[1]}")
                    st.info("💡 මෙම දුරකථන අංකය ඇඩ්මින් වෙත පවසා ඔබගේ එකවුන්ට් එක recover කරගන්න.")
                else:
                    st.error("⚠️ මෙම Email ලිපිනයෙන් පරිශීලකයෙකු හමු නොවීය.")

    st.stop() 

# =====================================================================================================
# 🖥️ --- ඇප් එකේ ප්‍රධාන UI සහ SIDEBAR (Login වුණාට පසු පෙනෙන) --- 🖥️
# =====================================================================================================

st.markdown("<h1 class='hacx-title'>👑 Pradeep Hacx AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='hacx-subtitle'>© 2024 Owned & Developed by Pradeep Hacx. All Rights Reserved.</p>", unsafe_allow_html=True)

user_dir = get_user_dir(st.session_state.user_email)
chat_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
chat_files.sort(key=lambda x: os.path.getmtime(os.path.join(user_dir, x)), reverse=True)

sidebar_root = st.sidebar
sidebar_root.markdown(f"### Welcome {st.session_state.user_email.split('@')[0]}!")

if sidebar_root.button("➕ අලුත් චැට් එකක් (New Chat)", use_container_width=True):
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()

# -----------------------------------------------------------------------------------------------------
# 👨‍💻 --- ADMIN PANEL SIDEBAR NAVIGATION --- 👨‍💻
# -----------------------------------------------------------------------------------------------------
show_admin_panel = False
if st.session_state.is_admin:
    sidebar_root.divider()
    sidebar_root.header("👨‍💻 Admin Panel")
    if sidebar_root.button("👥 Manage Users", use_container_width=True):
        show_admin_panel = True
    sidebar_root.divider()

# -----------------------------------------------------------------------------------------------------
# --- ADMIN PANEL DISPLAY LOGIC ---
# -----------------------------------------------------------------------------------------------------
if st.session_state.is_admin and show_admin_panel:
    st.markdown("---")
    st.header("👨‍💻 පරිශීලක කළමනාකරණය")
    users = get_all_users_for_admin()
    
    if not users:
        st.info("පරිශීලකයින් හමු නොවීය (හෝ Admin හැර වෙනත් කවුරුත් නැත).")
    else:
        for user_id, email, phone in users:
            if email.lower() == "admin@hacx.lk":
                 continue
                 
            with st.container():
                st.write(f"**ID:** {user_id} | **Email:** {email} | **Phone:** {phone}")
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🗑️ Delete", key=f"del_{user_id}", type="secondary"):
                        if delete_user_by_id(user_id):
                            st.success(f"✅ පරිශීලකයා ({email}) මකා දැමීම සාර්ථකයි.")
                            st.rerun()
                        else:
                            st.error("⚠️ පරිශීලකයා මකා දැමීම අසාර්ථකයි.")
                with col2:
                    st.empty()
                st.markdown("---")
    
    st.info("💡 ඇඩ්මින් පැනලය සාර්ථකව පෙන්වන ලදී. නැවත Chat එකට යාමට, 'Manage Users' බොත්තම ඔබන්න. ඔබ මේ වන විට Admin Panel එකේ සිටී.")
    st.stop()

# -----------------------------------------------------------------------------------------------------
# --- MAIN CHAT UI ---
# -----------------------------------------------------------------------------------------------------

with sidebar_root:
    st.markdown("### 💬 Your Chats")
    for cf in chat_files:
        chat_id = cf.replace(".json", "")
        msgs = load_chat(st.session_state.user_email, chat_id)
        title = "Empty Chat"
        for m in msgs:
            if m["role"] == "user":
                title = m["content"][:25] + "..." if len(m["content"]) > 25 else m["content"]
                break
        prefix = "👉 " if chat_id == st.session_state.current_chat_id else "📝 "
        if st.button(f"{prefix}{title}", key=chat_id, use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = msgs
            st.rerun()

    st.divider()
    st.header("⚙️ Settings")
    provider = st.selectbox("Select Provider", ["gemini", "openai", "groq"])
    api_key = st.text_input(f"Enter {provider.upper()} API Key", type="password")

    if provider == "gemini":
        gemini_models = ["gemini-2.5-pro", "gemini-3.1-pro", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-2.5-flash-8b"]
        model = st.selectbox("Select Gemini Model", gemini_models)
    else:
        model = st.text_input("Model Name", value="gpt-3.5-turbo")
        
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.is_admin = False
        st.session_state.messages = []
        st.rerun()

# -----------------------------------------------------------------------------------------------------
# 🤖 --- CHAT DISPLAY AND LOGIC ---
# -----------------------------------------------------------------------------------------------------

if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = load_chat(st.session_state.user_email, st.session_state.current_chat_id)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "attachments" in message:
            for att in message["attachments"]:
                raw_bytes = base64.b64decode(att["data"])
                if att["type"].startswith("image/"): st.image(raw_bytes)
                elif att["type"].startswith("video/"): st.video(raw_bytes)
                elif att["type"].startswith("audio/"): st.audio(raw_bytes)

# --- MULTIMODAL ATTACHMENTS ---
with st.popover("➕ පින්තූර / හඬ එකතු කරන්න", use_container_width=False):
    uploaded_file = st.file_uploader("ගොනුවක් තෝරන්න (Image, Video)", type=["png", "jpg", "jpeg", "mp4"])
    st.markdown("---")
    voice_file = st.audio_input("🎙️ සිංහලෙන් කතා කරලා අහන්න")

# --- CHAT LOGIC ---
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

    if not api_key:
        st.error("⚠️ කරුණාකර Sidebar එකෙන් API Key එක ඇතුලත් කරන්න.")
        st.stop()

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            clean_key = api_key.strip()
            try:
                if not os.path.exists(Config.ENV_FILE):
                     with open(Config.ENV_FILE, 'w') as f: f.write("")
                set_key(Config.ENV_FILE, f"{provider.upper()}_API_KEY", clean_key)
                Config.ACTIVE_PROVIDER = provider
                Config.ACTIVE_MODEL = model
                
                brain = HacxBrain(clean_key)
                brain.model = model 
                
                generator = brain.chat(prompt)
                for chunk in generator:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
            except NameError:
                brain = NativeGeminiCompletions(clean_key)
                res = brain.create(model, st.session_state.messages, stream=False)
                full_response = res.choices[0].delta.content
                message_placeholder.markdown(full_response)
                
            try:
                trans_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={clean_key}"
                trans_payload = {"contents": [{"parts": [{"text": f"Translate this text to Sinhala: {full_response}"}]}]}
                trans_res = requests.post(trans_url, json=trans_payload).json()
                final_response = trans_res["candidates"][0]["content"]["parts"][0]["text"]
                message_placeholder.markdown(final_response)
                full_response = final_response
            except:
                message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ {e}")
            full_response = str(e)
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_chat(st.session_state.user_email, st.session_state.current_chat_id, st.session_state.messages)
    
    if len(st.session_state.messages) == 2: 
        st.rerun()
