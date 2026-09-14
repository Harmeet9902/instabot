import os
import re
import urllib.parse
import threading
import requests
from flask import Flask
import telebot

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
RAPIDAPI_KEY = "a9e87211f4msh6140869f034e657p1029f9jsn04a5d7c9ce6f"
RAPIDAPI_HOST = "instagram-reels-downloader-api.p.rapidapi.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Ultra-Fast Downloader Online 24/7"

def extract_media(url: str):
    encoded_url = urllib.parse.quote(url, safe='')
    endpoint = f"https://{RAPIDAPI_HOST}/download?url={encoded_url}"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(endpoint, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()

            # Video Link Parsing
            video_url = (
                data.get("download_url") or
                data.get("video_url") or
                data.get("data", {}).get("download_url") or
                data.get("data", {}).get("video_url")
            )
            if video_url:
                return video_url, "video"

            # Direct results array parsing
            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                first = data["data"][0]
                media_link = first.get("url") or first.get("download_url")
                media_type = "video" if first.get("type") == "video" or "mp4" in str(media_link).lower() else "photo"
                return media_link, media_type

            # Photo fallback parsing
            photo_url = data.get("image_url") or data.get("data", {}).get("image_url")
            if photo_url:
                return photo_url, "photo"

    except Exception:
        pass

    return None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome!**\n\n"
        "Send or paste any **Instagram Reel, Video, or Photo** link here.\n\n"
        "⚡ Original Maximum Quality (No Watermark, No Ads)."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_download(message):
    text = message.text or ""
    if "instagram.com" not in text:
        bot.reply_to(message, "⚠️ **Invalid Link!** Please send a valid Instagram link.", parse_mode="Markdown")
        return

    status = bot.reply_to(message, "⚡ **Processing your link...**\nFetching original high-quality media, please wait.", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        media_url, media_type = extract_media(text.strip())

        if not media_url:
            bot.edit_message_text(
                "❌ **Download Failed.**\nThe reel might be private or temporarily restricted.",
                chat_id=message.chat.id,
                message_id=status.message_id,
                parse_mode="Markdown"
            )
            return

        bot.edit_message_text("📤 **Uploading to Telegram...**", chat_id=message.chat.id, message_id=status.message_id, parse_mode="Markdown")

        temp_filename = f"media_{message.message_id}.mp4" if media_type == "video" else f"media_{message.message_id}.jpg"

        with requests.get(media_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(temp_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

        with open(temp_filename, 'rb') as f:
            if media_type == "video":
                bot.send_video(
                    message.chat.id,
                    f,
                    supports_streaming=True,
                    caption="🎬 **Original High Quality (No Watermark)**",
                    parse_mode="Markdown"
                )
            else:
                bot.send_photo(
                    message.chat.id,
                    f,
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
