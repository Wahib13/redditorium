import datetime
from collections import defaultdict

from fastapi import FastAPI, Depends, Query, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager
from starlette.middleware.cors import CORSMiddleware

import config
import api.models as schema
from api.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_user_optional,
)
from db.connection import get_session_dependency
from db.models import Article, Keyword, KeywordMapping, User, UserKeywordRule

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


def _resolve_keywords(
        keywords: list[Keyword],
        user_mappings: list[KeywordMapping],
        admin_mappings: list[KeywordMapping],
) -> dict[str, dict]:
    """Resolve YAKE keywords through mappings. Returns {canonical_text: {id, articles}}."""
    lookup = {m.raw_keyword: m.canonical_keyword for m in admin_mappings}
    lookup.update({m.raw_keyword: m.canonical_keyword for m in user_mappings})

    groups: dict[str, dict] = {}
    for kw in keywords:
        canonical = lookup.get(kw.text, kw.text)
        if canonical not in groups:
            groups[canonical] = {"id": None, "articles": []}
        if canonical == kw.text:
            groups[canonical]["id"] = kw.id
        existing_ids = {a.id for a in groups[canonical]["articles"]}
        groups[canonical]["articles"].extend(
            a for a in kw.articles if a.id not in existing_ids
        )
    return groups


def _apply_keyword_rules(
        articles: list[Article],
        admin_rules: list[UserKeywordRule],
        user_rules: list[UserKeywordRule],
) -> dict[str, list[schema.ArticleInKeyword]]:
    """Pattern-match article titles against rules. User rules override admin rules for same pattern."""
    effective: dict[str, tuple[str, bool]] = {}  # pattern -> (keyword, case_sensitive)
    for rule in admin_rules:
        effective[rule.pattern] = (rule.keyword, rule.case_sensitive)
    for rule in user_rules:
        effective[rule.pattern] = (rule.keyword, rule.case_sensitive)

    groups: dict[str, list[schema.ArticleInKeyword]] = defaultdict(list)
    for article in articles:
        if not article.title:
            continue
        for pattern, (keyword, case_sensitive) in effective.items():
            haystack = article.title if case_sensitive else article.title.lower()
            needle = pattern if case_sensitive else pattern.lower()
            if needle in haystack:
                groups[keyword].append(
                    schema.ArticleInKeyword(id=article.id, title=article.title, url=article.url)
                )
    return dict(groups)


def _to_keyword_list(groups: dict[str, dict]) -> list[schema.KeywordWithArticles]:
    result = [
        schema.KeywordWithArticles(id=v["id"], text=text, articles=v["articles"])
        for text, v in groups.items()
    ]
    result.sort(key=lambda k: len(k.articles), reverse=True)
    return result


# --- Auth ---

@app.post("/auth/register", status_code=201)
def register(
        body: schema.UserCreate,
        session=Depends(get_session_dependency),
) -> schema.UserRead:
    if session.query(User).filter_by(email=body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/auth/login")
def login(
        form: OAuth2PasswordRequestForm = Depends(),
        session=Depends(get_session_dependency),
) -> schema.TokenResponse:
    user = session.query(User).filter_by(email=form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return schema.TokenResponse(access_token=create_access_token(user.id))


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)) -> schema.UserRead:
    return current_user


# --- Keywords ---

