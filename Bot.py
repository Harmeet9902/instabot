import os
import re
import threading
import requests
from flask import Flask
import telebot

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Server is Online 24/7"

def extract_media_stream(url: str):
    match = re.search(r'/(?:reel|p|tv)/([A-Za-z0-9_-]+)', url)
    if not match:
        return None, None
    shortcode = match.group(1)

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "*/*"
    }

    # Core Method 1: DDInstagram / EZ Fast CDN (Bypasses all IP restrictions)
    try:
        api_url = f"https://api.ddinstagram.com/videos/{shortcode}"
        res = requests.get(api_url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if "direct_url" in data:
                return data["direct_url"], "video"
    except Exception:
        pass

    # Core Method 2: Native Instagram App Proxy
    try:
        api_url = f"https://www.instagram.com/reel/{shortcode}/?__a=1&__d=dis"
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get('items', [])
            if items:
                item = items[0]
                if 'video_versions' in item:
                    return item['video_versions'][0]['url'], "video"
                elif 'image_versions2' in item:
                    return item['image_versions2']['candidates'][0]['url'], "photo"
    except Exception:
        pass

    # Core Method 3: High-Speed Web Engine
    try:
        res = requests.get(f"https://api.vkrdownloader.com/server?vkr=https://www.instagram.com/reel/{shortcode}/", timeout=12).json()
        d_url = res.get("data", {}).get("download_url") or res.get("download_url")
        if d_url:
            return d_url, "video"
    except Exception:
        pass

    return None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_msg = (
        "👋 **Welcome to Instagram Downloader!**\n\n"
        "📥 Send any **Instagram Reel, Video, or Photo** link.\n\n"
        "⚡ I will instantly fetch it in **Original Maximum Quality** (No Watermarks, No Ads)."
    )
    bot.reply_to(message, welcome_msg, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_download(message):
    text = message.text or ""
    if "instagram.com" not in text:
        bot.reply_to(message, "⚠️ **Invalid Link!** Please send a valid Instagram link.")
        return

    status = bot.reply_to(message, "⚡ **Processing your request...**\nConnecting to high-speed media servers...", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        media_url, media_type = extract_media_stream(text.strip())

        if not media_url:
            bot.edit_message_text(
                "❌ **Download Failed.**\nThe reel might be private or restricted by Instagram.",
                chat_id=message.chat.id,
                message_id=status.message_id,
                parse_mode="Markdown"
            )
            return

        bot.edit_message_text("📤 **Uploading file to Telegram...**", chat_id=message.chat.id, message_id=status.message_id, parse_mode="Markdown")

        temp_filename = f"media_{message.message_id}.mp4" if media_type == "video" else f"media_{message.message_id}.jpg"

        req_headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}
        with requests.get(media_url, headers=req_headers, stream=True, timeout=45) as r:
            r.raise_for_status()
            with open(temp_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

        with open(temp_filename, 'rb') as media_file:
            if media_type == "video":
                bot.send_video(
                    message.chat.id,
                    media_file,
                    supports_streaming=True,
                    caption="🎬 **Original Full HD/4K Video**",
                    parse_mode="Markdown"
                )
            else:
                bot.send_photo(
                    message.chat.id,
                    media_file,
                    caption="🖼️ **Original Quality Photo**",
                    parse_mode="Markdown"
                )

        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)

    except Exception:
        bot.edit_message_text("❌ **An error occurred during download.** Please try again.", chat_id=message.chat.id, message_id=status.message_id)

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
