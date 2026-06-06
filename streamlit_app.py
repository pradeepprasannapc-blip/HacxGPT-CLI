import streamlit as st
import os
import requests

# 1. Google Native Client Setup (Error 401 & 404 මගහරින කොටස)
class NativeGeminiCompletions:
    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, model, messages, stream=False, temperature=0.75):
        contents = []
        # AI එකට සිංහලෙන් උත්තර දෙන්න උපදෙස් දීම
        system_text = "You are a helpful AI assistant. Always respond in Sinhala."
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"] + " (Always answer in Sinhala)"
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        
        payload = {"contents": contents, "system_instruction": {"parts": [{"text": system_text}]}}
        
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={self.api_key}"
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if res.status_code != 200:
            raise Exception(f"Google API Error {res.status_code}: {res.text}")
        
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return type('obj', (object,), {'choices': [type('obj', (object,), {'message': type('obj', (object,), {'content': text})})]})()

class NativeClient:
    def __init__(self, api_key, **kwargs):
        self.chat = type('obj', (object,), {'completions': NativeGeminiCompletions(api_key)})

# --- Streamlit UI Setup ---
st.set_page_config(page_title="HacxGPT Sinhala", page_icon="🤖", layout="centered")

try:
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
    from hacxgpt.utils.security import Security
    import hacxgpt.core.brain as brain_module
    
    Security.encrypt = lambda text: text
    Security.decrypt = lambda text: text
    # HacxBrain එන්ජිමේ අභ්‍යන්තර Client එක අපේ Native Client එකෙන් ප්‍රතිස්ථාපනය කිරීම
    brain_module.Client = NativeClient

except ImportError:
    st.error("ඇප් එකේ ෆයිල්ස් හොයාගන්න බැහැ.")
    st.stop()

st.title("🤖 HacxGPT - සිංහලෙන්")

with st.sidebar:
    api_key = st.text_input("Enter GEMINI API Key", type="password")
    model = st.selectbox("Select Model", ["gemini-1.5-flash", "gemini-pro"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("ඔබේ ප්‍රශ්නය සිංහලෙන් අහන්න..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not api_key:
        st.error("API Key එකක් ඇතුලත් කරන්න.")
        st.stop()

    with st.chat_message("assistant"):
        try:
            # HacxBrain එන්ජිම භාවිතා කරමින් පිළිතුර ලබා ගැනීම
            brain = HacxBrain(api_key.strip())
            brain.model = model
            
            # එන්ජිම හරහා ලැබෙන පිළිතුර
            response_obj = brain.client.chat.completions.create(model=model, messages=brain.history)
            full_response = response_obj.choices[0].message.content
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"❌ දෝෂයක් ඇතිවිය: {e}")
