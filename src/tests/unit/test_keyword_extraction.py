from unittest.mock import MagicMock

from db.models import Article, Keyword, article_keyword
from pipeline.keywords import (
    extract_keywords_batch,
    extract_keywords_keybert,
    link_keywords,
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


# --- link_keywords ---

def test_new_keyword_is_created_and_linked(db_session, fake_articles):
    article = fake_articles[0]
    count = link_keywords(db_session, article, [("machine learning", 0.1)])

    assert count == 1
    kw = db_session.query(Keyword).filter_by(text="machine learning").first()
    assert kw is not None
    assert article in kw.articles


def test_existing_keyword_is_reused(db_session, fake_articles):
    article = fake_articles[0]
    existing = Keyword(text="python")
    db_session.add(existing)
    db_session.flush()

    count = link_keywords(db_session, article, [("python", 0.2)])

    assert count == 1
    assert db_session.query(Keyword).filter_by(text="python").count() == 1
    assert article in existing.articles


def test_blocked_keyword_is_skipped(db_session, fake_articles):
    article = fake_articles[0]
    blocked = Keyword(text="spam", blocked=True)
    db_session.add(blocked)
    db_session.flush()

    count = link_keywords(db_session, article, [("spam", 0.05)])

    assert count == 0
    assert article not in blocked.articles


def test_mixed_blocked_and_valid(db_session, fake_articles):
    article = fake_articles[0]
    blocked = Keyword(text="ads", blocked=True)
    db_session.add(blocked)
    db_session.flush()

    count = link_keywords(db_session, article, [("ads", 0.1), ("climate", 0.2), ("economy", 0.3)])

    assert count == 2


def test_text_is_normalized(db_session, fake_articles):
    article = fake_articles[0]
    link_keywords(db_session, article, [("  Python  ", 0.1)])

    assert db_session.query(Keyword).filter_by(text="python").first() is not None
    assert db_session.query(Keyword).filter_by(text="  Python  ").first() is None


def test_score_is_stored(db_session, fake_articles):
    article = fake_articles[0]
    link_keywords(db_session, article, [("interest rates", 0.042)])

    row = db_session.execute(
        article_keyword.select().where(article_keyword.c.article_id == article.id)
    ).first()
    assert row is not None
    assert abs(row.score - 0.042) < 1e-6


def test_duplicate_keyword_in_batch_linked_once(db_session, fake_articles):
    article = fake_articles[0]
    count = link_keywords(db_session, article, [("energy crisis", 0.9), ("energy crisis", 0.8)])

    assert count == 1
    assert db_session.query(Keyword).filter_by(text="energy crisis").count() == 1


def test_empty_text_is_skipped(db_session, fake_articles):
    article = fake_articles[0]
    count = link_keywords(db_session, article, [("", 0.5), ("   ", 0.3)])

    assert count == 0


# --- extract_keywords_keybert ---

def _mock_kw_model(keywords: list[tuple[str, float]]) -> MagicMock:
    m = MagicMock()
    m.extract_keywords.return_value = keywords
    return m


def test_keybert_short_title_is_skipped(db_session, fake_articles):
    article = fake_articles[0]
    article.title = "Too short"  # < 4 words, KeyBERT skipped
    kw_model = _mock_kw_model([])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 0
    kw_model.extract_keywords.assert_not_called()


def test_keybert_extracts_and_links(db_session, fake_articles):
    article = fake_articles[0]  # "AI Lives Rent Free In My Head"
    kw_model = _mock_kw_model([("artificial intelligence", 0.85), ("machine learning", 0.72)])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 2  # keybert keywords only; topic linking lives elsewhere now
    kw_model.extract_keywords.assert_called_once()


def test_keybert_title_too_short_links_nothing(db_session, fake_articles):
    article = fake_articles[0]
    article.title = "Short title"  # 2 words
    kw_model = _mock_kw_model([])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 0
    kw_model.extract_keywords.assert_not_called()


def test_keybert_exactly_four_words_allowed(db_session, fake_articles):
    article = fake_articles[0]
    article.title = "UK energy crisis deepens"
    kw_model = _mock_kw_model([("energy crisis", 0.9)])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 1
    kw_model.extract_keywords.assert_called_once()


def test_keybert_none_title_links_nothing(db_session, fake_articles):
    article = fake_articles[0]
    article.title = None
    kw_model = _mock_kw_model([])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 0
    kw_model.extract_keywords.assert_not_called()


def test_keybert_duplicate_call_does_not_double_link(db_session, fake_articles):
    article = fake_articles[0]
    kw_model = _mock_kw_model([("energy crisis", 0.9)])

    count1 = extract_keywords_keybert(article, db_session, kw_model)
    count2 = extract_keywords_keybert(article, db_session, kw_model)

    assert count1 == 1
    assert count2 == 0
    assert db_session.query(Keyword).filter_by(text="energy crisis").count() == 1


def test_keybert_blocked_keyword_not_linked(db_session, fake_articles):
    article = fake_articles[0]
    blocked = Keyword(text="spam", blocked=True)
    db_session.add(blocked)
    db_session.flush()

    kw_model = _mock_kw_model([("spam", 0.9), ("technology", 0.7)])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 1
    assert article not in blocked.articles


# --- extract_keywords_batch ---

def _mock_batch_model(per_doc: list[list[tuple[str, float]]]) -> MagicMock:
    """Mock KeyBERT for a list input: extract_keywords returns one list per doc."""
    m = MagicMock()
    m.extract_keywords.return_value = per_doc
    return m


def test_batch_links_keywords_for_each_article(db_session, fake_articles):
    kw_model = _mock_batch_model([
        [("artificial intelligence", 0.85)],  # fake_articles[0]
        [("python language", 0.70)],          # fake_articles[1]
    ])

    count = extract_keywords_batch(db_session, fake_articles, kw_model)

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

    extract_keywords_batch(db_session, fake_articles, kw_model)

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

    count = extract_keywords_batch(db_session, fake_articles, kw_model)

    assert count == 1  # only python language links


def test_batch_does_not_duplicate_existing_link(db_session, fake_articles):
    # Pre-link the topic keyword, then have KeyBERT surface the same phrase.
    _seed_topic_keywords(db_session, "technology")
    link_topic_keywords(db_session, [fake_articles[0]])

    kw_model = _mock_batch_model([
        [("technology", 0.9)],  # collides with the topic link
        [("python language", 0.7)],
    ])

    count = extract_keywords_batch(db_session, fake_articles, kw_model)

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

    count = extract_keywords_batch(db_session, fake_articles, kw_model)

    assert count == 0
    kw_model.extract_keywords.assert_not_called()
