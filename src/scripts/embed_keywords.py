"""One-time backfill: embed all keywords that don't have an embedding yet."""
import logging

import config
from adapters.embeddings import SentenceTransformerClient
from db.connection import get_session
from db.models import Keyword

config.setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    client = SentenceTransformerClient()
    with get_session() as session:
        keywords = session.query(Keyword).filter(Keyword.embedding.is_(None)).all()
        logger.info(f"embedding {len(keywords)} keywords")
        texts = [kw.text for kw in keywords]
        embeddings = client.embed_batch(texts)
        for kw, emb in zip(keywords, embeddings):
            kw.embedding = emb
        session.commit()
        logger.info("done")
