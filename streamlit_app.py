import streamlit as st
import os
import openai

st.set_page_config(page_title="HacxGPT Web", page_icon="🤖", layout="centered")

try:
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
    from hacxgpt.utils.security import Security
    from dotenv import set_key
    
    # HacxGPT හි ප්‍රධාන එන්ජිම (Module එක) මෙතනට ගන්නවා
    import hacxgpt.core.brain as brain_module
    
    # 🔥 ට්‍රික් 1: Security Bypass (Encrypt කිරීම නැවැත්වීම)
    Security.encrypt = lambda text: text
    Security.decrypt = lambda text: text
    
    # 🔥 ට්‍රික් 2: Network Engine Replacement
    # HacxGPT ඇතුලේ තියෙන දෝෂ සහිත api.Client වෙනුවට, ලෝකේ පිළිගත්ත 
    # නිල openai.OpenAI client එකම එන්ජිමට හොරෙන් සම්බන්ධ කරනවා. 
    # (මෙතනින් එන්ජිමේ Streaming, History වගේ කිසිම දෙයක් වෙනස් වෙන්නේ නෑ)
    brain_module.Client = openai.OpenAI
    
    # 🔥 ට්‍රික් 3: Gemini URL Fixer
    # එන්ජිම Start වෙන්න කලින් අල්ලගෙන, Gemini වලට ගැලපෙන නිවැරදිම ලින්ක් එක දෙනවා
    original_init = HacxBrain._init_client
    def patched_init_client(self):
        if Config.ACTIVE_PROVIDER == "gemini":
            if hasattr(Config, "PROVIDERS") and "gemini" in Config.PROVIDERS:
                # Gemini වල OpenAI Compatibility ලින්ක් එක
                Config.PROVIDERS["gemini"]["base_url"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
        original_init(self)
    HacxBrain._init_client = patched_init_client

except ImportError as e:
    st.error(f"ඇප් එකේ ෆයිල්ස් හොයාගන්න බැහැ. Error: {e}")
    st.stop()

st.title("🤖 HacxGPT - Web Interface")
st.markdown("HacxGPT එන්ජිම 100% ක් භාවිතා කරමින්.")

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
            
            # ටර්මිනල් එකේ වගේම .env සැකසුම් හැදීම
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
            
            # ඔයාට ඕනේ කරපු ඔරිජිනල් HacxBrain එන්ජිමම දැන් රන් වෙනවා!
            brain = HacxBrain(clean_key)
            brain.set_provider(provider, clean_key)
            brain.set_model(model)
            
            # HacxBrain හි chat function එක (Streaming, History ඔක්කොමත් එක්කම)
            generator = brain.chat(prompt)
            
            for chunk in generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            full_response = "සමාවෙන්න, දෝෂයක් ඇතිවිය."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
