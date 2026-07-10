from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import subqueryload, joinedload

import api.models as schema
from adapters.embeddings import SentenceTransformerClient
from api.keywords import _article_schema
from db.connection import get_session_dependency
from db.models import Article, Feed, Keyword, article_keyword

router = APIRouter()

_embed_client: SentenceTransformerClient | None = None


def _get_embed_client() -> SentenceTransformerClient:
    global _embed_client
    if _embed_client is None:
        _embed_client = SentenceTransformerClient()
    return _embed_client


def _article_options():
    return [
        subqueryload(Article.keywords),
        joinedload(Article.feed).joinedload(Feed.source),
    ]


@router.get("/search")
def search_articles(
        q: str = Query(..., min_length=1),
        limit: int = Query(default=10, ge=1, le=100),
        session=Depends(get_session_dependency),
) -> list[schema.ArticleSearchResult]:
    client = _get_embed_client()
    query_embedding = client.embed(q)

    # 1. Article content search
    article_dist = Article.embedding.cosine_distance(query_embedding).label("distance")
    content_rows = session.execute(
        select(Article, article_dist)
        .where(Article.embedding.isnot(None))
        .order_by(article_dist)
        .limit(limit)
        .options(*_article_options())
    ).all()

    # map article_id to (Article, best_distance)
    seen: dict[int, tuple[Article, float]] = {a.id: (a, d) for a, d in content_rows}

    # 2. Keyword similarity search articles linked to similar keywords
    kw_dist = Keyword.embedding.cosine_distance(query_embedding).label("kw_distance")
    similar_kw = session.execute(
        select(Keyword.id, kw_dist)
        .where(Keyword.embedding.isnot(None), ~Keyword.blocked)
        .order_by(kw_dist)
        .limit(limit)
    ).all()

    if similar_kw:
        kw_id_to_dist = {row.id: row.kw_distance for row in similar_kw}

        # Map article_id to best keyword distance
        linked_rows = session.execute(
            select(article_keyword.c.article_id, article_keyword.c.keyword_id)
            .where(article_keyword.c.keyword_id.in_(list(kw_id_to_dist)))
        ).all()

        article_best_kw_dist: dict[int, float] = {}
        for art_id, kw_id in linked_rows:
            d = kw_id_to_dist[kw_id]
            if art_id not in article_best_kw_dist or d < article_best_kw_dist[art_id]:
                article_best_kw_dist[art_id] = d

        # Update distance for articles already in results if keyword match is closer
        for art_id, d in article_best_kw_dist.items():
            if art_id in seen and d < seen[art_id][1]:
                seen[art_id] = (seen[art_id][0], d)

        # Fetch articles that only appeared via keyword match. Only the closest
        # `limit` can survive the final `[:limit]`, so cap here to avoid loading
        # every article linked to a high-degree keyword (e.g. a topic keyword).
        new_ids = sorted(
            (aid for aid in article_best_kw_dist if aid not in seen),
            key=lambda aid: article_best_kw_dist[aid],
        )[:limit]
        if new_ids:
            new_articles = session.execute(
                select(Article)
                .where(Article.id.in_(new_ids))
                .options(*_article_options())
            ).scalars().all()
            for a in new_articles:
                seen[a.id] = (a, article_best_kw_dist[a.id])

    sorted_results = sorted(seen.values(), key=lambda x: x[1])[:limit]
    return [
        schema.ArticleSearchResult(**_article_schema(a).model_dump(), distance=d)
        for a, d in sorted_results
    ]
