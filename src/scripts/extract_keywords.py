import logging

from keybert import KeyBERT

import config
from adapters.embeddings import SentenceTransformerClient
from db.connection import get_session
from db.models import Article
from pipeline.embeddings import embed_article
from pipeline.keywords import extract_keywords_keybert

config.setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    client = SentenceTransformerClient()
    kw_model = KeyBERT(model=client.model)

    with get_session() as session:
        articles = (
            session.query(Article)
            .filter(Article.title.isnot(None))
            .filter(Article.embedding.is_(None))
            .all()
        )

        logger.info(f"found {len(articles)} articles to embed and extract keywords")
        total_linked = 0

        for article in articles:
            embed_article(article, session, client)
            linked = extract_keywords_keybert(article, session, kw_model)
            total_linked += linked

        logger.info(f"done — {total_linked} keyword links created")
