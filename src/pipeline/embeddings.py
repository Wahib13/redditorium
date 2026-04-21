import logging

import numpy as np
from sqlalchemy import insert
from sqlalchemy.orm import Session

from adapters.embeddings import SentenceTransformerClient
from db.models import Article, Config, Keyword, article_keyword

logger = logging.getLogger(__name__)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


def embed_article(article: Article, session: Session, client: SentenceTransformerClient) -> None:
    text = (article.title or "") + " " + (article.text or "")[:500]
    article.embedding = client.embed(text.strip())
    session.commit()


def classify_article_by_embedding(
    article: Article,
    session: Session,
    client: SentenceTransformerClient,
) -> int:
    config = session.get(Config, "embedding_similarity_threshold")
    threshold = float(config.value) if config else 0.3

    keywords = session.query(Keyword).filter_by(blocked=False).all()
    linked = 0

    for keyword in keywords:
        keyword_embedding = client.embed(keyword.text)
        similarity = _cosine_similarity(article.embedding, keyword_embedding)

        if similarity >= threshold:
            existing = session.execute(
                article_keyword.select().where(
                    article_keyword.c.article_id == article.id,
                    article_keyword.c.keyword_id == keyword.id,
                )
            ).first()
            if not existing:
                session.execute(
                    insert(article_keyword).values(
                        article_id=article.id,
                        keyword_id=keyword.id,
                        score=similarity,
                    )
                )
                linked += 1

    session.commit()
    return linked
