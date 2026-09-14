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
    return "R-Download Moody Engine Live!"

def fetch_moody_media(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Accept": "*/*",
        "Referer": "https://www.moody0100.com/"
    }

    # Moody0100 R-Download Core API
    try:
        api_endpoint = "https://www.moody0100.com/api/v1/download"
        res = requests.post(api_endpoint, json={"url": url}, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            media_url = data.get("url") or data.get("download_url") or data.get("media")
            if media_url:
                return media_url, "video" if "mp4" in media_url.lower() else "photo"
    except Exception:
        pass

    # Moody0100 Direct Endpoint Fallback
    try:
        direct_url = f"https://www.moody0100.com/file/fetch?url={url}"
        res = requests.get(direct_url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and data.get("url"):
                return data["url"], "video"
    except Exception:
        pass

    # Ddownr / Snap High-Speed Direct Engine
    try:
        res = requests.get(f"https://api.vkrdownloader.com/server?vkr={url}", timeout=15).json()
        d_url = res.get("data", {}).get("download_url") or res.get("download_url")
        if d_url:
            return d_url, "video"
    except Exception:
        pass

    return None, None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 **Welcome!**\n\n"
        "Instagram ਤੋਂ ਕੋਈ ਵੀ ਲਿੰਕ (Reel ਜਾਂ Photo) ਸਿੱਧਾ ਇੱਥੇ ਭੇਜੋ।\n"
        "⚡ **Original Maximum Quality** (Powered by R⤓Download Engine).",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: True)
def handle_download(message):
    raw_url = message.text.strip() if message.text else ""

    if "instagram.com" not in raw_url:
        bot.reply_to(message, "⚠️ ਕਿਰਪਾ ਕਰਕੇ ਇੰਸਟਾਗ੍ਰਾਮ ਦਾ ਲਿੰਕ ਭੇਜੋ।")
        return

    status = bot.reply_to(message, "⚡ **Processing with R-Download Engine...**\nOriginal 4K/HD ਕੁਆਲਿਟੀ ਫੈਚ ਹੋ ਰਹੀ ਹੈ...", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        download_url, media_type = fetch_moody_media(raw_url)

        if not download_url:
            bot.edit_message_text(
                "❌ ਵੀਡੀਓ ਲੱਭੀ ਨਹੀਂ ਜਾਂ ਲਿੰਕ ਪ੍ਰਾਈਵੇਟ ਹੈ।",
                chat_id=message.chat.id,
                message_id=status.message_id
            )
            return

        bot.edit_message_text("📤 **ਫਾਈਲ ਅੱਪਲੋਡ ਹੋ ਰਹੀ ਹੈ...**", chat_id=message.chat.id, message_id=status.message_id)

        temp_filename = f"media_{message.message_id}.mp4" if media_type == "video" else f"media_{message.message_id}.jpg"

        req_headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}
        with requests.get(download_url, headers=req_headers, stream=True, timeout=45) as r:
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
                    caption="🎬 **Here is your video in Original Full Quality!**",
                    parse_mode="Markdown"
                )
            else:
                bot.send_photo(
                    message.chat.id,
                    media_file,
                    caption="🖼️ **Original Full Quality Photo**",
                    parse_mode="Markdown"
                )

        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)

    except Exception:
        bot.edit_message_text("❌ ਕੋਈ ਸਮੱਸਿਆ ਆਈ ਹੈ, ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।", chat_id=message.chat.id, message_id=status.message_id)

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
