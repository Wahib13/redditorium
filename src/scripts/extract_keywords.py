import config
from db.connection import get_session
from pipeline.keywords import extract_keywords

config.setup_logging()

with get_session() as session:
    extract_keywords(session)
