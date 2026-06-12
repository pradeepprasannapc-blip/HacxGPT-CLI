import streamlit as st
import os
import requests
import json
import uuid
import base64

# --- 🔥 THE ULTIMATE FIX: අලුත් Native Gemini Wrapper එක 🔥 ---
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

# --- 🔥 UI Hiding Fix (Menu එක තියලා Manage App සම්පූර්ණයෙන්ම මැකීම) 🔥 ---
st.markdown("""
<style>
/* Menu button (Hamburger) එක විතරක් ඉතුරු කරලා අනිත් දේවල් හංගමු */
header { background: transparent !important; }
.stAppDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* යටින් එන Manage App සහ Streamlit දේවල් සම්පූර්ණයෙන්ම මැකීම */
footer { visibility: hidden !important; display: none !important; }
.viewerBadge_container__1QSob { display: none !important; }
#st-deck-go-action-floating { display: none !important; }
[data-testid="stBottomBar"] { display: none !important; } /* සමහර වෙලාවට එන අලුත් බාර් එක */

/* ඇප් එකේ ඉඩකඩ ලස්සන කිරීම */
.block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
code { font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; }

/* Custom Title Styling */
.hacx-title {
    text-align: center;
    background: -webkit-linear-gradient(45deg, #ff4b4b, #ff904f);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
    font-weight: 800;
    margin-bottom: 0px;
    padding-bottom: 0px;
}
.hacx-subtitle {
    text-align: center;
    color: #888;
    font-size: 12px;
    margin-top: -5px;
    margin-bottom: 20px;
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
    st.error(f"ඇප් එකේ ෆයිල්ස් හොයාගන්න බැහැ. Error: {e}")
    st.stop()

# --- MULTI-CHAT MEMORY SYSTEM ---
CHAT_DIR = "user_chats"
if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

def get_user_dir(email):
    user_dir = os.path.join(CHAT_DIR, email)
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

# --- LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    st.markdown("<h1 class='hacx-title'>👑 Pradeep Hacx AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hacx-subtitle'>Secure Login Portal</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        email_input = st.text_input("ඔබගේ Email ලිපිනය (Google Account)")
        submitted = st.form_submit_button("ඇතුලත් වන්න (Login)")
        if submitted and email_input:
            st.session_state.logged_in = True
            safe_email = email_input.strip().lower().replace("@", "_at_").replace(".", "_dot_")
            st.session_state.user_email = safe_email
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
    st.stop()

# --- MAIN APP UI & SIDEBAR ---
# 🔥 අලුත් ලස්සන Title එක සහ Copyright කොටස 🔥
st.markdown("<h1 class='hacx-title'>👑 Pradeep Hacx AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='hacx-subtitle'>© 2024 Owned & Developed by Pradeep Hacx. All Rights Reserved.</p>", unsafe_allow_html=True)

user_dir = get_user_dir(st.session_state.user_email)
chat_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
chat_files.sort(key=lambda x: os.path.getmtime(os.path.join(user_dir, x)), reverse=True)

with st.sidebar:
    st.markdown("### 👑 Pradeep Hacx AI")
    if st.button("➕ අලුත් චැට් එකක් (New Chat)", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
        
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
        st.session_state.messages = []
        st.rerun()

# --- CHAT DISPLAY ---
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
