from __future__ import annotations

import datetime as dt
import html

import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser


def clean_description(desc_html: str | None) -> str | None:
    if not desc_html:
        return None
    desc_html = html.unescape(desc_html)
    soup = BeautifulSoup(desc_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def google_articles(
    query: str,
    max_url_length: int = 4000,
    lookback_min_date: str | None = None,
    lookback_max_date: str | None = None,
) -> list[dict]:
    query = query.replace(" ", "+")

    if lookback_min_date is None:
        lookback_min_date = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    if lookback_max_date is None:
        lookback_max_date = dt.datetime.now().strftime("%Y-%m-%d")

    url = (
        "https://news.google.com/rss/search?q="
        f"{query}&hl=en-US&gl=US&ceid=US:en,cd_min:{lookback_min_date},cd_max:{lookback_max_date}"
    )
    feed = feedparser.parse(url)

    items: list[dict] = []
    for entry in feed.entries:
        link = entry.get("link")
        if not link or len(link) > max_url_length:
            continue

        items.append(
            {
                "title": entry.get("title"),
                "link": link,
                "published": entry.get("published"),
                "description": clean_description(entry.get("description", "")),
                "source": (
                    entry.source.get("title")
                    if entry.get("source") and isinstance(entry.source, dict)
                    else None
                ),
            }
        )

    return items


def normalize_date(date_value: str) -> str:
    try:
        return parser.parse(date_value).strftime("%Y-%m-%d")
    except Exception:
        return date_value


def get_recent_articles(
    query: str,
    lookback_min_date: str | None = None,
    lookback_max_date: str | None = None,
    max_items: int = 100,
    max_url_length: int = 4000,
) -> pd.DataFrame:
    if lookback_min_date is None:
        lookback_min_date = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    if lookback_max_date is None:
        lookback_max_date = dt.datetime.now().strftime("%Y-%m-%d")

    articles = google_articles(
        query,
        max_url_length=max_url_length,
        lookback_min_date=lookback_min_date,
        lookback_max_date=lookback_max_date,
    )

    recent_articles = []
    for article in articles:
        published = article.get("published")
        if not published:
            continue
        try:
            published_dt = parser.parse(published).replace(tzinfo=None)
        except Exception:
            continue

        min_dt = dt.datetime.strptime(lookback_min_date, "%Y-%m-%d")
        max_dt = dt.datetime.strptime(lookback_max_date, "%Y-%m-%d")
        if min_dt < published_dt <= max_dt:
            article["published"] = normalize_date(published)
            recent_articles.append(article)

    recent_articles.sort(key=lambda item: item["published"], reverse=True)
    return pd.DataFrame(recent_articles[:max_items])
