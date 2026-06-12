import streamlit as st
import os
import requests

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
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        
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
st.set_page_config(page_title="HacxGPT Web", page_icon="🤖", layout="centered")

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

st.title("🤖 HacxGPT - Web Interface")

with st.sidebar: # 'With' වෙනුවට 'with' ලෙස නිවැරදි කර ඇත
    st.header("⚙️ Settings")
    provider = st.selectbox("Select Provider", ["gemini", "openai", "groq"])
    api_key = st.text_input(f"Enter {provider.upper()} API Key", type="password")

    # Provider අනුව model එක තෝරන විදිහ වෙනස් කිරීම
    if provider == "gemini":
        gemini_models = [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.0-pro"
        ]
        model = st.selectbox("Select Gemini Model", gemini_models)
    else:
        # OpenAI සහ Groq සඳහා text input එක
        default_model = "gpt-3.5-turbo" if provider == "openai" else "llama3-8b-8192"
        model = st.text_input("Model Name", value=default_model)

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
            
            set_key(Config.ENV_FILE, f"{provider.upper()}_API_KEY", clean_key)
            Config.ACTIVE_PROVIDER = provider
            Config.ACTIVE_MODEL = model
            
            brain = HacxBrain(clean_key)
            brain.model = model 
            
            generator = brain.chat(prompt)
            
            for chunk in generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            
            # --- මෙතනින් තමයි සිංහලට පරිවර්තනය වෙන්නේ ---
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
            st.error(f"❌ Error: {e}")
            full_response = "සමාවෙන්න, දෝෂයක් ඇතිවිය."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
