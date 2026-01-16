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

