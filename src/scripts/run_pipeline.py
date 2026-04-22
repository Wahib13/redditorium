import argparse
import asyncio
import logging

import httpx
from keybert import KeyBERT

import config
from adapters.embeddings import SentenceTransformerClient
from db.connection import get_session
from db.models import Article
from pipeline.embeddings import embed_article
from pipeline.feed_data import stream_rss_entries
from pipeline.keywords import extract_keywords_keybert

config.setup_logging()
logger = logging.getLogger(__name__)

_client: SentenceTransformerClient | None = None
_kw_model: KeyBERT | None = None


def _run_for_article(article_id: int) -> int:
    """Thread worker. Creates its own session."""
    with get_session() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return 0
        embed_article(article, session, _client)
        return extract_keywords_keybert(article, session, _kw_model)


def _notify_api(api_base: str) -> None:
    """Notify the API that an article was processed. Best-effort as API may not be running."""
    try:
        httpx.post(f"{api_base}/internal/articles-processed", timeout=5)
    except Exception as exc:
        logger.warning(f"could not notify API: {exc}")


async def keyword_worker(queue: asyncio.Queue, api_base: str) -> None:
    while True:
        article_id = await queue.get()
        await asyncio.to_thread(_run_for_article, article_id)
        await asyncio.to_thread(_notify_api, api_base)
        queue.task_done()


async def main(api_base: str) -> None:
    global _client, _kw_model
    _client = SentenceTransformerClient()
    _kw_model = KeyBERT(model=_client.model)

    queue = asyncio.Queue()
    with get_session() as session:
        worker = asyncio.create_task(keyword_worker(queue, api_base))
        await stream_rss_entries(session, on_new_article=queue.put)
        await queue.join()
        worker.cancel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", required=True, help="Base URL of the API (e.g. http://localhost:8081)")
    args = parser.parse_args()
    asyncio.run(main(args.api_base))
