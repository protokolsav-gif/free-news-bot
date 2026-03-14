import os
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
    # общий поток по региону
    "https://news.google.com/rss/search?q=(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик+OR+Анапа+OR+Туапсе+OR+Армавир+OR+Ейск+OR+Сириус)+when:3d&hl=ru&gl=RU&ceid=RU:ru",

    # РБК
    "https://news.google.com/rss/search?q=site:rbc.ru+(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик+OR+Анапа)+when:14d&hl=ru&gl=RU&ceid=RU:ru",

    # Коммерсант
    "https://news.google.com/rss/search?q=site:kommersant.ru+(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик+OR+Анапа)+when:14d&hl=ru&gl=RU&ceid=RU:ru",

    # Медуза
    "https://news.google.com/rss/search?q=site:meduza.io+(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик)+when:30d&hl=ru&gl=RU&ceid=RU:ru",

    # The Insider
    "https://news.google.com/rss/search?q=site:theins.ru+(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик)+when:30d&hl=ru&gl=RU&ceid=RU:ru",

    # Агентство
    "https://news.google.com/rss/search?q=site:agents.media+(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик)+when:30d&hl=ru&gl=RU&ceid=RU:ru",

    # Проект
    "https://news.google.com/rss/search?q=site:proekt.media+(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик)+when:30d&hl=ru&gl=RU&ceid=RU:ru",

    # 7x7
    "https://news.google.com/rss/search?q=site:7x7-journal.ru+(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск+OR+Геленджик)+when:30d&hl=ru&gl=RU&ceid=RU:ru",

    # коррупция / силовики / репрессии
    "https://news.google.com/rss/search?q=(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар)+(%D0%BA%D0%BE%D1%80%D1%80%D1%83%D0%BF%D1%86%D0%B8%D1%8F+OR+%D1%84%D1%81%D0%B1+OR+%D0%BC%D0%B2%D0%B4+OR+%D1%81%D0%BA+OR+%D0%B0%D1%80%D0%B5%D1%81%D1%82+OR+%D0%BE%D0%B1%D1%8B%D1%81%D0%BA+OR+%D1%81%D1%83%D0%B4+OR+%D1%83%D0%B3%D0%BE%D0%BB%D0%BE%D0%B2%D0%BD%D0%BE%D0%B5+%D0%B4%D0%B5%D0%BB%D0%BE)+when:14d&hl=ru&gl=RU&ceid=RU:ru",

    # протесты / активизм
    "https://news.google.com/rss/search?q=(%22Краснодарский+край%22+OR+Кубань+OR+Краснодар+OR+Сочи+OR+Новороссийск)+(%D0%BF%D1%80%D0%BE%D1%82%D0%B5%D1%81%D1%82+OR+%D0%BC%D0%B8%D1%82%D0%B8%D0%BD%D0%B3+OR+%D0%BF%D0%B8%D0%BA%D0%B5%D1%82+OR+%D0%B0%D0%BA%D1%86%D0%B8%D1%8F+OR+%D0%B7%D0%B0%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D0%BB%D0%B8+OR+%D0%B0%D0%BA%D1%82%D0%B8%D0%B2%D0%B8%D1%81%D1%82)+when:14d&hl=ru&gl=RU&ceid=RU:ru",

    # застройка / земля / экология
    "https://news.google.com/rss/search?q=(%D0%A1%D0%BE%D1%87%D0%B8+OR+%D0%93%D0%B5%D0%BB%D0%B5%D0%BD%D0%B4%D0%B6%D0%B8%D0%BA+OR+%D0%9D%D0%BE%D0%B2%D0%BE%D1%80%D0%BE%D1%81%D1%81%D0%B8%D0%B9%D1%81%D0%BA+OR+%D0%90%D0%BD%D0%B0%D0%BF%D0%B0+OR+%D0%9A%D1%80%D0%B0%D1%81%D0%BD%D0%BE%D0%B4%D0%B0%D1%80)+(%D0%B7%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0+OR+%D0%B7%D0%B5%D0%BC%D0%BB%D1%8F+OR+%D1%8D%D0%BA%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%8F+OR+%D1%81%D0%B2%D0%B0%D0%BB%D0%BA%D0%B0+OR+%D0%B2%D1%8B%D1%80%D1%83%D0%B1%D0%BA%D0%B0+OR+%D0%BF%D0%BE%D0%B1%D0%B5%D1%80%D0%B5%D0%B6%D1%8C%D0%B5)+when:14d&hl=ru&gl=RU&ceid=RU:ru",

    # политика / губернатор / депутаты
    "https://news.google.com/rss/search?q=(%22%D0%9A%D1%80%D0%B0%D1%81%D0%BD%D0%BE%D0%B4%D0%B0%D1%80%D1%81%D0%BA%D0%B8%D0%B9+%D0%BA%D1%80%D0%B0%D0%B9%22+OR+%D0%9A%D1%83%D0%B1%D0%B0%D0%BD%D1%8C+OR+%D0%9A%D1%80%D0%B0%D1%81%D0%BD%D0%BE%D0%B4%D0%B0%D1%80)+(%D0%B3%D1%83%D0%B1%D0%B5%D1%80%D0%BD%D0%B0%D1%82%D0%BE%D1%80+OR+%D0%9A%D0%BE%D0%BD%D0%B4%D1%80%D0%B0%D1%82%D1%8C%D0%B5%D0%B2+OR+%D0%B4%D0%B5%D0%BF%D1%83%D1%82%D0%B0%D1%82+OR+%D0%BC%D1%8D%D1%80+OR+%D0%B0%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%86%D0%B8%D1%8F)+when:14d&hl=ru&gl=RU&ceid=RU:ru",
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


