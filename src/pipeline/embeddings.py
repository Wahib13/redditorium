import logging

from sqlalchemy.orm import Session

from adapters.embeddings import SentenceTransformerClient
from db.models import Article

logger = logging.getLogger(__name__)


def embed_article(article: Article, session: Session, client: SentenceTransformerClient) -> None:
    text = (article.title or "") + " " + (article.text or "")[:500]
    article.embedding = client.embed(text.strip())
    session.commit()
