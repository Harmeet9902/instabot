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

def clean_instagram_link(raw_url: str) -> str:
    # ਲਿੰਕ ਵਿੱਚੋਂ ਸਿਰਫ਼ ਅਸਲ ਸ਼ਾਰਟਕੋਡ ਕੱਢ ਕੇ ਸਾਫ਼ ਲਿੰਕ ਤਿਆਰ ਕਰਨਾ
    match = re.search(r'/(?:reel|p|tv)/([A-Za-z0-9_-]+)', raw_url)
    if match:
        return f"https://www.instagram.com/reel/{match.group(1)}/"
    return raw_url.split('?')[0].strip()

def extract_media(raw_url: str):
    clean_url = clean_instagram_link(raw_url)
    encoded_url = urllib.parse.quote(clean_url, safe='')
    endpoint = f"https://{RAPIDAPI_HOST}/download?url={encoded_url}"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(endpoint, headers=headers, timeout=25)
        if response.status_code == 200:
            data = response.json()

            # ਲਿਸਟ ਫਾਰਮੈਟ ਚੈੱਕ ਕਰਨਾ
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                url = item.get("download_url") or item.get("url") or item.get("video_url")
                if url:
                    return url, "video"

            # ਡਿਕਸ਼ਨਰੀ ਫਾਰਮੈਟ ਚੈੱਕ ਕਰਨਾ
            if isinstance(data, dict):
                # ਸਿੱਧੇ ਲਿੰਕ
                direct_url = data.get("download_url") or data.get("video_url") or data.get("url")
                if direct_url:
                    return direct_url, "video"

                # data ਆਬਜੈਕਟ ਦੇ ਅੰਦਰ
                sub_data = data.get("data")
                if isinstance(sub_data, dict):
                    url = sub_data.get("download_url") or sub_data.get("video_url") or sub_data.get("url")
                    if url:
                        return url, "video"
                elif isinstance(sub_data, list) and len(sub_data) > 0:
                    first = sub_data[0]
                    url = first.get("download_url") or first.get("url") or first.get("video_url")
                    if url:
                        return url, "video"

                # ਫੋਟੋ ਫਾਲਬੈਕ
                photo_url = data.get("image_url") or (data.get("data", {}).get("image_url") if isinstance(data.get("data"), dict) else None)
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
                "❌ **Download Failed.**\nThe reel might be private or restricted by Instagram.",
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