@app.get("/keywords/")
def get_keywords(
        date: datetime.date = Query(default=None),
        session=Depends(get_session_dependency),
        current_user: User | None = Depends(get_current_user_optional),
) -> list[schema.KeywordWithArticles]:
    if date is None:
        date = datetime.date.today()
    start, end = _date_window(date)

    keywords = (
        session.query(Keyword)
        .join(Keyword.articles)
        .filter(~Keyword.blocked)
        .filter(Article.created >= start, Article.created < end)
        .options(contains_eager(Keyword.articles))
        .all()
    )

    raw_texts = [kw.text for kw in keywords]
    admin_mappings = (
        session.query(KeywordMapping)
        .join(User, User.id == KeywordMapping.user_id)
        .filter(KeywordMapping.raw_keyword.in_(raw_texts))
        .filter(User.admin.is_(True))
        .all()
    )
    user_mappings = []
    if current_user and not current_user.admin:
        user_mappings = (
            session.query(KeywordMapping)
            .filter(KeywordMapping.raw_keyword.in_(raw_texts))
            .filter(KeywordMapping.user_id == current_user.id)
            .all()
        )

    all_articles = (
        session.query(Article)
        .filter(Article.created >= start, Article.created < end)
        .all()
    )
    admin_rules = (
        session.query(UserKeywordRule)
        .join(User, User.id == UserKeywordRule.user_id)
        .filter(User.admin.is_(True))
        .all()
    )
    user_rules = []
    if current_user and not current_user.admin:
        user_rules = (
            session.query(UserKeywordRule)
            .filter(UserKeywordRule.user_id == current_user.id)
            .all()
        )

    groups = _resolve_keywords(keywords, user_mappings, admin_mappings)
    rule_groups = _apply_keyword_rules(all_articles, admin_rules, user_rules)

    for text, rule_articles in rule_groups.items():
        if text not in groups:
            groups[text] = {"id": None, "articles": []}
        existing_ids = {a.id for a in groups[text]["articles"]}
        groups[text]["articles"].extend(a for a in rule_articles if a.id not in existing_ids)

    return _to_keyword_list(groups)


@app.post("/keyword/{keyword_id}/block")
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


# --- Keyword mappings ---

@app.get("/keyword-mappings/")
def get_keyword_mappings(
        session=Depends(get_session_dependency),
        current_user: User = Depends(get_current_user),
) -> list[schema.KeywordMappingRead]:
    return (
        session.query(KeywordMapping)
        .filter(KeywordMapping.user_id == current_user.id)
        .all()
    )


@app.post("/keyword-mappings/", status_code=201)
def create_keyword_mapping(
        body: schema.KeywordMappingCreate,
        session=Depends(get_session_dependency),
        current_user: User = Depends(get_current_user),
) -> schema.KeywordMappingRead:
    mapping = KeywordMapping(
        raw_keyword=body.raw_keyword,
        canonical_keyword=body.canonical_keyword,
        user_id=current_user.id,
    )
    session.add(mapping)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A mapping for '{body.raw_keyword} to {body.canonical_keyword}' already exists for this user",
        )
    session.refresh(mapping)
    return mapping


@app.delete("/keyword-mapping/{mapping_id}", status_code=204)
def delete_keyword_mapping(
        mapping_id: int,
        session=Depends(get_session_dependency),
        current_user: User = Depends(get_current_user),
):
    mapping = session.query(KeywordMapping).filter_by(id=mapping_id).first()
    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    if mapping.user_id != current_user.id and not current_user.admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    session.delete(mapping)
    session.commit()


# --- Keyword rules ---

@app.get("/keyword-rules/")
def get_keyword_rules(
        session=Depends(get_session_dependency),
        current_user: User = Depends(get_current_user),
) -> list[schema.UserKeywordRuleRead]:
    return session.query(UserKeywordRule).filter_by(user_id=current_user.id).all()


@app.post("/keyword-rules/", status_code=201)
def create_keyword_rule(
        body: schema.UserKeywordRuleCreate,
        session=Depends(get_session_dependency),
        current_user: User = Depends(get_current_user),
) -> schema.UserKeywordRuleRead:
    rule = UserKeywordRule(
        pattern=body.pattern,
        keyword=body.keyword,
        case_sensitive=body.case_sensitive,
        user_id=current_user.id,
    )
    session.add(rule)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A rule for pattern '{body.pattern}' already exists for this user",
        )
    session.refresh(rule)
    return rule


@app.delete("/keyword-rule/{rule_id}", status_code=204)
def delete_keyword_rule(
        rule_id: int,
        session=Depends(get_session_dependency),
        current_user: User = Depends(get_current_user),
):
    rule = session.query(UserKeywordRule).filter_by(id=rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    if rule.user_id != current_user.id and not current_user.admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    session.delete(rule)
    session.commit()


# --- Internal / WebSocket ---

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
