import streamlit as st
import os
import requests

# --- 1. සත්‍ය Google Native Client එක (ආරක්ෂිත සහ නිවැරදි) ---
class NativeGeminiCompletions:
    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, model, messages, stream=False, temperature=0.75):
        # සියලුම මැසේජ් එක පෙළකට ගොනු කිරීම
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        
        # පද්ධති උපදෙස: හැමවිටම සිංහලෙන් ප්‍රතිචාර දක්වන්න
        payload = {
            "contents": contents,
            "system_instruction": {"parts": [{"text": "You are a helpful assistant. Always respond in Sinhala language."}]}
        }
        
        # නිවැරදි API එන්ඩ්පොයින්ට් එක
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if res.status_code != 200:
            raise Exception(f"Google API Error {res.status_code}: {res.text}")
        
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return type('obj', (object,), {'choices': [type('obj', (object,), {'message': type('obj', (object,), {'content': text})})]})()

class NativeClient:
    def __init__(self, api_key, **kwargs):
        self.chat = type('obj', (object,), {'completions': NativeGeminiCompletions(api_key)})

# --- 2. Streamlit UI හා එන්ජින් පාලනය ---
st.set_page_config(page_title="HacxGPT Sinhala", page_icon="🤖", layout="centered")

try:
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
    from hacxgpt.utils.security import Security
    import hacxgpt.core.brain as brain_module
    
    # එන්ජිමේ Encryption අක්‍රිය කර අපේ Native Client එක රිංගවීම
    Security.encrypt = lambda text: text
    Security.decrypt = lambda text: text
    brain_module.Client = NativeClient
except Exception as e:
    st.error("ඇප් එකේ ෆයිල්ස් ගැටලුවක්: " + str(e))
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

if prompt := st.chat_input("ඔබේ ප්‍රශ්නය මෙතන ලියන්න..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not api_key:
        st.error("කරුණාකර API Key එකක් ඇතුළත් කරන්න.")
        st.stop()

    with st.chat_message("assistant"):
        try:
            # එන්ජිම පණ ගැන්වීම
            brain = HacxBrain(api_key.strip())
            brain.model = model
            
            # පිළිතුර ලබා ගැනීම
            response_obj = brain.client.chat.completions.create(model=model, messages=brain.history)
            full_response = response_obj.choices[0].message.content
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"දෝෂයක්: {e}")
