import logging

from keybert import KeyBERT
from sqlalchemy.orm import Session

from db.models import Article, Keyword, article_keyword

logger = logging.getLogger(__name__)


def link_keywords(
        session: Session,
        article: Article,
        raw_keywords: list[tuple[str, float | None]],
) -> int:
    """Apply pre-extracted keywords to an article. Returns number of keywords linked."""
    linked = 0
    for kw_text, score in raw_keywords:
        normalized = kw_text.lower().strip()
        if not normalized:
            continue

        existing_kw = session.query(Keyword).filter_by(text=normalized).first()
        if existing_kw and existing_kw.blocked:
            continue

        keyword = existing_kw or Keyword(text=normalized)
        if not existing_kw:
            session.add(keyword)
            session.flush()

        already_linked = session.execute(
            article_keyword.select().where(
                article_keyword.c.article_id == article.id,
                article_keyword.c.keyword_id == keyword.id,
            )
        ).first()
        if already_linked:
            continue

        session.execute(
            article_keyword.insert().values(
                article_id=article.id,
                keyword_id=keyword.id,
                score=score,
            )
        )
        linked += 1

    session.commit()
    return linked


def extract_keywords_keybert(article: Article, session: Session, kw_model: KeyBERT) -> int:
    """Extract keywords from article title using KeyBERT, always including the feed topic."""
    topic_name = article.feed.topic.name if article.feed and article.feed.topic else None
    keywords: list[tuple[str, float | None]] = [(topic_name, None)] if topic_name else []

    title = article.title or ""
    if len(title.split()) >= 4:
        keywords += kw_model.extract_keywords(title, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=5)

    return link_keywords(session, article, keywords)
