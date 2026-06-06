import streamlit as st
import os
import requests

# --- ස්ථාවර සහ පිරිසිදු කෝඩ් එක ---
st.set_page_config(page_title="HacxGPT Sinhala", page_icon="🤖", layout="centered")

st.title("🤖 HacxGPT - සිංහලෙන්")

with st.sidebar:
    api_key = st.text_input("Enter GEMINI API Key", type="password")
    # 'gemini-1.5-flash' වෙනුවට 'gemini-1.5-flash-latest' ලෙස භාවිතා කරන්න (Google ලා ඒක තමයි දැන් හඳුනාගන්නේ)
    model = st.selectbox("Select Model", ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"])

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
            # Google වෙත කෙලින්ම ඉල්ලීමක් යැවීම
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{"parts": [{"text": f"{prompt}. පිළිතුර සිංහලෙන් ලබා දෙන්න."}]}]
            }
            
            res = requests.post(url, json=payload)
            data = res.json()
            
            if "candidates" in data:
                full_response = data["candidates"][0]["content"]["parts"][0]["text"]
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                st.error(f"දෝෂයක්: {data.get('error', {}).get('message', 'නොදන්නා දෝෂයක්')}")
        except Exception as e:
            st.error(f"සම්බන්ධතා දෝෂය: {e}")
