import os
import requests
import threading
from flask import Flask
import telebot

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Server Active 24/7"

def fetch_direct_media(raw_url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    # Engine 1: ਸਿੱਧਾ ਪੂਰਾ ਲਿੰਕ ਭੇਜਣ ਵਾਲਾ ਓਪਨ ਸਰਵਰ
    try:
        api_url = f"https://api.siputzx.my.id/api/d/ig?url={raw_url}"
        res = requests.get(api_url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") and data.get("data"):
                media_list = data["data"]
                if isinstance(media_list, list) and len(media_list) > 0:
                    first_item = media_list[0]
                    download_url = first_item.get("url")
                    m_type = "video" if "mp4" in download_url.lower() or "video" in str(first_item) else "photo"
                    return download_url, m_type
    except Exception:
        pass

    # Engine 2: ਫਾਲਬੈਕ ਵੈੱਬ ਸਰਵਰ
    try:
        api_url = f"https://widipe.com/download/igdl?url={raw_url}"
        res = requests.get(api_url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") and data.get("result"):
                results = data["result"]
                if isinstance(results, list) and len(results) > 0:
                    d_url = results[0].get("url")
                    return d_url, "video"
    except Exception:
        pass

    # Engine 3: ਯੂਨੀਵਰਸਲ ਡਾਊਨਲੋਡਰ ਗੇਟਵੇ
    try:
        api_url = f"https://api.vkrdownloader.com/server?vkr={raw_url}"
        res = requests.get(api_url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            d_url = data.get("data", {}).get("download_url") or data.get("download_url")
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
        "Instagram ਤੋਂ ਕੋਈ ਵੀ ਲਿੰਕ ਸਿੱਧਾ ਕਾਪੀ ਕਰਕੇ ਇੱਥੇ ਪੇਸਟ ਕਰੋ।\n"
        "⚡ ਓਰੀਜਨਲ ਫੁੱਲ ਕੁਆਲਿਟੀ ਵਿੱਚ ਮੀਡੀਆ ਤੁਰੰਤ ਡਾਊਨਲੋਡ ਹੋ ਜਾਵੇਗਾ।",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: True)
def handle_download(message):
    raw_url = message.text.strip() if message.text else ""

    if "instagram.com" not in raw_url:
        bot.reply_to(message, "⚠️ ਕਿਰਪਾ ਕਰਕੇ ਇੰਸਟਾਗ੍ਰਾਮ ਦਾ ਲਿੰਕ ਭੇਜੋ।")
        return

    status = bot.reply_to(message, "⚡ **Processing... ਮੀਡੀਆ ਫੈਚ ਹੋ ਰਿਹਾ ਹੈ**", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_video')

    try:
        download_url, media_type = fetch_direct_media(raw_url)

        if not download_url:
            bot.edit_message_text(
                "❌ ਵੀਡੀਓ ਲੱਭੀ ਨਹੀਂ। ਲਿੰਕ ਚੈੱਕ ਕਰੋ ਜੀ।",
                chat_id=message.chat.id,
                message_id=status.message_id
            )
            return

        bot.edit_message_text("📤 **ਫਾਈਲ ਭੇਜੀ ਜਾ ਰਹੀ ਹੈ...**", chat_id=message.chat.id, message_id=status.message_id)

        temp_filename = f"media_{message.message_id}.mp4" if media_type == "video" else f"media_{message.message_id}.jpg"
        
        # ਵੀਡੀਓ ਸਟ੍ਰੀਮ ਡਾਊਨਲੋਡ
        with requests.get(download_url, stream=True, timeout=40) as r:
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
                    caption="🎬 **Original Full Quality (No Watermark)**",
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
        bot.edit_message_text("❌ ਕੋਈ ਦਿੱਕਤ ਆਈ ਹੈ, ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।", chat_id=message.chat.id, message_id=status.message_id)

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
