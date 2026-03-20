from __future__ import annotations

import datetime as dt
import html
from typing import Optional
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser
from tagging import tag_articles


def clean_description(desc_html: Optional[str]) -> Optional[str]:
    if not desc_html:
        return None
    desc_html = html.unescape(desc_html)
    soup = BeautifulSoup(desc_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def google_articles(
    query: str,
    max_url_length: int = 4000,
    lookback_min_date: Optional[str] = None,
    lookback_max_date: Optional[str] = None,
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

    items = []
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
    lookbackMinDate: Optional[str] = None,
    lookbackMaxDate: Optional[str] = None,
    max_items: int = 100,
    max_url_length: int = 4000,
) -> pd.DataFrame:
    if lookbackMinDate is None:
        lookbackMinDate = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    if lookbackMaxDate is None:
        lookbackMaxDate = dt.datetime.now().strftime("%Y-%m-%d")

    articles = google_articles(
        query,
        max_url_length=max_url_length,
        lookback_min_date=lookbackMinDate,
        lookback_max_date=lookbackMaxDate,
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

        min_dt = dt.datetime.strptime(lookbackMinDate, "%Y-%m-%d")
        max_dt = dt.datetime.strptime(lookbackMaxDate, "%Y-%m-%d")
        if min_dt < published_dt <= max_dt:
            article["published"] = normalize_date(published)
            recent_articles.append(article)

    recent_articles.sort(key=lambda item: item["published"], reverse=True)
    return pd.DataFrame(recent_articles[:max_items])


def func_tagging(
    df: Optional[pd.DataFrame] = None,
    useTags: bool = True,
    tagType: str = "research",
    tag_profile: Optional[str] = None,
    tag_adds: Optional[pd.DataFrame] = None,
    lookbackMin=None,
    lookbackMax=None,
) -> pd.DataFrame:
    if df is None:
        raise ValueError("Local-only mode requires a dataframe input.")
    if not useTags or tag_adds is None:
        raise ValueError("Local-only mode requires a tag reference dataframe via tag_adds.")
    if tag_profile is not None:
        print(f"Ignoring tag_profile '{tag_profile}' in local-only mode.")
    if lookbackMin is not None or lookbackMax is not None:
        print("Ignoring lookback parameters in func_tagging because the caller already provides the dataframe.")

    return tag_articles(df=df, tag_ref=tag_adds, tag_type=tagType)
