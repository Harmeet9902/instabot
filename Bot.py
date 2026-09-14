import os
import re
import requests
import threading
from flask import Flask
import telebot

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
bot = telebot.TeleBot(BOT_TOKEN)

# Render 24/7 ਐਕਟਿਵ ਰੱਖਣ ਲਈ
app = Flask(__name__)

@app.route('/')
def home():
    return "Instagram Downloader Engine Live!"

def get_shortcode(url: str) -> str:
    match = re.search(r'/(?:reel|p|tv)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def fetch_instagram_media(url: str):
    shortcode = get_shortcode(url)
    if not shortcode:
        return None

    # Fast High-Quality API Endpoints
    api_urls = [
        f"https://api.vkrdownloader.com/server?vkr={url}",
        f"https://insta-downloader.deno.dev/api?url={url}"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    }

    # Method 1: Deno Fast Engine
    try:
        res = requests.get(f"https://insta-downloader.deno.dev/api?url=https://www.instagram.com/reel/{shortcode}/", headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if "url" in data:
                return [{"url": data["url"], "type": "video"}]
            if isinstance(data, list) and len(data) > 0 and "url" in data[0]:
                return [{"url": item["url"], "type": "video" if "mp4" in item.get("url", "") else "photo"} for item in data]
    except Exception:
        pass

    # Method 2: Fallback Engine
    try:
        res = requests.get(f"https://api.vkrdownloader.com/server?vkr=https://www.instagram.com/reel/{shortcode}/", headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            download_url = data.get("data", {}).get("download_url") or data.get("download_url")
            if download_url:
                return [{"url": download_url, "type": "video"}]
    except Exception:
        pass

    # Method 3: Instagram Direct GraphQL Fallback
    try:
        graphql_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
        res = requests.get(graphql_url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                item = items[0]
                if "video_versions" in item:
                    # ਸਭ ਤੋਂ ਉੱਚੀ ਕੁਆਲਿਟੀ ਵਾਲਾ ਵੀਡੀਓ CDN ਲਿੰਕ
                    best_video = item["video_versions"][0]["url"]
                    return [{"url": best_video, "type": "video"}]
                elif "image_versions2" in item:
                    best_img = item["image_versions2"]["candidates"][0]["url"]
                    return [{"url": best_img, "type": "photo"}]
    except Exception:
        pass

    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to Instagram 4K / HD Downloader!**\n\n"
        "📥 Send me any **Instagram Reel, Video, or Photo** link.\n\n"
        "⚡ I will fetch it in **Original Maximum Quality** without any watermark!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    raw_text = message.text or ""
    
    if "instagram.com" not in raw_text:
        bot.reply_to(message, "⚠️ **Please send a valid Instagram link!**", parse_mode="Markdown")
        return

    status_msg = bot.reply_to(message, "⚡ **Processing in Full Quality...**\nConnecting to high-speed media server...", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        media_list = fetch_instagram_media(raw_text.strip())

        if not media_list:
            bot.edit_message_text(
                "❌ **Failed to fetch media.**\n"
                "1. Check if the account is Private.\n"
                "2. The reel might be restricted or deleted.",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )
            return

        bot.edit_message_text("📤 **Downloading & Sending file...**", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

        for item in media_list:
            media_url = item["url"]
            media_type = item["type"]

            # ਫੁੱਲ ਕੁਆਲਿਟੀ ਫਾਈਲ ਡਾਊਨਲੋਡ ਕਰਕੇ ਭੇਜਣਾ
            resp = requests.get(media_url, stream=True, timeout=30)
            if resp.status_code == 200:
                temp_filename = f"media_{message.message_id}.mp4" if media_type == "video" else f"media_{message.message_id}.jpg"
                with open(temp_filename, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)

                with open(temp_filename, 'rb') as f:
                    if media_type == "video":
                        bot.send_video(
                            message.chat.id,
                            f,
                            supports_streaming=True,
                            caption="🎬 **Original Quality Video (No Watermark)**",
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

        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        bot.edit_message_text("❌ **An unexpected error occurred.** Please try again.", chat_id=message.chat.id, message_id=status_msg.message_id)

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