def is_junk(title):
    low = title.lower()

    junk_words = [
        "погода",
        "синоптик",
        "штормовое предупреждение",
        "туризм",
        "турист",
        "пляж",
        "курортный сезон",
        "открыли сезон",
        "афиша",
        "концерт",
        "фестиваль",
        "матч",
        "спорт",
        "футбол",
        "хоккей",
        "дтп",
        "авария без пострадавших",
        "гороскоп",
        "рецепт",
        "шоу",
        "звезда",
    ]

    return any(word in low for word in junk_words)


def pick_top(items):
    items = items[:50]

    joined = "\n".join(
        [f"{i+1}. {title}\n{link}" for i, (title, link) in enumerate(items)]
    )

    prompt = f"""
Ты редактор независимого общественно-политического издания «Протокол».

Тебе дали список новостей, связанных с Краснодарским краем.

Нужно выбрать 5 самых важных новостей.

Приоритет тем:
1. коррупция чиновников
2. имущество и бизнес элит
3. силовые структуры (ФСБ, МВД, СК)
4. репрессии и политические дела
5. протесты, митинги, пикеты, гражданские акции
6. региональная политика
7. застройка и земельные конфликты
8. экология
9. давление на активистов и журналистов
10. крупные бизнес-конфликты и лоббизм

Игнорируй:
- ДТП
- бытовые происшествия
- туризм
- развлечения
- курортную ерунду
- спорт
- мелкие новости без общественного значения

Пиши:
- сухо
- нейтрально
- коротко
- без пафоса

Формат ответа:
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

            if is_junk(title):
                continue

            if link in sent:
                continue

            found.append((title, link))

    # убираем дубли
    unique = []
    seen_links = set()
    for title, link in found:
        if link in seen_links:
            continue
        seen_links.add(link)
        unique.append((title, link))

    if not unique:
        send("🗞 Новых важных новостей по Краснодарскому краю не найдено.")
        return

    try:
        text = pick_top(unique)

        low = text.lower()
        if (not text.strip()) or ("ничего" in low and "важн" in low):
            msg = "🗞 Новые новости по Краснодарскому краю:\n\n"
            for i, (t, l) in enumerate(unique[:10], 1):
                msg += f"{i}. {t}\n{l}\n\n"
            send(msg)
            save_sent([link for _, link in unique[:10]])
        else:
            send("🗞 Важное по Краснодарскому краю:\n\n" + text)
            save_sent([link for _, link in unique[:10]])

    except Exception as e:
        msg = "🗞 Новости по Краснодарскому краю (без нейронки):\n\n"
        for i, (t, l) in enumerate(unique[:10], 1):
            msg += f"{i}. {t}\n{l}\n\n"
        send(msg)
        save_sent([link for _, link in unique[:10]])
        print("OPENAI ERROR:", e)


if __name__ == "__main__":
    main()
