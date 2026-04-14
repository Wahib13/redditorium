import config
from db.connection import get_session
from pipeline.content import fetch_article_content

config.setup_logging()

with get_session() as session:
    fetch_article_content(session)
