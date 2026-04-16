import argparse
import asyncio
import logging

import httpx

import config
from db.connection import get_session
from db.models import Article
from pipeline.feed_data import stream_rss_entries
from pipeline.keywords import extract_keywords_for_article

config.setup_logging()

logger = logging.getLogger(__name__)


def _run_for_article(article_id: int) -> int:
    """Thread worker. Creates its own session — session management lives here, not in the pipeline module."""
    with get_session() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return 0
        return extract_keywords_for_article(article, session)


def _notify_api(api_base: str, article_ids: list[int]) -> None:
    """Notify the API of all processed articles in one request. Best-effort — API may not be running."""
    try:
        httpx.post(
            f"{api_base}/internal/articles-processed",
            json={"article_ids": article_ids},
            timeout=5,
        )
    except Exception as exc:
        logger.warning(f"could not notify API: {exc}")


async def keyword_worker(queue: asyncio.Queue, processed: list[int]) -> None:
    while True:
        article_id = await queue.get()
        await asyncio.to_thread(_run_for_article, article_id)
        processed.append(article_id)
        queue.task_done()


async def main(api_base: str) -> None:
    queue = asyncio.Queue()
    processed: list[int] = []
    with get_session() as session:
        worker = asyncio.create_task(keyword_worker(queue, processed))
        await stream_rss_entries(session, on_new_article=queue.put)
        await queue.join()
        worker.cancel()
    if processed:
        await asyncio.to_thread(_notify_api, api_base, processed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", required=True, help="Base URL of the API (e.g. http://localhost:8081)")
    args = parser.parse_args()
    asyncio.run(main(args.api_base))
