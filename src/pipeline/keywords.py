import logging

import spacy
from sqlalchemy.orm import Session

from db.models import Article, Keyword, article_keyword

logger = logging.getLogger(__name__)

_nlp = spacy.load("en_core_web_sm")
_ENTITY_LABELS = {"PERSON", "ORG", "GPE", "LOC", "EVENT", "PRODUCT", "WORK_OF_ART", "NORP", "FAC", "LAW"}


def link_keywords(
        session: Session,
        article: Article,
        raw_keywords: list[tuple[str, float | None]],
) -> int:
    """Apply pre-extracted keywords to an article. Returns number of keywords linked."""
    linked = 0
    for kw_text, score in raw_keywords:
        normalized = kw_text.lower().strip()

        existing = session.query(Keyword).filter_by(text=normalized).first()
        if existing and existing.blocked:
            continue

        keyword = existing or Keyword(text=normalized)
        if not existing:
            session.add(keyword)
            session.flush()

        try:
            session.execute(
                article_keyword.insert().values(
                    article_id=article.id,
                    keyword_id=keyword.id,
                    score=score,
                )
            )
            linked += 1

            session.commit()
        except Exception as e:
            logger.exception(f"failed to link keyword: {keyword.id}:{keyword.text} to {article.id}:{article.title}")
    return linked


def extract_keywords_for_article(
        article: Article,
        session: Session,
) -> int:
    """Extract and link keywords for a single article. Returns number of keywords linked."""
    text = article.title or ""
    if not text.strip() and article.text:
        text = article.text[:500]
    doc = _nlp(text)
    raw_keywords = [
        (ent.text, None)
        for ent in doc.ents
        if ent.label_ in _ENTITY_LABELS
    ]
    return link_keywords(session, article, raw_keywords)


def extract_keywords(session: Session) -> None:
    """Batch extraction for all articles that have a title but no keywords yet."""
    articles = (
        session.query(Article)
        .filter(Article.title.isnot(None))
        .filter(~Article.keywords.any())
        .all()
    )

    logger.info(f"found {len(articles)} articles to process")
    total_linked = total_skipped_blocked = 0

    for article in articles:
        linked = extract_keywords_for_article(article, session)
        total_linked += linked

    logger.info(
        f"done — {total_linked} keyword links created, "
        f"{total_skipped_blocked} skipped by DB block flag"
    )
