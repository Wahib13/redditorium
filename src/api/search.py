from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

import api.models as schema
from adapters.embeddings import SentenceTransformerClient
from db.connection import get_session_dependency
from db.models import Article

router = APIRouter()

_embed_client: SentenceTransformerClient | None = None


def _get_embed_client() -> SentenceTransformerClient:
    global _embed_client
    if _embed_client is None:
        _embed_client = SentenceTransformerClient()
    return _embed_client


@router.get("/search")
def search_articles(
        q: str = Query(..., min_length=1),
        limit: int = Query(default=10, ge=1, le=100),
        session=Depends(get_session_dependency),
) -> list[schema.ArticleSearchResult]:
    client = _get_embed_client()
    query_embedding = client.embed(q)
    distance_col = Article.embedding.cosine_distance(query_embedding).label("distance")

    rows = session.execute(
        select(Article, distance_col)
        .where(Article.embedding.isnot(None))
        .order_by(distance_col)
        .limit(limit)
    ).all()

    return [
        schema.ArticleSearchResult(
            id=article.id,
            title=article.title,
            url=article.url,
            summary=article.summary,
            distance=distance,
        )
        for article, distance in rows
    ]
