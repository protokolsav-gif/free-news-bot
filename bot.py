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
            "parse_mode": "Markdown",
        },
        timeout=30,
    )
    r.raise_for_status()

def send_long(text):
    posts = text.split("---POST---")

    for post in posts:
        post = post.strip()
        if post:
            send(post)

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

def rewrite_news(items):
    items = items[:12]

    joined = "\n\n".join(
        [f"{i+1}. {title}\n{link}" for i, (title, link) in enumerate(items)]
    )

    prompt = f"""
Ты редактор независимого регионального медиа «Протокол».

Тебе дали список новостей, связанных с Краснодарским краем.

Задача:
1. Выбери 3–5 действительно важных историй.
2. Для КАЖДОЙ выбранной истории напиши ОТДЕЛЬНЫЙ почти готовый текст для публикации.
3. Не делай дайджест.
4. Не пиши нумерованный список.
5. Не ограничивайся пересказом в одну строку.

Приоритет:
— коррупция
— силовики, суды, ФСБ, МВД, СК
— репрессии и политические дела
— протесты, митинги, пикеты, гражданские акции
— застройка, земля, побережье
— экология
— давление на активистов и журналистов
— крупные политические и бизнес-конфликты

Игнорируй:
— туризм
— спорт
— развлечения
— обычные кадровые назначения
— дорожные новости без конфликта
— проходные события

Формат КАЖДОЙ новости строго такой:

Между разными новостями обязательно ставь отдельной строкой:
---POST---

Не ставь ---POST--- в начале и в конце ответа.

**Заголовок**

Лид 1–2 предложения. В лиде естественно укажи источник: «пишет РБК», «сообщает “Коммерсант”», «по данным 93.RU» и так далее.

Основной текст. 4–8 коротких абзацев. Пиши ясно, сухо, без канцелярита, без пафоса, без списков.

Контекст:
1–3 предложения. Объясни, почему эта история важна для Краснодарского края, власти, денег, репрессий, протестов или общественного конфликта.

Запрещено:
— писать «Источник:»
— писать «Почему важно:»
— писать «Черновик»
— писать «Что проверить»
— выдумывать факты
— добавлять детали, которых нет в новости

Если данных мало, пиши осторожно: «по данным издания», «как следует из публикации».

СПИСОК НОВОСТЕЙ:
{joined}
""".strip()

    r = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return r.output_text.strip()

def main():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)

    # if not (6 <= now.hour <= 22):
#     return

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
        send("ТЕСТ РЕРАЙТА v2\n\n🗞 Новых важных новостей по Краснодарскому краю не найдено.")
        return

    try:
        text = rewrite_news(found)

        low = text.lower()
        if (not text.strip()) or ("ничего" in low and "важн" in low):
            send("ТЕСТ РЕРАЙТА v2\n\n🗞 Новых важных новостей по Краснодарскому краю не найдено.")
            save_sent([link for _, link in found[:10]])
        else:
            send_long("ТЕСТ РЕРАЙТА v2\n\n" + text)
            save_sent([link for _, link in found[:10]])

    except Exception as e:
        msg = "ТЕСТ РЕРАЙТА v2\n\n🗞 Новости по Краснодарскому краю без нейронки:\n\n"
        for i, (t, l) in enumerate(found[:10], 1):
            msg += f"{i}. {t}\n{l}\n\n"
        send(msg)
        save_sent([link for _, link in found[:10]])
        print("OPENAI ERROR:", e)

if __name__ == "__main__":
    main()
