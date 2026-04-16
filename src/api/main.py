import datetime

from fastapi import FastAPI, Depends, Query, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import contains_eager
from starlette.middleware.cors import CORSMiddleware

import config
import api.models as schema
from db.connection import get_session_dependency
from db.models import Article, Keyword

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: dict) -> None:
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()


def _date_window(date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    start = datetime.datetime(date.year, date.month, date.day)
    return start, start + datetime.timedelta(days=1)


@app.get("/keywords/")
def get_keywords(
        date: datetime.date = Query(default=None),
        session=Depends(get_session_dependency),
) -> list[schema.KeywordWithArticles]:
    if date is None:
        date = datetime.date.today()
    start = datetime.datetime(date.year, date.month, date.day)
    end = start + datetime.timedelta(days=1)

    keywords = (
        session.query(Keyword)
        .join(Keyword.articles)
        .filter(~Keyword.blocked)
        .filter(Article.created >= start, Article.created < end)
        .options(contains_eager(Keyword.articles))
        .all()
    )
    keywords.sort(key=lambda kw: len(kw.articles), reverse=True)
    return keywords


@app.post("/keyword/{keyword_id}/block")
def block_keyword(
        keyword_id: int,
        session=Depends(get_session_dependency)
):
    keyword = session.query(Keyword).filter_by(id=keyword_id).first()
    if keyword is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    keyword.blocked = True
    session.commit()
    return {"id": keyword_id, "blocked": True}


@app.post("/internal/articles-processed")
async def articles_processed(
        body: schema.ArticlesProcessedRequest,
        session=Depends(get_session_dependency),
):
    articles = session.query(Article).filter(Article.id.in_(body.article_ids)).all()
    payload = {
        "type": "articles_added",
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "keywords": [{"id": k.id, "text": k.text} for k in a.keywords],
            }
            for a in articles
        ],
    }
    await manager.broadcast(payload)
    return {"ok": True, "count": len(articles)}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
