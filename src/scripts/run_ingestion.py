import config
from adapters.hackernews import HackerNewsAPIClient
from ingestion import hackernews

config.setup_logging()

hackernews.fetch_stories(
    HackerNewsAPIClient(),
    limit=20
)
