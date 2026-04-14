import config
from db.connection import get_session
from pipeline.feed_data import fetch_rss_entries, save_articles

config.setup_logging()

with get_session() as session:
    new_articles = fetch_rss_entries(session)
    save_articles(new_articles, session)
