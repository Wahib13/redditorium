import asyncio
import datetime
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import feedparser

from db.models import Article, Source, Feed

logger = logging.getLogger(__name__)


def _extract_summary(entry: Any) -> str | None:
    value = entry.get("summary_detail")
    if not value:
        return None
    text = value.get("value") if isinstance(value, dict) else value
    return text.strip()


def _extract_published(entry: Any) -> datetime.datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.datetime(*parsed[:6])


def _extract_image(entry: Any) -> str | None:
    thumbnails = entry.get("media_thumbnail")
    if thumbnails:
        url = thumbnails[0].get("url") if isinstance(thumbnails[0], dict) else None
        if url:
            return url

    for item in entry.get("media_content", []):
        if isinstance(item, dict):
            medium = item.get("medium", "")
            mime = item.get("type", "")
            if medium == "image" or mime.startswith("image/"):
                url = item.get("url")
                if url:
                    return url

    for enc in entry.get("enclosures", []):
        if isinstance(enc, dict) and enc.get("type", "").startswith("image/"):
            url = enc.get("url") or enc.get("href")
            if url:
                return url

    return None


def _build_article(feed: Feed, entry: Any) -> "Article | None":
    """Turn a feedparser entry into an unsaved Article, or None if it lacks a url/title."""
    url = entry.get("link")
    title = entry.get("title")
    if not url or not title:
        return None
    return Article(
        url=url,
        title=title,
        summary=_extract_summary(entry),
        image=_extract_image(entry),
        source_topic=feed.topic.name,
        feed=feed,
        created=_extract_published(entry) or datetime.datetime.utcnow(),
    )


async def collect_feed_articles(
        feed: Feed,
        seen_urls: set[str],
        parse_fn: Callable[[str], Any] = feedparser.parse,
) -> list["Article"]:
    """Parse a feed and return unsaved Articles for URLs not already in seen_urls.

    Does not touch the session; dedup against seen_urls is caller-managed so a
    single run can catch the same story appearing across feeds. Mutates seen_urls.
    """
    feed_data = await asyncio.to_thread(parse_fn, feed.url)
    logger.info(f"number of entries found: {len(feed_data.entries)}")
    articles: list[Article] = []
    for entry in feed_data.entries:
        url = entry.get("link")
        if not url or url in seen_urls:
            continue
        article = _build_article(feed, entry)
        if article is None:
            continue
        seen_urls.add(url)
        articles.append(article)
    return articles
