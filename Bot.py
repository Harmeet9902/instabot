import os
import re
import json
import threading
import requests
from flask import Flask
import telebot

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "R-Download Core Engine Live!"

def shortcode_to_media_id(shortcode: str) -> int:
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    media_id = 0
    for char in shortcode:
        media_id = (media_id * 64) + alphabet.index(char)
    return media_id

def get_shortcode(url: str) -> str:
    match = re.search(r'/(?:reel|p|tv)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def r_download_engine(url: str):
    shortcode = get_shortcode(url)
    if not shortcode:
        return None

    media_id = shortcode_to_media_id(shortcode)

    # 1. Instagram iOS Native App Headers (Like R-Download)
    headers = {
        'User-Agent': 'Instagram 278.0.0.19.115 (iPhone14,2; iOS 16_5; en_US; en-US; scale=3.00; 1170x2532; 458887549)',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-IG-App-ID': '936619743392459',
        'X-ASBD-ID': '198387',
        'X-IG-WWW-Claim': '0',
        'Origin': 'https://www.instagram.com',
        'Referer': f'https://www.instagram.com/reel/{shortcode}/'
    }

    # Engine Method 1: Direct Instagram Mobile Info API
    try:
        api_url = f"https://i.instagram.com/api/v1/media/{media_id}/info/"
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get('items', [])
            if items:
                item = items[0]
                if 'video_versions' in item:
                    # ਓਰੀਜਨਲ ਮੈਕਸ ਕੁਆਲਿਟੀ ਵੀਡੀਓ CDN
                    return item['video_versions'][0]['url']
                elif 'image_versions2' in item:
                    return item['image_versions2']['candidates'][0]['url']
    except Exception:
        pass

    # Engine Method 2: FastDL Backend Scraper
    try:
        post_url = f"https://www.instagram.com/reel/{shortcode}/"
        res = requests.post(
            "https://fastdl.app/c/",
            data={"url": post_url},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=10
        )
        match = re.search(r'href="(https://[^"]+dl=1[^"]*)"', res.text)
        if match:
            return match.group(1)
    except Exception:
        pass

    # Engine Method 3: SaveTube / InDown Scraper Fallback
    try:
        res = requests.get(f"https://api.vkrdownloader.com/server?vkr=https://www.instagram.com/reel/{shortcode}/", timeout=10)
        data = res.json()
        download_url = data.get("data", {}).get("download_url") or data.get("download_url")
        if download_url:
            return download_url
    except Exception:
        pass

    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 **Welcome!**\n\n"
        "📥 Send any **Instagram Reel or Post** link here.\n\n"
        "⚡ **Original Maximum Quality** (No Watermark, No Ads, R-Engine).",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: True)
def handle_download(message):
    text = message.text or ""
    if "instagram.com" not in text:
        bot.reply_to(message, "⚠️ **Invalid Link!** Please send a valid Instagram Reel/Post link.")
        return

    status = bot.reply_to(message, "⚡ **Processing in Original Full HD/4K...**\nConnecting to Instagram CDN...", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        media_url = r_download_engine(text.strip())

        if not media_url:
            bot.edit_message_text(
                "❌ **Download Failed.**\nReel might be private or from an age-restricted account.",
                chat_id=message.chat.id,
                message_id=status.message_id,
                parse_mode="Markdown"
            )
            return

        bot.edit_message_text("📤 **Downloading & Sending Video...**", chat_id=message.chat.id, message_id=status.message_id, parse_mode="Markdown")

        temp_file = f"media_{message.message_id}.mp4"
        
        # ਸਿੱਧਾ CDN ਤੋਂ ਵੀਡੀਓ ਡਾਊਨਲੋਡ ਕਰਨਾ
        stream_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X)'
        }
        with requests.get(media_url, headers=stream_headers, stream=True, timeout=40) as r:
            r.raise_for_status()
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

        with open(temp_file, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                supports_streaming=True,
                caption="🎬 **Here is your video in Original Quality!**",
                parse_mode="Markdown"
            )

        if os.path.exists(temp_file):
            os.remove(temp_file)

        bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)

    except Exception as e:
        bot.edit_message_text("❌ An error occurred during download. Please try again.", chat_id=message.chat.id, message_id=status.message_id)

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
