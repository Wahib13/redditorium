from db.models import Article, Topic


def infer_topics(session):
    """
    Assign a Topic entity to each Article based on source_topic
    """
    articles = session.query(Article).filter(
        ~Article.topics.any()
    ).all()

    for article in articles:
        if not article.source_topic:
            continue

        topic = (
            session.query(Topic)
            .filter_by(name=article.source_topic)
            .first()
        )

        if not topic:
            topic = Topic(name=article.source_topic)
            session.add(topic)
            session.flush()  # ensures topic.id exists

        if topic not in article.topics:
            article.topics.append(topic)

    session.commit()
