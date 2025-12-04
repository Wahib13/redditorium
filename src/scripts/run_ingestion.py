import config
from adapters.hackernews import HackerNewsAPIClient
from db.connection import get_session
from ingestion import hackernews

config.setup_logging()

with get_session() as session:
    hackernews.fetch_stories(
        HackerNewsAPIClient(),
        session,
    )
