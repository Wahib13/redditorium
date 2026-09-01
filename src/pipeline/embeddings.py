import logging

from sqlalchemy.orm import Session

from adapters.embeddings import SentenceTransformerClient
from db.models import Article

logger = logging.getLogger(__name__)


def _article_text(article: Article) -> str:
    return ((article.title or "") + " " + (article.text or "")[:500]).strip()


def embed_article(article: Article, session: Session, client: SentenceTransformerClient) -> None:
    article.embedding = client.embed(_article_text(article))
    session.commit()


def embed_articles_batch(
        articles: list[Article],
        client: SentenceTransformerClient,
        batch_size: int = 64,
) -> int:
    """Embed many articles with batched model calls.

    Sets ``Article.embedding`` in place using one ``embed_batch`` call per chunk
    of ``batch_size``. Articles with no title or text are skipped. Does not
    commit — the caller owns the transaction. Returns how many were embedded.
    """
    candidates = [a for a in articles if a.title or a.text]
    if not candidates:
        return 0

    embedded = 0
    for start in range(0, len(candidates), batch_size):
        chunk = candidates[start:start + batch_size]
        embeddings = client.embed_batch([_article_text(a) for a in chunk])
        for article, embedding in zip(chunk, embeddings):
            article.embedding = embedding
        embedded += len(chunk)
    return embedded
