from db.models import Article, Topic, Source
from inference.main import infer_topics


def test_topic_inference(db_session):
    source = db_session.query(Source).first()
    article = Article(
        title="AI is everywhere",
        source_topic="technology",
        source=source
    )
    db_session.add(article)
    db_session.commit()

    infer_topics(db_session)

    topic = (
        db_session.query(Topic)
        .filter_by(name="technology")
        .one()
    )

    db_session.refresh(article)
    assert topic in article.topics


def test_topic_inference_is_idempotent(db_session):
    source = db_session.query(Source).first()
    article = Article(
        title="AI again",
        source_topic="TECHNOLOGY",
        source=source
    )
    db_session.add(article)
    db_session.commit()

    topics = db_session.query(Topic).all()
    prev_count = len(topics)

    infer_topics(db_session)
    infer_topics(db_session)  # run twice

    db_session.refresh(article)

    assert len(article.topics) == 1
    assert article.topics[0].name == "TECHNOLOGY"

    # also ensure only one Topic exists
    assert db_session.query(Topic).count() == prev_count


def test_existing_topic_is_reused(db_session):
    topic = db_session.query(Topic).filter_by(name="TECHNOLOGY").first()

    source = db_session.query(Source).first()
    article = Article(
        title="Reuse topic",
        source_topic="TECHNOLOGY",
        source=source
    )
    db_session.add(article)
    db_session.commit()

    infer_topics(db_session)

    db_session.refresh(article)


    assert article.topics[0].id == topic.id
