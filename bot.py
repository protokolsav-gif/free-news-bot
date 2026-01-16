import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import openai

# === НАСТРОЙКИ ===

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

openai.api_key = OPENAI_API_KEY

# === RSS ===

RSS_FEEDS = [
    # федеральные
    "https://tass.ru/rss/v2.xml",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://www.interfax.ru/rss.asp",
    "https://www.kommersant.ru/rss/regions",

    # юг / край
    "https://kubnews.ru/rss/",
    "https://yuga.ru/rss/",
    "https://kavkaz-uzel.eu/rss",
    "https://fedpress.ru/rss/yug",
    "https://www.yugopolis.ru/rss",

    # краснодар
    "https://93.ru/rss/",
    "https://www.livekuban.ru/rss",
    "https://kubanpress.ru/rss",
    "https://www.dg-yug.ru/rss.xml",
    "https://yugtimes.com/rss/",
    "https://www.kuban.kp.ru/rss/",
    "https://kuban.mk.ru/rss/",
]

# === ТЕЛЕГРАМ ===

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })

# === NEURAL FIL
