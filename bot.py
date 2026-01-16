import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

RSS_FEEDS = [
    "https://www.reuters.com/world/rss",
    "https://www.politico.com/rss/politics08.xml",
    "https://www.theguardian.com/world/rss",
]

KEYWORDS = [
    "sanction", "arrest", "law", "ban", "court",
    "investigation", "leak", "police", "government",
    "election", "corruption", "protest"
]
def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": text})

    try:
        data = r.json()
    except Exception:
        data = {"not_json": r.text}

    print("TELEGRAM RESPONSE:", data)

    if not r.ok or (isinstance(data, dict) and data.get("ok") is False):
        raise RuntimeError(f"Telegram error: {data}")


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)

    found = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            if not hasattr(e, "published_parsed"):
                continue

            published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            if published < cutoff:
                continue

            text = (e.title + " " + getattr(e, "summary", "")).lower()
            if any(k in text for k in KEYWORDS):
                found.append((e.title, e.link))

    if not found:
        send("За последний час — ничего важного.")
        return

    message = "🗞 Новости за последний час:\n\n"
    for i, (title, link) in enumerate(found[:15], 1):
        message += f"{i}. {title}\n{link}\n\n"

    send(message)


if __name__ == "__main__":
    main()

