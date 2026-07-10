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


def save_new_article(
        session, feed: Feed, url: str, title: str | None, summary: str | None = None,
        image: str | None = None, published: datetime.datetime | None = None,
) -> "Article | None":
    """Persist a new article if the URL hasn't been seen. Returns saved Article or None if duplicate."""
    if session.query(Article).filter_by(url=url).first():
        return None
    article = Article(
        url=url, title=title, summary=summary, image=image,
        source_topic=feed.topic.name, feed=feed,
        created=published or datetime.datetime.utcnow(),
    )
    session.add(article)
    session.commit()
    logger.info(f"saved article {article.id}: {title}")
    return article


async def process_feed(
        session,
        feed: Feed,
        on_new_article: Callable[[int], Awaitable[None]],
        parse_fn: Callable[[str], Any] = feedparser.parse,
) -> None:
    feed_data = parse_fn(feed.url)
    print(f"number of entries found: {len(feed_data.entries)}")
    for entry in feed_data.entries:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue
        summary = _extract_summary(entry)
        image = _extract_image(entry)
        published = _extract_published(entry)
        article = save_new_article(session, feed, url, title, summary, image, published)
        if article:
            await on_new_article(article.id)


async def stream_rss_entries(
        session,
        on_new_article: Callable[[int], Awaitable[None]],
        parse_fn: Callable[[str], Any] = feedparser.parse,
) -> None:
    """Fetch all feeds. Calls on_new_article(article_id) for each new article saved."""
    sources = session.query(Source).all()
    for source in sources:
        print(f"running for source: {source.id}: {source.name}")
        for feed in source.feeds:
            print(f"running for feed in: {source.name} - {feed.url}")
            await process_feed(session, feed, on_new_article, parse_fn)
