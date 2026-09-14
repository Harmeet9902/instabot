import os
import glob
import re
import threading
from flask import Flask
import telebot
import yt_dlp

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
bot = telebot.TeleBot(BOT_TOKEN)

# Render ਸਰਵਰ ਨੂੰ ਐਕਟਿਵ ਰੱਖਣ ਲਈ
app = Flask(__name__)

@app.route('/')
def home():
    return "Instagram Bot is Live 24/7!"

def clean_instagram_url(url: str) -> str:
    # ਬੇਲੋੜੇ ਟਰੈਕਿੰਗ ਪੈਰਾਮੀਟਰ ਹਟਾਉਣਾ
    match = re.search(r'(https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/[A-Za-z0-9_-]+)', url)
    if match:
        return match.group(1) + "/"
    return url.split('?')[0]

def download_instagram(url: str, output_folder: str):
    os.makedirs(output_folder, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_folder, '%(id)s_%(autonumber)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to Instagram Downloader!**\n\n"
        "📥 Send or paste any **Instagram Reel, Video, or Photo** link here.\n\n"
        "✨ I will fetch and send it to you in **Original High Quality** without watermarks!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    raw_text = message.text or ""
    
    if "instagram.com" not in raw_text:
        bot.reply_to(message, "⚠️ **Invalid Link!**\nPlease send a valid Instagram Reel or Post link.", parse_mode="Markdown")
        return

    clean_url = clean_instagram_url(raw_text.strip())

    # 1. Processing ਮੈਸੇਜ ਦਿਖਾਉਣਾ
    status_msg = bot.reply_to(message, "⚡ **Processing your link...**\nFetching original high quality media, please wait.", parse_mode="Markdown")
    
    # 2. ਚੈਟ ਵਿੱਚ 'upload_video' ਜਾਂ 'typing' ਸਟੇਟਸ ਦਿਖਾਉਣਾ
    bot.send_chat_action(message.chat.id, 'upload_video')

    user_folder = f"temp_{message.message_id}"

    try:
        download_instagram(clean_url, user_folder)
        media_files = glob.glob(os.path.join(user_folder, "*"))

        if not media_files:
            bot.edit_message_text("❌ **Failed to fetch media.**\nThe account might be private or the link is expired.", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
            return

        bot.edit_message_text("📤 **Uploading your file...**", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

        for file_path in media_files:
            ext = file_path.lower().split('.')[-1]
            with open(file_path, 'rb') as f:
                if ext in ["mp4", "mkv", "mov", "webm"]:
                    bot.send_video(
                        message.chat.id, 
                        f, 
                        supports_streaming=True, 
                        caption="🎬 **Here is your video in Original Quality!**", 
                        parse_mode="Markdown"
                    )
                elif ext in ["jpg", "jpeg", "png", "webp"]:
                    bot.send_photo(
                        message.chat.id, 
                        f, 
                        caption="🖼️ **Here is your photo in Original Quality!**", 
                        parse_mode="Markdown"
                    )

        # ਕੰਮ ਪੂਰਾ ਹੁੰਦੇ ਹੀ Processing ਵਾਲਾ ਮੈਸੇਜ ਡਿਲੀਟ
        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        bot.edit_message_text("❌ **Error processing video.**\nPlease verify the link and try again.", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
    finally:
        # ਫਾਈਲਾਂ ਡਿਲੀਟ ਕਰਨਾ
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
