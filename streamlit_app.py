import streamlit as st
import os
import requests

# HacxGPT මුල් එන්ජිම (Brain එක) එහෙම්මම තියාගන්නවා
try:
    from hacxgpt.core.brain import HacxBrain
except ImportError:
    st.error("HacxGPT එන්ජිම සොයාගත නොහැක.")
    st.stop()

st.set_page_config(page_title="HacxGPT Web", page_icon="🤖", layout="centered")
st.title("🤖 HacxGPT - සිංහලෙන්")

with st.sidebar:
    api_key = st.text_input("Enter GEMINI API Key", type="password")
    model = st.text_input("Model Name", value="gemini-1.5-flash")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("ඔබේ ප්‍රශ්නය මෙතන ලියන්න..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not api_key:
        st.error("API Key එකක් ඇතුළත් කරන්න.")
        st.stop()

    with st.chat_message("assistant"):
        try:
            # 🔴 මෙතනදී අපි HacxBrain එකේ තියෙන 'client' එකට අලුත් පාරක් හදනවා
            # අපි කෙලින්ම HacxBrain එකට අණ කරනවා අපේ නිවැරදි URL එක පාවිච්චි කරන්න කියලා
            
            # Google වෙත නිල API ඉල්ලීමක් යැවීමට අපි හදපු පාලම
            def custom_request(api_key, model, prompt):
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": f"{prompt}. පිළිතුර සිංහලෙන් ලබා දෙන්න."}]}]}
                res = requests.post(url, json=payload)
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]

            # එන්ජිම හරහාම ප්‍රතිචාරය ලබා ගැනීම
            full_response = custom_request(api_key.strip(), model, prompt)
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"දෝෂයක්: කරුණාකර මොඩල් නම 'gemini-1.5-flash' ලෙස තහවුරු කරන්න. විස්තරය: {e}")
