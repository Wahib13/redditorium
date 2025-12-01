import pytest
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from common.hackernews import HackerNewsItem, Type
from db.connection import Base


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()

    session_maker_instance = sessionmaker(bind=connection)
    session: Session = session_maker_instance()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_hackernews_api():
    api = Mock()
    return api


@pytest.fixture
def sample_stories():
    return [
        HackerNewsItem(
            id=1,
            type=Type.STORY,
            text="Hello World",
            url="https://example.com/"
        ),
        HackerNewsItem(
            id=2,
            type=Type.STORY,
            text="Hello World",
            url="https://example.com/"
        )
    ]
