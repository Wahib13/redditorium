from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import subqueryload, joinedload

import api.models as schema
from adapters.embeddings import SentenceTransformerClient
from api.keywords import _article_schema
from db.connection import get_session_dependency
from db.models import Article, Feed, Source

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
        .options(
            subqueryload(Article.keywords),
            joinedload(Article.feed).joinedload(Feed.source),
        )
    ).all()

    return [
        schema.ArticleSearchResult(**_article_schema(article).model_dump(), distance=distance)
        for article, distance in rows
    ]
