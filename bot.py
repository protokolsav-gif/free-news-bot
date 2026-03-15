import os
import re
import requests
import feedparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from openai import OpenAI

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

SENT_FILE = "sent_links.txt"

RSS_FEEDS = [
    "https://www.rbc.ru/rbcfreenews.rss",
    "https://www.kommersant.ru/RSS/news.xml",
    "https://meduza.io/rss/all",
    "https://7x7-journal.ru/feed",
    "https://93.ru/rss/",
    "https://www.livekuban.ru/rss",
    "https://kubnews.ru/rss/",
    "https://yuga.ru/rss/",
]

REGION_WORDS = [
    "краснодар",
    "краснодарский край",
    "кубань",
    "сочи",
    "анап",
    "геленджик",
    "новороссийск",
    "туапсе",
    "армавир",
    "ейск",
    "сириус",
]

JUNK_WORDS = [
    "погода",
    "туризм",
    "турист",
    "пляж",
    "курортный",
    "афиша",
    "концерт",
    "фестиваль",
    "матч",
    "футбол",
    "хоккей",
    "спорт",
    "гороскоп",
    "шоу",
    "звезда",
    "рецепт",
]

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text[:3900],
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    r.raise_for_status()

def load_sent():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_sent(links):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

def normalize_title(title):
    title = title.lower().strip()
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"[«»\"'“”„]", "", title)
    return title

def is_junk(title):
    low = title.lower()
    return any(word in low for word in JUNK_WORDS)

def is_region_related(title, summary):
    text = (title + " " + summary).lower()
    return any(word in text for word in REGION_WORDS)

def pick_top(items):
    items = items[:30]

    joined = "\n".join(
        [f"{i+1}. {title}\n{link}" for i, (title, link) in enumerate(items)]
    )

    prompt = f"""
Ты редактор независимого общественно-политического издания «Протокол».

Тебе дали список новостей, связанных с Краснодарским краем.

Выбери 5 самых важных новостей.

Приоритет:
1. коррупция
2. имущество и бизнес элит
3. ФСБ, МВД, СК, суды
4. репрессии и политические дела
5. протесты, митинги, пикеты, гражданские акции
6. региональная политика
7. застройка и земельные конфликты
8. экология
9. давление на активистов и журналистов
10. крупные бизнес-конфликты

Игнорируй:
- спорт
- туризм
- развлечения
- бытовой шум
- курортную ерунду
- мелкие новости без общественного значения

Пиши:
- сухо
- коротко
- нейтрально
- без пафоса

Формат:
1) Заголовок
— что произошло, 1 короткая фраза
— ссылка

СПИСОК:
{joined}
""".strip()

    resp = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )
    return resp.output_text.strip()

def main():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)

    if not (6 <= now.hour <= 22):
        return

    cutoff = now - timedelta(hours=24)
    sent = load_sent()

    found = []
    seen_titles = set()

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for e in feed.entries:
            if not hasattr(e, "published_parsed"):
                continue

            published = datetime(*e.published_parsed[:6], tzinfo=tz)
            if published < cutoff:
                continue

            title = getattr(e, "title", "").strip()
            summary = getattr(e, "summary", "").strip()
            link = getattr(e, "link", "").strip()

            if not title or not link:
                continue

            if is_junk(title):
                continue

            if not is_region_related(title, summary):
                continue

            if link in sent:
                continue

            norm_title = normalize_title(title)
            if norm_title in seen_titles:
                continue

            seen_titles.add(norm_title)
            found.append((title, link))

    if not found:
        send("🗞 Новых важных новостей по Краснодарскому краю не найдено.")
        return

    try:
        text = pick_top(found)
        low = text.lower()

        if (not text.strip()) or ("ничего" in low and "важн" in low):
            msg = "🗞 Новые новости по Краснодарскому краю:\n\n"
            for i, (t, l) in enumerate(found[:10], 1):
                msg += f"{i}. {t}\n{l}\n\n"
            send(msg)
            save_sent([link for _, link in found[:10]])
        else:
            send("🗞 Важное по Краснодарскому краю:\n\n" + text)
            save_sent([link for _, link in found[:10]])

    except Exception as e:
        msg = "🗞 Новости по Краснодарскому краю (без нейронки):\n\n"
        for i, (t, l) in enumerate(found[:10], 1):
            msg += f"{i}. {t}\n{l}\n\n"
        send(msg)
        save_sent([link for _, link in found[:10]])
        print("OPENAI ERROR:", e)

if __name__ == "__main__":
    main()
