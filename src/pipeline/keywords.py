import logging

import nltk
import yake

nltk.download('stopwords', quiet=True)
from sqlalchemy.orm import Session

from db.models import Article, Keyword, article_keyword

logger = logging.getLogger(__name__)


def extract_keywords_for_article(
        article: Article,
        session: Session,
) -> int:
    """Extract and link keywords for a single article. Returns number of keywords linked."""
    nltk_stopwords = set(nltk.corpus.stopwords.words("english"))
    extractor = yake.KeywordExtractor(
        lan="en",
        n=3,
        dedup_lim=0.9,
        dedup_func="seqm",
        windowsSize=1,
        top=10,
        stopwords=nltk_stopwords,
    )

    raw_keywords = extractor.extract_keywords(article.title)
    linked = 0

    for kw_text, score in raw_keywords:
        normalized = kw_text.lower().strip()

        # skip if globally blocked in DB
        existing = session.query(Keyword).filter_by(text=normalized).first()
        if existing and existing.blocked:
            continue

        # upsert keyword
        keyword = existing or Keyword(text=normalized)
        if not existing:
            session.add(keyword)
            session.flush()

        # link to article with YAKE score
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
