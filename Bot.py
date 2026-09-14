import os
import re
import requests
import threading
from flask import Flask
import telebot

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Ultra-Fast Instagram Engine Active!"

def clean_url(url: str) -> str:
    match = re.search(r'(https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/[A-Za-z0-9_-]+)', url)
    return match.group(1) if match else url.split('?')[0]

def extract_media(url: str):
    target_url = clean_url(url)
    
    # Engine 1: Cobalt Core API (ਬਿਨਾਂ ਵਾਟਰਮਾਰਕ, ਫੁੱਲ ਕੁਆਲਿਟੀ)
    cobalt_servers = [
        "https://api.cobalt.tools",
        "https://cobalt.api.scpt.tw",
        "https://api.server.cobalt.tools"
    ]
    for srv in cobalt_servers:
        try:
            r = requests.post(
                f"{srv}/",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json={"url": target_url, "videoQuality": "max"},
                timeout=8
            )
            if r.status_code == 200:
                res_data = r.json()
                if "url" in res_data:
                    return res_data["url"]
                if res_data.get("status") == "picker" and "picker" in res_data:
                    return res_data["picker"][0]["url"]
        except Exception:
            continue

    # Engine 2: Fast High-Speed Web Scraper
    try:
        api_res = requests.get(f"https://api.vkrdownloader.com/server?vkr={target_url}", timeout=10).json()
        download_url = api_res.get("data", {}).get("download_url") or api_res.get("download_url")
        if download_url:
            return download_url
    except Exception:
        pass

    # Engine 3: Alternative Deno CDN Bridge
    try:
        res = requests.get(f"https://insta-downloader.deno.dev/api?url={target_url}", timeout=10).json()
        if isinstance(res, dict) and "url" in res:
            return res["url"]
        if isinstance(res, list) and len(res) > 0 and "url" in res[0]:
            return res[0]["url"]
    except Exception:
        pass

    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 **Welcome!**\n\nSend any **Instagram Reel or Post** link here.\n"
        "⚡ Original Full Quality (No Watermark, No Ads).",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: True)
def handle_download(message):
    text = message.text or ""
    if "instagram.com" not in text:
        bot.reply_to(message, "⚠️ Please send a valid Instagram Reel link.")
        return

    status = bot.reply_to(message, "⚡ **Processing Full Quality Media...**", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        media_url = extract_media(text.strip())

        if not media_url:
            bot.edit_message_text(
                "❌ **Download Failed.** The Reel might be restricted or invalid.",
                chat_id=message.chat.id,
                message_id=status.message_id,
                parse_mode="Markdown"
            )
            return

        bot.edit_message_text("📤 **Uploading Video...**", chat_id=message.chat.id, message_id=status.message_id, parse_mode="Markdown")

        # ਵੀਡੀਓ ਫਾਈਲ ਡਾਊਨਲੋਡ ਕਰਕੇ ਭੇਜਣਾ
        temp_file = f"video_{message.message_id}.mp4"
        with requests.get(media_url, stream=True, timeout=30) as r:
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
                caption="🎬 **Here is your video in Original Full HD/4K!**",
                parse_mode="Markdown"
            )

        if os.path.exists(temp_file):
            os.remove(temp_file)

        bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)

    except Exception as e:
        bot.edit_message_text("❌ Error while sending video. Please try again.", chat_id=message.chat.id, message_id=status.message_id)

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
