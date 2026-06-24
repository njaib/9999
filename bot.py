import telebot
import feedparser
import time
from deep_translator import GoogleTranslator
import re
import pycountry
import flag
import threading
from flask import Flask
import os

# --- CONFIG ---
BOT_TOKEN = "8805157616:AAHhD_bRckdy3CH_KkmGX8lXbLVg08OE83M"
CHANNEL_ID = "@AFGaziz"

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.foxnews.com/foxnews/latest",
    "https://www.france24.com/en/rss",
    "https://rss.dw.com/xml/rss-en-all",
    "http://rss.cnn.com/rss/edition_world.rss",
    "https://www.theguardian.com/world/rss",
    "https://www.rt.com/rss/news/"
]

bot = telebot.TeleBot(BOT_TOKEN)
translator = GoogleTranslator(source='auto', target='fa')
sent_news = set()

# --- Flask server (fix Render port issue) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram News Bot is running ✔"

# --- FUNCTIONS ---
def get_country_flag(text):
    for country in pycountry.countries:
        if country.name in text:
            return flag.flag(country.alpha_2)
    return "🌍"

def get_image_url(entry):
    if 'media_content' in entry:
        return entry.media_content[0].get('url')

    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href')

    if 'description' in entry:
        img_match = re.search(r'<img src="([^"]+)"', entry.description)
        if img_match:
            return img_match.group(1)

    return None

def process_news():
    while True:
        for url in RSS_FEEDS:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                news_id = entry.get('id', entry.link)

                if news_id in sent_news:
                    continue

                try:
                    title = entry.title
                    summary = re.sub('<[^<]+?>', '', entry.get('summary', ''))

                    country_flag = get_country_flag(title + " " + summary)

                    translated_title = translator.translate(title)
                    translated_summary = translator.translate(summary[:1000])

                    img_url = get_image_url(entry)

                    caption = (
                        f"{country_flag} <b>{translated_title}</b>\n\n"
                        f"{translated_summary}\n\n"
                        f"🔗 <a href='{entry.link}'>مشاهده منبع خبر</a>\n"
                        f"🆔 {CHANNEL_ID}"
                    )

                    if img_url:
                        bot.send_photo(CHANNEL_ID, img_url, caption=caption, parse_mode='HTML')
                    else:
                        bot.send_message(CHANNEL_ID, caption, parse_mode='HTML')

                    print("Sent:", title)
                    sent_news.add(news_id)

                    time.sleep(60)

                except Exception as e:
                    print("Error:", e)

# --- RUN BOTH BOT + WEB SERVER ---
if __name__ == "__main__":
    print("Bot starting...")

    # Run bot in background thread
    t = threading.Thread(target=process_news)
    t.daemon = True
    t.start()

    # Run web server for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)