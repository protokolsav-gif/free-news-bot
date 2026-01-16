import feedparser
import requests
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from openai import OpenAI

# ===== НАСТРОЙКИ =====

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

RSS_FEEDS = [
    "https://kubnews.ru/rss/",
    "https://yuga.ru/rss/",
    "https://93.ru/rss/",
    "https://www.livekuban.ru/rss",
]

KEYWORDS = [
    "арест", "суд", "уголов", "полици", "протест",
    "выбор", "корруп", "задерж", "обыск"
]

# ===== TELEGRAM =====

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ===== AI =====

def summarize(news):
    prompt = (
        "Ты редактор независимого медиа. "
        "Кратко выдели 3–5 самых важных новостей:\n\n"
        + "\n".join(news)
    )

    r = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return r.output_text

# ===== MAIN =====

def main():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)

    if not (6 <= now.hour <= 22):
        return

    cutoff = now - timedelta(hours=1)
    collected = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            if not hasattr(e, "published_parsed"):
                continue

            published = datetime(*e.published_parsed[:6], tzinfo=tz)
            if published < cutoff:
                continue

            text = (e.title + " " + getattr(e, "summary", "")).lower()
            if any(k in text for k in KEYWORDS):
                collected.append(f"• {e.title}\n{e.link}")

    if not collected:
        send("За последний час — ничего важного.")
        return

    summary = summarize(collected)
    send("🗞 Сводка за последний час:\n\n" + summary)

if __name__ == "__main__":
    main()
