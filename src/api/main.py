from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware

import config
import api.models as schema
from api.auth import router as auth_router
from api.keywords import router as keywords_router
from db.connection import get_session_dependency
from db.models import Article
from fastapi import Depends

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(keywords_router)


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
