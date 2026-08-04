# magespace.py - Streamlit Cloud Optimized Bot
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def generate_image_magespace(prompt_text, is_nsfw=False, init_image_b64=None):
    try:
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
        
        print(f"🤖 [MAGE BOT] ආරම්භ විය. Prompt: {prompt_text}")
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.mage.space/")
        time.sleep(5) # සයිට් එක ලෝඩ් වෙනකම් ඉන්නවා
        
        try:
            # සර්ච් බාර් එක හොයාගෙන Prompt එක ටයිප් කිරීම
            element = driver.find_element(By.ID, "search-bar")
            element.send_keys(prompt_text)
            element.send_keys(Keys.ENTER)
            
            print("⏳ ඡායාරූපය නිර්මාණය වෙමින් පවතී (තත්පර 15ක් පමණ රැඳී සිටින්න)...")
            time.sleep(15) 
            
            # හැදුණු ෆොටෝ එකේ ලින්ක් එක ගැනීම
            elementer = driver.find_elements(By.XPATH,"//img[contains(@class, 'mantine-Image-image')]")
            if elementer:
                img_url = elementer[-1].get_attribute("src")
                img_bytes = requests.get(img_url).content
                print("✅ ඡායාරූපය සාර්ථකව බාගත කරගත්තා!")
                driver.quit()
                return img_bytes
        except Exception as e:
            print("❌ [MAGE BOT LOGIC ERROR]:", e)
            
        driver.quit()
        return None
    except Exception as e:
        print(f"❌ [DRIVER ERROR]: {e}")
        return None
