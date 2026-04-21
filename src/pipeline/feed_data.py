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


def save_new_article(
        session, feed: Feed, url: str, title: str | None, summary: str | None = None
) -> "Article | None":
    """Persist a new article if the URL hasn't been seen. Returns saved Article or None if duplicate."""
    if session.query(Article).filter_by(url=url).first():
        return None
    article = Article(url=url, title=title, summary=summary, source_topic=feed.topic.name, feed=feed)
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
    for entry in feed_data.entries:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue
        summary = _extract_summary(entry)
        article = save_new_article(session, feed, url, title, summary)
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
        for feed in source.feeds:
            await process_feed(session, feed, on_new_article, parse_fn)
