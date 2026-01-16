import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# ===== НАСТРОЙКИ =====

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# ===== RSS =====

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

    # сочи
    "https://sochi24.tv/rss",
    "https://scapp.ru/rss",

    # новороссийск
    "https://novorab.ru/rss",

    # анапа
    "https://anapa.media/rss",

    # ейск
    "https://yeisk.info/rss",

    # официальное
    "https://admkrai.krasnodar.ru/rss",
]

KEYWORDS = [
    "арест", "суд", "задерж", "обыск", "дело",
    "протест", "выбор", "коррупц", "запрет",
    "штраф", "полици", "фсб", "ск", "чиновник"
]

# ===== TELEGRAM =====

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ===== OPENAI =====

def summarize(title, link):
    prompt = f"""
Ты редактор регионального издания.
Коротко (2–3 предложения) перескажи новость для редакционной сводки.
Без воды, без оценок.

Заголовок: {title}
Ссылка: {link}
"""

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-5-mini",
        "messages": [
            {"role": "system", "content": "Ты новостной редактор."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    r = requests.post(OPENAI_URL, headers=headers, json=data, timeout=30)
