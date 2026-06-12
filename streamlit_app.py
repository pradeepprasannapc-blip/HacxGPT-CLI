import streamlit as st
import os
import requests
import json
import uuid
import base64

# --- 🔥 THE ULTIMATE FIX: අලුත් Native Gemini Wrapper එක (එන්ජිමට හානියක් නොවන පරිදි) 🔥 ---
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
        
        # 1. පරණ මැසේජ් හිස්ට්‍රිය සහ අලුත් ප්‍රශ්නය සාමාන්‍ය පරිදි සකස් කිරීම
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        
        # 2. 🔥 MULTIMODAL INTERCEPTION: ෆොටෝ/වොයිස් තියෙනවා නම් එය අන්තිම මැසේජ් එකට රහසේම සම්බන්ධ කිරීම
        if "active_parts" in st.session_state and st.session_state.active_parts:
            for item in reversed(contents):
                if item["role"] == "user":
                    item["parts"] = st.session_state.active_parts
                    break
            # එක පාරක් යැවූ පසු එය Clear කිරීම (පරිවර්තනයට හෝ ඊළඟ ප්‍රශ්නෙට පැටලෙන්නේ නැති වීමට)
            st.session_state.active_parts = None
        
        payload = {"contents": contents}
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if res.status_code != 200:
            raise Exception(f"Google Native API Error {res.status_code}: {res.text}")
        
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return [MockResponse(text)] if stream else MockResponse(text)

class NativeClient:
    def __init__(self, api_key, **kwargs):
        class Chat:
            def __init__(self, key):
                self.completions = NativeGeminiCompletions(key)
        self.chat = Chat(api_key)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="HacxGPT Web", page_icon="🤖", layout="centered", initial_sidebar_state="auto")

# --- 🔥 UI Hiding Fix (Header, Footer, Toolbar) 🔥 ---
st.markdown("""
<style>
/* අනවශ්‍ය සියලුම දේවල් මැකීම */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stAppDeployButton { display: none !important; }
footer { visibility: hidden !important; display: none !important; }

/* ඇප් එකේ ඉඩකඩ ලස්සන කිරීම */
.block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }

/* කෝඩ් කොපි කරන කොටස පැහැදිලි කිරීම */
code { font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; }
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
    # HacxBrain එන්ජිමට අලුත් කන්/ඇස් සවිකිරීම
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
    st.title("🔐 HacxGPT Login")
    st.markdown("කරුණාකර ඔබගේ ගිණුමට ඇතුලත් වන්න. (ඔබගේ චැට් ඉතිහාසය සුරක්ෂිතව තබාගැනීම සඳහා)")
    
    with st.form("login_form"):
        email_input = st.text_input("ඔබගේ Email ලිපිනය (Google Account)")
        submitted = st.form_submit_button("ඇතුලත් වන්න (Login)")
        
        if submitted:
            if email_input:
                st.session_state.logged_in = True
                safe_email = email_input.strip().lower().replace("@", "_at_").replace(".", "_dot_")
                st.session_state.user_email = safe_email
                st.session_state.current_chat_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.rerun()
            else:
                st.error("⚠️ කරුණාකර Email ලිපිනයක් ලබා දෙන්න.")
    st.stop()

# --- MAIN APP UI & SIDEBAR ---
st.title("🤖 HacxGPT - Web Interface")

user_dir = get_user_dir(st.session_state.user_email)
chat_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
chat_files.sort(key=lambda x: os.path.getmtime(os.path.join(user_dir, x)), reverse=True)

with st.sidebar:
    if st.button("➕ New Chat", use_container_width=True):
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
        gemini_models = [
            "gemini-2.5-pro",
            "gemini-3.1-pro",
            "gemini-2.5-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash-8b",
            "gemini-3.5-flash-8b"
        ]
        model = st.selectbox("Select Gemini Model", gemini_models)
    else:
        default_model = "gpt-3.5-turbo" if provider == "openai" else "llama3-8b-8192"
        model = st.text_input("Model Name", value=default_model)
        
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.messages = []
        st.rerun()

# --- CHAT DISPLAY ---
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = load_chat(st.session_state.user_email, st.session_state.current_chat_id)

# පරණ මැසේජ් සහ ඒවායේ තිබූ පින්තූර/හඬ පට නැවත පෙන්වීම
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "attachments" in message:
            for att in message["attachments"]:
                raw_bytes = base64.b64decode(att["data"])
                if att["type"].startswith("image/"): st.image(raw_bytes)
                elif att["type"].startswith("video/"): st.video(raw_bytes)
                elif att["type"].startswith("audio/"): st.audio(raw_bytes)

# --- 🔥 MULTIMODAL INPUTS FEATURE (ෆොටෝ / වොයිස් එකතු කිරීම) 🔥 ---
with st.expander("📎 Attach Media (පින්තූර / වීඩියෝ / හඬ එකතු කරන්න)", expanded=False):
    uploaded_file = st.file_uploader("ගොනුවක් තෝරන්න (Image, Video, Audio)", type=["png", "jpg", "jpeg", "mp4", "mp3", "wav", "m4a"])
    voice_file = st.audio_input("🎙️ හඬක් පටිගත කරන්න (Voice Recorder)")

# --- CHAT LOGIC ---
if prompt := st.chat_input("මොනවා හරි අහන්න..."):
    attachments = []
    active_parts = [{"text": prompt}]
    
    # පින්තූර හෝ වීඩියෝ සැකසීම
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        attachments.append({"name": uploaded_file.name, "type": uploaded_file.type, "data": b64_data})
        active_parts.append({"inline_data": {"mime_type": uploaded_file.type, "data": b64_data}})
        
    # Voice රෙකෝඩින් සැකසීම
    if voice_file:
        voice_bytes = voice_file.getvalue()
        b64_data = base64.b64encode(voice_bytes).decode("utf-8")
        attachments.append({"name": "Voice_Record.wav", "type": voice_file.type, "data": b64_data})
        active_parts.append({"inline_data": {"mime_type": voice_file.type, "data": b64_data}})
        
    # Wrapper එකට කියවීමට සුරැකීම
    st.session_state.active_parts = active_parts
    
    # User Screen එකේ ක්ෂණිකව පෙන්වීම
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type.startswith("image/"): st.image(file_bytes)
            elif uploaded_file.type.startswith("video/"): st.video(file_bytes)
            elif uploaded_file.type.startswith("audio/"): st.audio(file_bytes)
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
            
            # මුල් මොළයට හානියක් නැත, එය ක්‍රියාත්මක වන්නේ අකුරු වලින්මය
            generator = brain.chat(prompt)
            
            for chunk in generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            
            # --- සිංහල පරිවර්තනය ---
            try:
                trans_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={clean_key}"
                trans_payload = {"contents": [{"parts": [{"text": f"Translate this text to Sinhala: {full_response}"}]}]}
                trans_res = requests.post(trans_url, json=trans_payload).json()
                final_response = trans_res["candidates"][0]["content"]["parts"][0]["text"]
                
                # කොපි බට්න් එකත් එක්කම අවසන් උත්තරය පෙන්වීම
                message_placeholder.markdown(final_response)
                full_response = final_response
            except:
                message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            full_response = "සමාවෙන්න, දෝෂයක් ඇතිවිය."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_chat(st.session_state.user_email, st.session_state.current_chat_id, st.session_state.messages)
    
    if len(st.session_state.messages) == 2: 
        st.rerun()
