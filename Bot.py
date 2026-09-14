import os
import glob
import threading
from flask import Flask
import telebot
import yt_dlp

# ਤੁਹਾਡਾ ਬੋਟ ਟੋਕਨ
BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
bot = telebot.TeleBot(BOT_TOKEN)

# Render ਸਰਵਰ ਨੂੰ 24/7 ਐਕਟਿਵ ਰੱਖਣ ਲਈ ਡੰਮੀ ਵੈੱਬ ਸਰਵਰ
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def download_instagram(url, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_folder, '%(id)s_%(autonumber)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15'
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! 📥\nਕਿਸੇ ਵੀ Instagram Reel, Video ਜਾਂ Photo ਦਾ ਲਿੰਕ ਭੇਜੋ, ਮੈਂ ਓਰੀਜਨਲ ਕੁਆਲਿਟੀ ਵਿੱਚ ਡਾਊਨਲੋਡ ਕਰਕੇ ਭੇਜਾਂਗਾ।")

@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    text = message.text or ""
    if "instagram.com" not in text:
        bot.reply_to(message, "❌ ਕਿਰਪਾ ਕਰਕੇ ਸਿਰਫ਼ Instagram ਦਾ ਸਹੀ ਲਿੰਕ ਭੇਜੋ ਜੀ।")
        return

    status = bot.reply_to(message, "⏳ ਫੁੱਲ ਕੁਆਲਿਟੀ ਡਾਊਨਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...")
    user_folder = f"temp_{message.message_id}"

    try:
        download_instagram(text.strip(), user_folder)
        media_files = glob.glob(os.path.join(user_folder, "*"))

        if not media_files:
            bot.edit_message_text("❌ ਕੋਈ ਮੀਡੀਆ ਨਹੀਂ ਮਿਲਿਆ। ਅਕਾਊਂਟ ਪ੍ਰਾਈਵੇਟ ਤਾਂ ਨਹੀਂ?", chat_id=message.chat.id, message_id=status.message_id)
            return

        bot.edit_message_text("📤 ਭੇਜਿਆ ਜਾ ਰਿਹਾ ਹੈ...", chat_id=message.chat.id, message_id=status.message_id)

        for file_path in media_files:
            ext = file_path.lower().split('.')[-1]
            with open(file_path, 'rb') as f:
                if ext in ["mp4", "mkv", "mov", "webm"]:
                    bot.send_video(message.chat.id, f, caption="✅ ਫੁੱਲ ਕੁਆਲਿਟੀ ਵੀਡੀਓ")
                elif ext in ["jpg", "jpeg", "png", "webp"]:
                    bot.send_photo(message.chat.id, f, caption="✅ ਓਰੀਜਨਲ ਫੋਟੋ")

        bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)

    except Exception as e:
        bot.edit_message_text("❌ ਡਾਊਨਲੋਡ ਕਰਨ ਦੌਰਾਨ ਕੋਈ ਸਮੱਸਿਆ ਆਈ ਹੈ।", chat_id=message.chat.id, message_id=status.message_id)
    finally:
        if os.path.exists(user_folder):
            for f in glob.glob(os.path.join(user_folder, "*")):
                try: os.remove(f)
                except Exception: pass
            try: os.rmdir(user_folder)
            except Exception: pass

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
