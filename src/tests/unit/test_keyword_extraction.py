from unittest.mock import MagicMock

from db.models import Article, Keyword, article_keyword
from pipeline.keywords import (
    extract_keywords_batch,
    link_topic_keywords,
)


# --- link_topic_keywords ---

def _seed_topic_keywords(session, *names):
    keywords = [Keyword(text=name) for name in names]
    session.add_all(keywords)
    session.flush()
    return keywords


def test_articles_linked_to_their_topic_keyword(db_session, fake_articles):
    _seed_topic_keywords(db_session, "technology", "politics")

    linked = link_topic_keywords(db_session, fake_articles)

    assert linked == 2
    tech = db_session.query(Keyword).filter_by(text="technology").first()
    politics = db_session.query(Keyword).filter_by(text="politics").first()
    assert fake_articles[0] in tech.articles  # source_topic="TECHNOLOGY"
    assert fake_articles[1] in politics.articles  # source_topic="POLITICS"


def test_blocked_topic_keyword_is_skipped(db_session, fake_articles):
    _seed_topic_keywords(db_session, "politics")
    db_session.add(Keyword(text="technology", blocked=True))
    db_session.flush()

    linked = link_topic_keywords(db_session, fake_articles)

    assert linked == 1  # only the POLITICS article links
    tech = db_session.query(Keyword).filter_by(text="technology").first()
    assert fake_articles[0] not in tech.articles


def test_missing_topic_keyword_is_skipped(db_session, fake_articles):
    _seed_topic_keywords(db_session, "technology")  # no "politics" keyword

    linked = link_topic_keywords(db_session, fake_articles)

    assert linked == 1


# --- extract_keywords_batch ---

def _mock_batch_model(per_doc: list[list[tuple[str, float]]]) -> MagicMock:
    """Mock KeyBERT for a list input: extract_keywords returns one list per doc."""
    m = MagicMock()
    m.extract_keywords.return_value = per_doc
    return m


def _mock_embed_client() -> MagicMock:
    """Mock embedding client returning one 384-dim vector per input text."""
    m = MagicMock()
    m.embed_batch.side_effect = lambda texts: [[0.0] * 384 for _ in texts]
    return m


def test_batch_links_keywords_for_each_article(db_session, fake_articles):
    kw_model = _mock_batch_model([
        [("artificial intelligence", 0.85)],  # fake_articles[0]
        [("python language", 0.70)],          # fake_articles[1]
    ])

    count = extract_keywords_batch(db_session, fake_articles, kw_model, _mock_embed_client())

    assert count == 2
    kw_model.extract_keywords.assert_called_once()  # a single batched call
    ai = db_session.query(Keyword).filter_by(text="artificial intelligence").first()
    py = db_session.query(Keyword).filter_by(text="python language").first()
    assert fake_articles[0] in ai.articles
    assert fake_articles[1] in py.articles


def test_batch_stores_scores(db_session, fake_articles):
    kw_model = _mock_batch_model([
        [("artificial intelligence", 0.85)],
        [("python language", 0.70)],
    ])

    extract_keywords_batch(db_session, fake_articles, kw_model, _mock_embed_client())

    row = db_session.execute(
        article_keyword.select().where(article_keyword.c.article_id == fake_articles[0].id)
    ).first()
    assert abs(row.score - 0.85) < 1e-6


def test_batch_embeds_only_new_keywords(db_session, fake_articles):
    existing = Keyword(text="artificial intelligence")
    db_session.add(existing)
    db_session.flush()

    embed_client = MagicMock()
    embed_client.embed_batch.return_value = [[0.5] * 384]  # only the one new text
    kw_model = _mock_batch_model([
        [("artificial intelligence", 0.85)],  # already exists → not embedded
        [("python language", 0.70)],          # new → embedded
    ])

    extract_keywords_batch(db_session, fake_articles, kw_model, embed_client)

    embed_client.embed_batch.assert_called_once_with(["python language"])
    py = db_session.query(Keyword).filter_by(text="python language").first()
    assert py.embedding is not None


def test_batch_skips_blocked_keyword(db_session, fake_articles):
    db_session.add(Keyword(text="artificial intelligence", blocked=True))
    db_session.flush()

    kw_model = _mock_batch_model([
        [("artificial intelligence", 0.85)],  # blocked → skipped
        [("python language", 0.70)],
    ])

    count = extract_keywords_batch(db_session, fake_articles, kw_model, _mock_embed_client())

    assert count == 1  # only python language links


def test_batch_does_not_duplicate_existing_link(db_session, fake_articles):
    # Pre-link the topic keyword, then have KeyBERT surface the same phrase.
    _seed_topic_keywords(db_session, "technology")
    link_topic_keywords(db_session, [fake_articles[0]])

    kw_model = _mock_batch_model([
        [("technology", 0.9)],  # collides with the topic link
        [("python language", 0.7)],
    ])

    count = extract_keywords_batch(db_session, fake_articles, kw_model, _mock_embed_client())

    assert count == 1  # only python language; technology already linked
    tech = db_session.query(Keyword).filter_by(text="technology").first()
    # still exactly one link between the article and the technology keyword
    links = db_session.execute(
        article_keyword.select().where(
            article_keyword.c.article_id == fake_articles[0].id,
            article_keyword.c.keyword_id == tech.id,
        )
    ).all()
    assert len(links) == 1


def test_batch_skips_short_titles(db_session, fake_articles):
    for a in fake_articles:
        a.title = "too short"  # < 4 words
    db_session.flush()
    kw_model = _mock_batch_model([])

    count = extract_keywords_batch(db_session, fake_articles, kw_model, _mock_embed_client())

    assert count == 0
    kw_model.extract_keywords.assert_not_called()
