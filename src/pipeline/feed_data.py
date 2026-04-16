import logging
from collections.abc import Awaitable, Callable

import feedparser

from db.models import Article, Source, Feed

logger = logging.getLogger(__name__)


def fetch_rss_entries(session):
    articles_to_insert = []

    for source in session.query(Source).all():
        for feed in source.feeds:
            feed_data = feedparser.parse(feed.url)
            print(feed_data.entries)
            for entry in feed_data.entries:
                url = entry.get("link")
                title = entry.get("title")

                # Simple deduplication: skip if URL already in DB
                exists = session.query(Article).filter_by(url=url).first()
                if exists:
                    continue

                article = Article(
                    url=url,
                    title=title,
                    source_topic=feed.topic.name,
                    feed=feed
                )
                articles_to_insert.append(article)

    return articles_to_insert


def save_articles(articles, session):
    session.add_all(articles)
    session.commit()
    print(f"Inserted {len(articles)} new articles")


async def stream_rss_entries(
        session,
        on_new_article: Callable[[int], Awaitable[None]],
) -> None:
    """Fetch all feeds concurrently. Calls on_new_article(article_id) for each new article saved."""
    sources = session.query(Source).all()
    for source in sources:
        for feed in source.feeds:
            await process_feed(session, feed, on_new_article)


async def process_feed(
        session,
        feed: Feed,
        on_new_article: Callable[[int], Awaitable[None]],
):
    feed_data = feedparser.parse(feed.url)
    for entry in feed_data.entries:
        url = entry.get("link")
        title = entry.get("title")
        if session.query(Article).filter_by(url=url).first():
            continue
        article = Article(url=url, title=title, source_topic=feed.topic.name, feed=feed)
        session.add(article)
        session.commit()
        logger.info(f"saved article {article.id}: {title}")
        await on_new_article(article.id)
