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
st.markdown("HacxGPT CLI හි Web සංස්කරණය.")

with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("ඔයාගේ API Key එක මෙතනට දෙන්න.")
    
    provider = st.selectbox("Select Provider", ["openai", "gemini", "groq"])
    api_key = st.text_input(f"Enter {provider.upper()} API Key", type="password")
    model = st.text_input("Model Name", value="gemini-pro" if provider=="gemini" else "gpt-3.5-turbo")

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
            Config.ACTIVE_PROVIDER = provider
            Config.ACTIVE_MODEL = model
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
            
            brain = HacxBrain(api_key)
            brain.set_provider(provider, api_key)
            brain.set_model(model)
            
            generator = brain.chat(prompt)
            
            for chunk in generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"❌ දෝෂයක් ඇතිවිය: {e}")
            full_response = "Error occurred."
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})
