import streamlit as st
import os
import requests

# --- 1. සත්‍ය Google Native Client එක (ස්ථාවර අනුවාදය) ---
class NativeGeminiCompletions:
    def __init__(self, api_key):
        self.api_key = api_key

    def create(self, model, messages, stream=False, temperature=0.75):
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        
        # දෝෂ වළක්වා ගැනීමට JSON Payload එක නිවැරදි කිරීම
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature}
        }
        
        # 'v1' අනුවාදය භාවිතා කිරීම (සියලුම නවීන මාදිලි සඳහා ගැලපේ)
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={self.api_key}"
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if res.status_code != 200:
            raise Exception(f"Google API Error {res.status_code}: {res.text}")
        
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return type('obj', (object,), {'choices': [type('obj', (object,), {'message': type('obj', (object,), {'content': text})})]})()

class NativeClient:
    def __init__(self, api_key, **kwargs):
        self.chat = type('obj', (object,), {'completions': NativeGeminiCompletions(api_key)})

# --- 2. Streamlit UI හා එන්ජින් සැකසුම ---
st.set_page_config(page_title="HacxGPT Sinhala", page_icon="🤖", layout="centered")

try:
    from hacxgpt.config import Config
    from hacxgpt.core.brain import HacxBrain
    from hacxgpt.utils.security import Security
    import hacxgpt.core.brain as brain_module
    
    # එන්ජිමේ Encryption අක්‍රිය කිරීම
    Security.encrypt = lambda text: text
    Security.decrypt = lambda text: text
    # Native Client එක සම්බන්ධ කිරීම
    brain_module.Client = NativeClient
except Exception as e:
    st.error("ඇප් එකේ ෆයිල්ස් ගැටලුවක්: " + str(e))
    st.stop()

st.title("🤖 HacxGPT - සිංහලෙන්")

with st.sidebar:
    api_key = st.text_input("Enter GEMINI API Key", type="password")
    model = st.selectbox("Select Model", ["gemini-1.5-flash", "gemini-1.5-pro"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("ඔබේ ප්‍රශ්නය මෙතන ලියන්න..."):
    # සිංහලෙන් උත්තර ලබා ගැනීමට ප්‍රොම්ප්ට් එක සකස් කිරීම
    prompt_with_lang = f"{prompt}. Please answer in Sinhala language."
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not api_key:
        st.error("කරුණාකර API Key එකක් ඇතුළත් කරන්න.")
        st.stop()

    with st.chat_message("assistant"):
        try:
            brain = HacxBrain(api_key.strip())
            brain.model = model
            
            # පද්ධතියට ලැබෙන prompt එක වෙනස් කර සිංහලෙන් උත්තර ලබා ගැනීම
            messages = brain.history
            messages[-1]["content"] = prompt_with_lang
            
            response_obj = brain.client.chat.completions.create(model=model, messages=messages)
            full_response = response_obj.choices[0].message.content
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"දෝෂයක්: {e}")
