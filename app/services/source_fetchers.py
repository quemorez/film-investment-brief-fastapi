from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Optional
import html
import re

import feedparser
import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT = 20

NEWS_FEEDS = [
    {"name": "Variety", "url": "https://variety.com/feed/", "region": "domestic", "category": "news"},
    {"name": "Deadline", "url": "https://deadline.com/feed/", "region": "domestic", "category": "news"},
    {"name": "The Hollywood Reporter", "url": "https://www.hollywoodreporter.com/feed/", "region": "domestic", "category": "news"},
    {"name": "Screen Daily", "url": "https://www.screendaily.com/304.rss", "region": "international", "category": "news"},
    {"name": "YouTube Official Blog", "url": "https://blog.youtube/feed/", "region": "both", "category": "platform"},
]

DATA_PAGES = [
    {"name": "PwC Global Entertainment & Media Outlook", "url": "https://www.pwc.com/us/en/industries/tmt/library/global-entertainment-media-outlook.html", "region": "both"},
    {"name": "Nielsen The Gauge", "url": "https://www.nielsen.com/data-center/the-gauge/", "region": "domestic"},
    {"name": "Motion Picture Association Research", "url": "https://www.motionpictures.org/research/", "region": "domestic"},
    {"name": "YouTube Culture & Trends", "url": "https://blog.youtube/culture-and-trends/", "region": "both"},
]

@dataclass
class RawItem:
    title: str
    source: str
    url: str
    published: Optional[str]
    body: str
    region: str
    category: str

def clean_text(value: str) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value

def parse_rss_date(value: object) -> Optional[str]:
    if not value:
        return None
    try:
        if isinstance(value, str):
            return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except Exception:
        return None
    return None

def safe_get(url: str) -> Optional[requests.Response]:
    try:
        resp = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        resp.raise_for_status()
        return resp
    except Exception:
        return None

def fetch_feed_items(days: int = 7, max_per_feed: int = 15) -> List[RawItem]:
    items: List[RawItem] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for feed in NEWS_FEEDS:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries[:max_per_feed]:
            published = None
            for field in ("published", "updated"):
                published = parse_rss_date(getattr(entry, field, None))
                if published:
                    break

            if published:
                try:
                    pub_dt = datetime.fromisoformat(published)
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass

            title = clean_text(getattr(entry, "title", "") or "")
            link = getattr(entry, "link", "") or ""
            summary = clean_text(getattr(entry, "summary", "") or getattr(entry, "description", "") or "")

            if not title or not link:
                continue

            items.append(
                RawItem(
                    title=title,
                    source=feed["name"],
                    url=link,
                    published=published,
                    body=summary,
                    region=feed["region"],
                    category=feed["category"],
                )
            )
    return items

def extract_page_text(url: str) -> str:
    resp = safe_get(url)
    if not resp:
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    text = clean_text(soup.get_text(" ", strip=True))
    return text[:4000]

def fetch_data_page_items() -> List[RawItem]:
    items: List[RawItem] = []
    for page in DATA_PAGES:
        text = extract_page_text(page["url"])
        if not text:
            continue
        items.append(
            RawItem(
                title=page["name"],
                source=page["name"],
                url=page["url"],
                published=None,
                body=text,
                region=page["region"],
                category="data",
            )
        )
    return items