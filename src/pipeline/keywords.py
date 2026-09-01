import logging
from collections.abc import Callable

from keybert import KeyBERT
from sqlalchemy.orm import Session

from adapters.embeddings import SentenceTransformerClient
from db.models import Article, Keyword, article_keyword

logger = logging.getLogger(__name__)


def link_keywords(
        session: Session,
        article: Article,
        raw_keywords: list[tuple[str, float | None]],
        on_linked: Callable[[], None] | None = None,
        embed_client: SentenceTransformerClient | None = None,
) -> int:
    """Apply pre-extracted keywords to an article. Returns number of keywords linked.
    Commits and calls on_linked() after each successful link."""
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
            if embed_client:
                keyword.embedding = embed_client.embed(normalized)
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
        session.commit()
        linked += 1
        if on_linked:
            on_linked()

    return linked


def link_topic_keywords(session: Session, articles: list[Article]) -> int:
    """Link each article to the pre-created Keyword for its source_topic.

    Topic keywords are seeded (lowercased) by init_db. Blocked topics are
    skipped. Articles must already be flushed so they have ids. Bulk-inserts
    the join rows and returns how many were inserted.
    """
    topic_texts = {a.source_topic.lower() for a in articles if a.source_topic}
    if not topic_texts:
        return 0

    keyword_ids = {
        kw.text: kw.id
        for kw in session.query(Keyword)
        .filter(Keyword.text.in_(topic_texts), ~Keyword.blocked)
        .all()
    }

    rows = [
        {"article_id": a.id, "keyword_id": keyword_ids[a.source_topic.lower()], "score": None}
        for a in articles
        if a.source_topic and a.source_topic.lower() in keyword_ids
    ]
    if rows:
        session.execute(article_keyword.insert(), rows)
    return len(rows)


def extract_keywords_keybert(
        article: Article,
        session: Session,
        kw_model: KeyBERT,
        on_linked: Callable[[], None] | None = None,
        embed_client: SentenceTransformerClient | None = None,
) -> int:
    """Extract keywords from article title using KeyBERT"""
    keywords: list[tuple[str, float | None]] = []

    title = article.title or ""
    if len(title.split()) >= 4:
        keywords += kw_model.extract_keywords(title, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=5)

    return link_keywords(session, article, keywords, on_linked=on_linked, embed_client=embed_client)


def _normalize_keywords(raw: list[tuple[str, float]]) -> list[tuple[str, float | None]]:
    """Lowercase/strip keyword phrases, drop blanks, and de-dup within one article."""
    out: list[tuple[str, float | None]] = []
    seen: set[str] = set()
    for text, score in raw:
        normalized = text.lower().strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append((normalized, score))
    return out


def extract_keywords_batch(
        session: Session,
        articles: list[Article],
        kw_model: KeyBERT,
        embed_client: SentenceTransformerClient | None = None,
        batch_size: int = 64,
        min_title_words: int = 4,
) -> int:
    """Extract keywords for many articles with batched model calls, then bulk-link.

    Runs KeyBERT over titles in chunks of ``batch_size`` (one vectorised model
    call per chunk), get-or-creates the Keyword rows (embedding the genuinely
    new ones in a single ``embed_batch`` call), and bulk-inserts the join rows.
    Blocked keywords are skipped, and pairs already linked this run (e.g. a topic
    keyword) are not duplicated. Articles must already be flushed so they have
    ids. Does not commit — the caller owns the transaction. Returns the number
    of join rows inserted.
    """
    candidates = [a for a in articles if a.title and len(a.title.split()) >= min_title_words]
    if not candidates:
        return 0

    per_article: dict[int, list[tuple[str, float | None]]] = {}
    for start in range(0, len(candidates), batch_size):
        chunk = candidates[start:start + batch_size]
        titles = [a.title for a in chunk]
        results = kw_model.extract_keywords(
            titles, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=5
        )
        # A list input yields a list-of-lists; guard the single-doc shape too.
        if results and not isinstance(results[0], list):
            results = [results]
        for article, raw in zip(chunk, results):
            per_article[article.id] = _normalize_keywords(raw)

    distinct_texts = {text for kws in per_article.values() for text, _ in kws}
    if not distinct_texts:
        return 0

    keywords_by_text: dict[str, Keyword] = {
        kw.text: kw
        for kw in session.query(Keyword).filter(Keyword.text.in_(distinct_texts)).all()
    }

    new_texts = [t for t in distinct_texts if t not in keywords_by_text]
    if new_texts:
        embeddings = embed_client.embed_batch(new_texts) if embed_client else [None] * len(new_texts)
        new_keywords = [Keyword(text=t, embedding=e) for t, e in zip(new_texts, embeddings)]
        session.add_all(new_keywords)
        session.flush()
        for kw in new_keywords:
            keywords_by_text[kw.text] = kw

    keyword_id_by_text = {text: kw.id for text, kw in keywords_by_text.items() if not kw.blocked}

    # Existing links for these articles (topic keywords linked earlier this run)
    # would collide with the join table's composite PK, so skip them.
    linked_pairs: set[tuple[int, int]] = {
        (row.article_id, row.keyword_id)
        for row in session.execute(
            article_keyword.select().where(article_keyword.c.article_id.in_(per_article))
        )
    }

    rows = []
    for article_id, kws in per_article.items():
        for text, score in kws:
            keyword_id = keyword_id_by_text.get(text)
            if keyword_id is None or (article_id, keyword_id) in linked_pairs:
                continue
            linked_pairs.add((article_id, keyword_id))
            rows.append({"article_id": article_id, "keyword_id": keyword_id, "score": score})

    if rows:
        session.execute(article_keyword.insert(), rows)
    return len(rows)
