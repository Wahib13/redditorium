from unittest.mock import MagicMock

from db.models import Article, Keyword, article_keyword
from pipeline.keywords import extract_keywords_keybert, link_keywords


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


def test_keybert_topic_always_linked(db_session, fake_articles):
    # fake_articles[0] feed has topic "TECHNOLOGY"
    article = fake_articles[0]
    article.title = "Too short"  # < 4 words, KeyBERT skipped
    kw_model = _mock_kw_model([])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 1
    assert db_session.query(Keyword).filter_by(text="technology").first() is not None
    kw_model.extract_keywords.assert_not_called()


def test_keybert_extracts_and_links(db_session, fake_articles):
    article = fake_articles[0]  # "AI Lives Rent Free In My Head", topic "TECHNOLOGY"
    kw_model = _mock_kw_model([("artificial intelligence", 0.85), ("machine learning", 0.72)])

    count = extract_keywords_keybert(article, db_session, kw_model)

    # topic + 2 keybert keywords
    assert count == 3
    kw_model.extract_keywords.assert_called_once()


def test_keybert_title_too_short_only_topic_linked(db_session, fake_articles):
    article = fake_articles[0]
    article.title = "Short title"  # 2 words
    kw_model = _mock_kw_model([])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 1  # topic only
    kw_model.extract_keywords.assert_not_called()


def test_keybert_exactly_four_words_allowed(db_session, fake_articles):
    article = fake_articles[0]
    article.title = "UK energy crisis deepens"
    kw_model = _mock_kw_model([("energy crisis", 0.9)])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 2  # topic + 1 keybert keyword
    kw_model.extract_keywords.assert_called_once()


def test_keybert_none_title_only_topic_linked(db_session, fake_articles):
    article = fake_articles[0]
    article.title = None
    kw_model = _mock_kw_model([])

    count = extract_keywords_keybert(article, db_session, kw_model)

    assert count == 1  # topic only
    kw_model.extract_keywords.assert_not_called()


def test_keybert_duplicate_call_does_not_double_link(db_session, fake_articles):
    article = fake_articles[0]
    kw_model = _mock_kw_model([("energy crisis", 0.9)])

    count1 = extract_keywords_keybert(article, db_session, kw_model)
    count2 = extract_keywords_keybert(article, db_session, kw_model)

    assert count1 == 2  # topic + energy crisis
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
