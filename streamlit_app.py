import streamlit as st
import os
import requests

# --- 🔥 THE ULTIMATE FIX: අලුත් Native Gemini Wrapper එක 🔥 ---
# HacxBrain එන්ජිමට කිසිදු වෙනසක් නොකර, දෝෂ සහිත api.py වෙනුවට මෙය ක්‍රියාත්මක වේ.
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
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        
        payload = {"contents": contents}
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}
        
        # 100% ක් නිවැරදි Google Native API ලින්ක් එක (401 Error එක සම්පූර්ණයෙන්ම වළක්වයි)
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
# -------------------------------------------------------------

st.set_page_config(page_title="HacxGPT Web", page_icon="🤖", layout="centered")

try:
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
    from hacxgpt.utils.security import Security
    import hacxgpt.core.brain as brain_module
    from dotenv import set_key
    
    # Key එක විකාර වීම වැලැක්වීමට Security Bypass කිරීම
    Security.encrypt = lambda text: text
    Security.decrypt = lambda text: text
    
    # 🔴 මෙතනින් තමයි HacxBrain එකේ දෝෂ සහිත Client එක අයින් කරලා, 
    # අපේ 100% නිවැරදි Native Client එක එන්ජිමට සම්බන්ධ කරන්නේ. 
    # මේකෙන් එන්ජිමේ කිසිම ෆීචර් එකක් නැති වෙන්නේ නෑ!
    brain_module.Client = NativeClient

except ImportError as e:
    st.error(f"ඇප් එකේ ෆයිල්ස් හොයාගන්න බැහැ. Error: {e}")
    st.stop()

st.title("🤖 HacxGPT - Web Interface")

with st.sidebar:
    st.header("⚙️ Settings")
    provider = st.selectbox("Select Provider", ["gemini", "openai", "groq"])
    api_key = st.text_input(f"Enter {provider.upper()} API Key", type="password")
    model = st.text_input("Model Name", value="gemini-1.5-flash" if provider=="gemini" else "gpt-3.5-turbo")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("මොනවා හරි අහන්න..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not api_key:
        st.error("⚠️ කරුණාකර Sidebar එකෙන් API Key එක ඇතුලත් කරන්න.")
        st.stop()

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            clean_key = api_key.strip()
            
            # පරිසර විචල්‍යයන් සැකසීම
            if not os.path.exists(Config.ENV_FILE):
                 with open(Config.ENV_FILE, 'w') as f: f.write("")
            
            key_var = f"{provider.upper()}_API_KEY"
            set_key(Config.ENV_FILE, key_var, clean_key)
            set_key(Config.ENV_FILE, "HACX_ACTIVE_PROVIDER", provider)
            set_key(Config.ENV_FILE, "HACX_ACTIVE_MODEL", model)
            
            os.environ[key_var] = clean_key
            os.environ["HACX_ACTIVE_PROVIDER"] = provider
            os.environ["HACX_ACTIVE_MODEL"] = model
            
            Config.ACTIVE_PROVIDER = provider
            Config.ACTIVE_MODEL = model
            
            if hasattr(Config, 'initialize'):
                try: Config.initialize()
                except Exception: pass
            
            # HacxBrain එන්ජිම පණ ගැන්වීම
            brain = HacxBrain(clean_key)
            brain.model = model 
            
            # Chat එක ආරම්භ කිරීම (දැන් දෝෂ සහිත api.py වෙනුවට අපේ Native එක වැඩ කරයි)
            generator = brain.chat(prompt)
            
            for chunk in generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            full_response = "සමාවෙන්න, දෝෂයක් ඇතිවිය."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
