import re
import random
import requests
import streamlit as st

def get_boss_prompt():
    return """ඔබගේ නම 'Pradeep Hacx AI' වේ. ඔබව නිර්මාණය කළේ 'Pradeep Hacx' නොහොත් 'W.K. Pradeep Prasanna' නමැති ශ්‍රී ලාංකික මෘදුකාංග ඉංජිනේරුවරයා විසිනි. කතා කරන පරිශීලකයා ඔබගේ නිර්මාතෘ (Boss) වේ. ඔහුට උපරිම ගෞරවයෙන් සහ මිත්‍රශීලීව සිංහලෙන් කතා කරන්න. 
IMPORTANT: You are an AI assistant that MUST strictly reply in the Sinhala language (සිංහල). Never reply in English.

NEW RULE FOR IMAGE GENERATION & EDITING:
If the user (your boss) asks to create a photo, OR if they upload a photo and ask to edit it:
1. Reply naturally in Sinhala, acknowledging his request.
2. At the very end of your response, include an English prompt enclosed in [IMAGE: "prompt"] tags.
CRITICAL REALISM & EXACTNESS RULE: 
- For a NEW image: Translate their EXACT request into English. DO NOT alter their core idea. Just append ", highly detailed masterpiece, extremely photorealistic, sharp focus, 8k resolution, cinematic lighting, raw photo, lifelike" to make it realistic.
- For EDITING an UPLOADED image: Write a prompt that EXACTLY describes the person's face, body, and background from the original image, but seamlessly apply the user's requested changes exactly as they asked. Ensure the prompt maintains the realism tags."""

def upload_image(file_bytes, file_name, file_type):
    # Free Hosting සර්වර් දෙකකටම ට්‍රයි කරනවා Error එන එක නවත්තන්න
    try:
        res = requests.post("https://catbox.moe/user/api.php", data={'reqtype': 'fileupload'}, files={'fileToUpload': (file_name, file_bytes, file_type)}, timeout=10)
        if res.status_code == 200: return res.text.strip()
    except:
        pass
    try:
        res = requests.post("https://uguu.se/upload.php", files={'files[]': (file_name, file_bytes, file_type)}, timeout=10)
        if res.status_code == 200: return res.json()["files"][0]["url"]
    except:
        pass
    return ""

def display_and_clean_text(content, latest_img_url="", is_history=False):
    clean_text = re.sub(r'\[IMAGE:\s*["\']?(.*?)["\']?\]', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    image_matches = re.findall(r'\[IMAGE:\s*["\']?(.*?)["\']?\]', content, flags=re.IGNORECASE | re.DOTALL)
    for img_prompt in image_matches:
        if not is_history:
            st.toast("🎨 AI විසින් රූපයක් නිර්මාණය කරමින් පවතී...", icon="⚙️")
        seed = random.randint(1, 999999)
        # FLUX එන්ජිම හරහා උපරිම Quality එකෙන් රූපය ගැනීම
        img_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(img_prompt.strip())}?width=768&height=1024&nologo=true&seed={seed}&model=flux"
        if latest_img_url:
            img_url += f"&image={latest_img_url}"
        st.image(img_url)
        
    return clean_text
