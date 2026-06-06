import streamlit as st
import os

st.set_page_config(page_title="HacxGPT Web", page_icon="🤖", layout="centered")

try:
    # CLI එකේ තියෙන ඔක්කොම Security සහ Config ෆයිල්ස් මෙතනට ගන්නවා
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
    from hacxgpt.utils.security import Security
    from dotenv import set_key
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
            
            # 🔴 මෙන්න මේ කොටස තමයි කලින් අඩු වෙලා තිබුණේ
            # ටර්මිනල් එකේ වගේම .env ෆයිල් එකක් හදලා ඒකට Encrypt කරලා Key එක දානවා
            if not os.path.exists(Config.ENV_FILE):
                 with open(Config.ENV_FILE, 'w') as f: f.write("")
                 
            encrypted_key = Security.encrypt(clean_key)
            key_var = f"{provider.upper()}_API_KEY"
            
            set_key(Config.ENV_FILE, key_var, encrypted_key)
            set_key(Config.ENV_FILE, "HACX_ACTIVE_PROVIDER", provider)
            set_key(Config.ENV_FILE, "HACX_ACTIVE_MODEL", model)
            
            # Config එක Initialize කරාම ඒකෙන් ස්වයංක්‍රීයව Key එක Decrypt කරගන්නවා
            Config.ACTIVE_PROVIDER = provider
            Config.ACTIVE_MODEL = model
            Config.initialize()
            
            # App එකට අවශ්‍ය විදිහටම config එකෙන් නිවැරදි key එක ගන්නවා
            app_key = Config.get_api_key()
            if not app_key:
                app_key = clean_key
            
            brain = HacxBrain(app_key)
            brain.set_provider(provider, app_key)
            brain.set_model(model)
            
            generator = brain.chat(prompt)
            
            for chunk in generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            full_response = "සමාවෙන්න, දෝෂයක් ඇතිවිය."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
