import streamlit as st
import os
import requests

# --- HacxGPT හි ඇති දෝෂය නිවැරදි කිරීම (Monkey Patching) ---
original_post = requests.post
original_request = requests.Session.request

def fix_gemini_headers(url, kwargs):
    # යවන URL එක Google Gemini එකේ නම් විතරක් මේක වැඩ කරයි
    if "generativelanguage.googleapis.com" in str(url):
        headers = kwargs.get("headers", {})
        auth_header = headers.get("Authorization", headers.get("authorization", ""))
        
        # OpenAI විදිහට තියෙන Bearer Token එක Google විදිහට හරවමු
        if auth_header.startswith("Bearer "):
            key = auth_header.replace("Bearer ", "")
            if "Authorization" in headers: del headers["Authorization"]
            if "authorization" in headers: del headers["authorization"]
            
            # Google ඉල්ලන නිවැරදි Header එක සකස් කිරීම
            headers["x-goog-api-key"] = key
            kwargs["headers"] = headers
            
            # අමතර ආරක්ෂාවට URL එකේ අගටත් Key එක එකතු කිරීම
            if "?key=" not in str(url):
                url = f"{url}?key={key}"
                
    return url, kwargs

def patched_post(url, **kwargs):
    url, kwargs = fix_gemini_headers(url, kwargs)
    return original_post(url, **kwargs)

def patched_request(self, method, url, **kwargs):
    if str(method).upper() == "POST":
        url, kwargs = fix_gemini_headers(url, kwargs)
    return original_request(self, method, url, **kwargs)

# Requests library එක අපේ අලුත් functions වලින් Replace කරනවා (මගදී අල්ලා ගැනීම)
requests.post = patched_post
requests.Session.request = patched_request
# -----------------------------------------------------------

st.set_page_config(page_title="HacxGPT Web", page_icon="🤖", layout="centered")

try:
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
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
            
            os.environ["HACX_ACTIVE_PROVIDER"] = provider
            os.environ["HACX_ACTIVE_MODEL"] = model
            
            Config.get_api_key = lambda *args, **kwargs: clean_key
            
            if hasattr(Config, 'initialize'):
                try: Config.initialize()
                except Exception: pass
            
            # ඔයාට ඕනේ කරපු HacxBrain එන්ජිමම තමයි මේ පාවිච්චි වෙන්නේ
            brain = HacxBrain(clean_key)
            brain.set_provider(provider, clean_key)
            brain.set_model(model)
            
            generator = brain.chat(prompt)
            
            for chunk in generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            full_response = "සමාවෙන්න, දෝෂයක් ඇතිවිය. කරුණාකර නැවත උත්සහ කරන්න."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
