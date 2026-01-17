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

# ===== TELEGRAM =====

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text[:3900],
        "disable_web_page_preview": True
    })
    r.raise_for_status()

# ===== AI =====

def pick_top(items):
    """
    items: list of (title, link)
    """
    items = items[:40]  # ограничим, чтобы было дёшево

    joined = "\n".join([f"{i+1}. {t}\n{l}" for i, (t, l) in enumerate(items)])

    prompt = f"""
Ты новостной редактор. Стиль: сухо, нейтрально, без эмоций.
Выбери 5 самых важных новостей из списка (приоритет Кубань/Краснодар/Сочи/Новороссийск, но если нет — бери самые значимые).

Формат ответа:
1) Заголовок (коротко)
— 1 фраза: что случилось
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

    # работаем только с 06:00 до 22:00 МСК
    if not (6 <= now.hour <= 22):
        send(f"😴 Сейчас нерабочее время (МСК): {now.strftime('%H:%M')}.")
        return

    # берём не 1 час, а 6 часов — чтобы точно было что выбрать
    cutoff = now - timedelta(hours=6)

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
            if title and link:
                found.append((title, link))

    if not found:
        send("🗞 За последние 6 часов не нашёл новостей в RSS (похоже, ленты пустые/падают).")
        return

    # Даже если нейронка упадёт — пришлём список ссылок, чтобы ты увидел, что есть вход
    try:
        text = pick_top(found)
        send("🗞 Топ за последние 6 часов (МСК):\n\n" + text)
    except Exception as e:
        msg = "🗞 (без нейронки) Список свежих новостей за 6 часов:\n\n"
        for i, (t, l) in enumerate(found[:15], 1):
            msg += f"{i}. {t}\n{l}\n\n"
        send(msg)
        print("OPENAI ERROR:", e)

if __name__ == "__main__":
    main()
