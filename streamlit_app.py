import streamlit as st
import requests

st.set_page_config(page_title="HacxGPT Sinhala", page_icon="🤖", layout="centered")
st.title("🤖 HacxGPT - සිංහලෙන්")

with st.sidebar:
    api_key = st.text_input("Enter GEMINI API Key", type="password")
    model = st.text_input("Model Name", value="gemini-1.5-flash")

if prompt := st.chat_input("ඔබේ ප්‍රශ්නය මෙතන ලියන්න..."):
    st.chat_message("user").markdown(prompt)
    if not api_key:
        st.error("API Key එකක් ඇතුළත් කරන්න.")
        st.stop()

    with st.chat_message("assistant"):
        try:
            # 🔴 වැදගත්: මොඩල් එකේ නමෙන් 'models/' කියන කොටසක් තියෙනවා නම් ඒක අයින් කරනවා
            clean_model = model.replace("models/", "")
            
            # API ඉල්ලීම යැවීම
            url = f"https://generativelanguage.googleapis.com/v1/models/{clean_model}:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"{prompt}. පිළිතුර සිංහලෙන් ලබා දෙන්න."}]}]}
            
            res = requests.post(url, json=payload)
            data = res.json()
            
            if "candidates" in data:
                full_response = data["candidates"][0]["content"]["parts"][0]["text"]
                st.markdown(full_response)
            else:
                st.error(f"දෝෂයක්: {data.get('error', {}).get('message', 'නොදන්නා දෝෂයක්')}")
        except Exception as e:
            st.error(f"සම්බන්ධතා දෝෂය: {e}")
