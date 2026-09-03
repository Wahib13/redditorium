import argparse
import asyncio
import logging
import time

import httpx
from keybert import KeyBERT

import config
from adapters.embeddings import SentenceTransformerClient
from db.connection import get_session
from db.models import Article, Feed, Source
from pipeline.embeddings import embed_articles_batch
from pipeline.feed_data import collect_feed_articles
from pipeline.keywords import extract_keywords_batch, link_topic_keywords

config.setup_logging()
logger = logging.getLogger(__name__)

_client: SentenceTransformerClient | None = None
_kw_model: KeyBERT | None = None


def _notify_api(api_base: str) -> None:
    """Notify the API that articles were processed. Best-effort as API may not be running."""
    try:
        httpx.post(f"{api_base}/internal/articles-processed", timeout=5)
    except Exception as exc:
        logger.warning(f"could not notify API: {exc}")


async def main(api_base: str) -> None:
    """fetch articles from each feed and insert them once"""
    started = time.monotonic()

    with get_session() as session:
        feeds: list[Feed] = [feed for source in session.query(Source).all() for feed in source.feeds]

        seen_urls: set[str] = {url for (url,) in session.query(Article.url).all()}

        feed_awaitables = [collect_feed_articles(feed, seen_urls) for feed in feeds]

        batches = await asyncio.gather(
            *feed_awaitables
        )

        new_articles = [
            article
            for batch in batches
            for article in batch
        ]

        session.add_all(new_articles)
        session.flush()
        linked = link_topic_keywords(session, new_articles)

        extracted = 0
        embedded = 0
        if new_articles:
            embed_client = SentenceTransformerClient()
            kw_model = KeyBERT(model=embed_client.model)
            extracted = extract_keywords_batch(session, new_articles, kw_model, embed_client)
            embedded = embed_articles_batch(new_articles, embed_client)

        session.commit()

    elapsed = time.monotonic() - started
    logger.info(
        f"inserted {len(new_articles)} new articles, linked {linked} topic keywords, "
        f"extracted {extracted} keyword links, embedded {embedded} articles in {elapsed:.2f}s"
    )

    _notify_api(api_base)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", required=True, help="Base URL of the API (e.g. http://localhost:8081)")
    args = parser.parse_args()
    asyncio.run(main(args.api_base))
