from db.models import Article, Keyword, article_keyword
from pipeline.keywords import link_keywords


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
