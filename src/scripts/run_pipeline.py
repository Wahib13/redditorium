import asyncio

import config
from db.connection import get_session
from db.models import Article
from pipeline.feed_data import stream_rss_entries
from pipeline.keywords import extract_keywords_for_article

config.setup_logging()


def _run_for_article(article_id: int) -> int:
    """Thread worker. Creates its own session — session management lives here, not in the pipeline module."""
    with get_session() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return 0
        return extract_keywords_for_article(article, session)


async def keyword_worker(queue: asyncio.Queue) -> None:
    while True:
        article_id = await queue.get()
        await asyncio.to_thread(_run_for_article, article_id)
        queue.task_done()


async def main() -> None:
    queue = asyncio.Queue()
    with get_session() as session:
        worker = asyncio.create_task(keyword_worker(queue))
        await stream_rss_entries(session, on_new_article=queue.put)
        await queue.join()
        worker.cancel()


asyncio.run(main())
