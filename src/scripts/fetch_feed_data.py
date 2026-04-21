import asyncio

import config
from db.connection import get_session
from db.models import Source
from pipeline.feed_data import process_feed

config.setup_logging()

async def on_insert(id_: int):
    ...

async def run():
    with get_session() as session:
        sources = session.query(Source).all()
        for source in sources:
            for feed in source.feeds:
                await process_feed(session, feed, on_insert)

if __name__ == "__main__":
    asyncio.run(run())
