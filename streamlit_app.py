import streamlit as st
import os

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
    
    # 🔴 මෙතන මම අලුත් Gemini Model එක default විදිහට දැම්මා
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
            # .strip() මගින් Key එකේ මුල/අග තියෙන හිස්තැන් ස්වයංක්‍රීයව මකා දමයි
            clean_key = api_key.strip()
            
            os.environ["HACX_ACTIVE_PROVIDER"] = provider
            os.environ["HACX_ACTIVE_MODEL"] = model
            os.environ[f"{provider.upper()}_API_KEY"] = clean_key
            
            if provider == "gemini":
                os.environ["GOOGLE_API_KEY"] = clean_key
                # 🔴 HacxGPT මගහැර කෙලින්ම Google Library එකට Key එක දීම
                import google.generativeai as genai
                genai.configure(api_key=clean_key)
            
            Config.ACTIVE_PROVIDER = provider
            Config.ACTIVE_MODEL = model
            
            if hasattr(Config, 'initialize'):
                try: Config.initialize()
                except Exception: pass
            
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
            full_response = "සමාවෙන්න, දෝෂයක් ඇතිවිය."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
