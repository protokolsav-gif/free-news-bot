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

SENT_FILE = "sent_links.txt"

# ===== TELEGRAM =====

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text[:3900],
        "disable_web_page_preview": True
    })
    r.raise_for_status()

# ===== ПАМЯТЬ =====

def load_sent():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_sent(links):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

# ===== AI =====

def pick_top(items):
    items = items[:40]

    joined = "\n".join(
        [f"{i+1}. {t}\n{l}" for i, (t, l) in enumerate(items)]
    )

    prompt = f"""
Ты новостной редактор. Стиль: сухо, нейтрально.
Выбери 5 самых важных новостей.

Формат:
1) Заголовок
— 1 фраза: что произошло
— ссылка

СПИСОК:
{joined}
""".strip()

    resp = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )
    return resp.output_text.strip()

# ===== MAIN =====

def main():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)

    if not (6 <= now.hour <= 22):
        return

    cutoff = now - timedelta(hours=6)

    sent = load_sent()
    found = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            if not hasattr(e, "published_parsed"):
                continue

            published = datetime(*e.published_parsed[:6], tzinfo=tz)
            if published < cutoff:
                continue

            title = getattr(e, "title", "").strip()
            link = getattr(e, "link", "").strip()

            if not title or not link:
                continue
            if link in sent:
                continue  # уже отправляли

            found.append((title, link))

    if not found:
        send("🗞 Новых новостей нет (всё уже отправляли).")
        return

    try:
        text = pick_top(found)
        send("🗞 Новые важные новости:\n\n" + text)

        # сохраняем ссылки, которые ушли
        save_sent([link for _, link in found])

    except Exception as e:
        msg = "🗞 Новые новости (без нейронки):\n\n"
        for i, (t, l) in enumerate(found[:10], 1):
            msg += f"{i}. {t}\n{l}\n\n"
        send(msg)
        save_sent([link for _, link in found[:10]])
        print("OPENAI ERROR:", e)

if __name__ == "__main__":
    main()
