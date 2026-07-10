import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import contains_eager, subqueryload, joinedload

import api.models as schema
from api.auth import get_current_user
from db.connection import get_session_dependency
from db.models import Article, Feed, Keyword, User


def _article_schema(a: Article) -> schema.Article:
    source = a.feed.source if a.feed else None
    return schema.Article(
        id=a.id,
        title=a.title,
        url=a.url,
        summary=a.summary,
        image=a.image,
        keywords=a.keywords,
        source_name=(source.display_name or source.name) if source else None,
        source_icon_url=source.icon_url if source else None,
        created=a.created,
    )

router = APIRouter()


def _date_window(date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    start = datetime.datetime(date.year, date.month, date.day)
    return start, start + datetime.timedelta(days=1)


def fetch_keywords_for_date(session, date: datetime.date) -> list[schema.KeywordWithArticles]:
    start, end = _date_window(date)
    keywords = (
        session.query(Keyword)
        .join(Keyword.articles)
        .filter(~Keyword.blocked)
        .filter(Article.created >= start, Article.created < end)
        .options(
            contains_eager(Keyword.articles).selectinload(Article.keywords),
            contains_eager(Keyword.articles).joinedload(Article.feed).joinedload(Feed.source),
        )
        .all()
    )
    result = [
        schema.KeywordWithArticles(
            id=kw.id,
            text=kw.text,
            articles=[_article_schema(a) for a in sorted(kw.articles, key=lambda a: a.created, reverse=True)],
        )
        for kw in keywords
    ]
    result.sort(key=lambda k: len(k.articles), reverse=True)
    return result


@router.get("/keywords/")
def get_keywords(
        date: datetime.date = Query(default=None),
        session=Depends(get_session_dependency),
) -> list[schema.KeywordWithArticles]:
    if date is None:
        date = datetime.date.today()
    return fetch_keywords_for_date(session, date)


@router.post("/keyword/{keyword_id}/block")
def block_keyword(
        keyword_id: int,
        session=Depends(get_session_dependency),
        current_user: User = Depends(get_current_user),
):
    keyword = session.query(Keyword).filter_by(id=keyword_id).first()
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    keyword.blocked = True
    session.commit()
    return {"id": keyword_id, "blocked": True}
