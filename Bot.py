import os
import re
import urllib.parse
import threading
import requests
from flask import Flask, request, jsonify, render_template_string
import telebot

BOT_TOKEN = "8872648718:AAGbgUSgZ07twAle3lzP71krsz9iEfwNn2w"
RAPIDAPI_KEY = "a9e87211f4msh6140869f034e657p1029f9jsn04a5d7c9ce6f"
RAPIDAPI_HOST = "instagram-reels-downloader-api.p.rapidapi.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ਸਾਡੀ ਆਪਣੀ Clean, Modern, 100% Ad-Free Mini App ਦਾ HTML/UI
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insta Downloader</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0f172a; color: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .card { background: #1e293b; border-radius: 20px; padding: 28px 24px; width: 100%; max-width: 420px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; border: 1px solid #334155; }
        h1 { font-size: 22px; font-weight: 700; margin-bottom: 8px; background: linear-gradient(135deg, #f43f5e, #fb7185); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p { font-size: 13px; color: #94a3b8; margin-bottom: 24px; }
        .input-group { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
        input { width: 100%; padding: 14px 16px; border-radius: 12px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 15px; outline: none; transition: 0.3s; }
        input:focus { border-color: #f43f5e; }
        button.btn { width: 100%; padding: 14px; border-radius: 12px; border: none; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; background: linear-gradient(135deg, #e11d48, #f43f5e); color: #fff; }
        button.btn:active { transform: scale(0.98); }
        #status { font-size: 13px; color: #38bdf8; margin-top: 15px; display: none; }
        #result-box { margin-top: 20px; display: none; }
        .dl-btn { display: block; width: 100%; padding: 14px; background: #10b981; color: white; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 15px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Instagram Saver</h1>
        <p>Original 4K/HD • Zero Ads • No Watermark</p>
        
        <div class="input-group">
            <input type="text" id="urlInput" placeholder="Paste Instagram Link Here..." />
            <button class="btn" onclick="startDownload()">Download Now</button>
        </div>

        <div id="status">⚡ Fetching Original High Quality...</div>
        <div id="result-box">
            <a id="downloadLink" href="#" target="_blank" class="dl-btn">⬇️ Save Video / Photo</a>
        </div>
    </div>

    <script>
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();

        async function startDownload() {
            const url = document.getElementById('urlInput').value.trim();
            const status = document.getElementById('status');
            const resultBox = document.getElementById('result-box');
            const downloadLink = document.getElementById('downloadLink');

            if (!url.includes("instagram.com")) {
                alert("Please paste a valid Instagram link!");
                return;
            }

            status.style.display = 'block';
            status.innerText = "⚡ Connecting to media server...";
            resultBox.style.display = 'none';

            try {
                const res = await fetch(`/api/get-video?url=${encodeURIComponent(url)}`);
                const data = await res.json();

                if (data.success && data.media_url) {
                    status.style.display = 'none';
                    downloadLink.href = data.media_url;
                    resultBox.style.display = 'block';
                } else {
                    status.innerText = "❌ Download failed. Please verify the link.";
                }
            } catch (err) {
                status.innerText = "❌ Network error. Please try again.";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/get-video')
def get_video_api():
    raw_url = request.args.get('url', '')
    match = re.search(r'/(?:reel|p|tv)/([A-Za-z0-9_-]+)', raw_url)
    clean_url = f"https://www.instagram.com/reel/{match.group(1)}/" if match else raw_url.split('?')[0]

    endpoint = f"https://{RAPIDAPI_HOST}/download?url={urllib.parse.quote(clean_url, safe='')}"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }

    try:
        r = requests.get(endpoint, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            video_url = data.get("download_url") or data.get("video_url") or (data.get("data", {}).get("download_url") if isinstance(data.get("data"), dict) else None)
            if not video_url and isinstance(data.get("data"), list) and len(data["data"]) > 0:
                video_url = data["data"][0].get("url") or data["data"][0].get("download_url")
            if video_url:
                return jsonify({"success": True, "media_url": video_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "Media not found"})

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
