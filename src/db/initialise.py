from db.connection import get_session, engine, Base
from db.models import Topic


def initialise_database():
    Base.metadata.create_all(engine)

    with get_session() as session:
        default_topic: Topic = Topic(
            description="default topic"
        )
        session.add(default_topic)
        session.commit()
