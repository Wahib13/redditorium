from fastapi import FastAPI, Depends, Query, HTTPException
from starlette.middleware.cors import CORSMiddleware

import config
from api.models import Article, Keyword
from db.connection import get_session_dependency
from db.models import Article as ArticleDB
from db.models import Keyword as KeywordDB

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/articles/")
def get_articles(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
        keyword_id: int = Query(default=None),
        session=Depends(get_session_dependency)
) -> list[Article]:
    query = session.query(ArticleDB)
    if keyword_id is not None:
        query = query.filter(ArticleDB.keywords.any(KeywordDB.id == keyword_id))
    return query.offset(skip).limit(limit).all()


@app.get("/keywords/")
def get_keywords(
        session=Depends(get_session_dependency)
) -> list[Keyword]:
    return session.query(KeywordDB).all()


@app.get("/keyword/{keyword_id}/")
def get_keyword(
        keyword_id: int,
        session=Depends(get_session_dependency)
) -> Keyword:
    keyword = session.query(KeywordDB).filter_by(id=keyword_id).first()
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@app.post("/keyword/{keyword_id}/block")
def block_keyword(
        keyword_id: int,
        session=Depends(get_session_dependency)
):
    keyword = session.query(KeywordDB).filter_by(id=keyword_id).first()
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    keyword.blocked = True
    session.commit()
    return {"id": keyword_id, "blocked": True}


@app.get("/article/{article_id}/")
def get_article(
        article_id: int,
        session=Depends(get_session_dependency)
) -> Article:
    article = session.query(ArticleDB).filter_by(id=article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
