import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.testclient import TestClient

from api.main import app
from db.connection import get_session_dependency, Base
from db.initialise import initialise_database
from db.models import Article, Feed, Source, Topic, Keyword

SAMPLE_ARTICLE_TEXT = "sample text"
SAMPLE_ARTICLE_SUMMARY = "a short lede summarising the story"


@pytest.fixture
def fake_source():
    topic = Topic(name="TECHNOLOGY")
    source_bbc = Source(name="BBC")
    source_bbc.feeds = [
        Feed(url="https://feed.test", topic=topic),
    ]
    return source_bbc


@pytest.fixture
def fake_keywords():
    return [
        Keyword(text="artificial intelligence"),
        Keyword(text="climate change"),
        Keyword(text="interest rates"),
        Keyword(text="machine learning"),
    ]


@pytest.fixture
def fake_articles(fake_source):
    return [
        Article(
            title="AI Lives Rent Free In My Head",
            url="https://example.com/article1",
            feed=fake_source.feeds[0],
            source_topic="TECHNOLOGY",
            text=SAMPLE_ARTICLE_TEXT,
            summary=SAMPLE_ARTICLE_SUMMARY,
        ),
        Article(
            title="Python is cool, but my favorite language is Sarcasm",
            url="https://example.com/article2",
            feed=fake_source.feeds[0],
            source_topic="POLITICS",
            text=SAMPLE_ARTICLE_TEXT,
            summary=SAMPLE_ARTICLE_SUMMARY,
        ),
    ]


@pytest.fixture
def fake_entries():
    return [
        {"link": "https://example.com/a", "title": "Article A"},
        {"link": "https://example.com/b", "title": "Article B"},
    ]


def make_test_db_session(fake_source, fake_articles):
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()

    session_maker_instance = sessionmaker(bind=connection)
    session: Session = session_maker_instance()

    initialise_database(session, [fake_source, *fake_articles])

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_session(
        fake_source,
        fake_articles,
):
    for session in make_test_db_session(fake_source, fake_articles):
        yield session


@pytest.fixture
def override_get_session(fake_source, fake_articles):
    gen = make_test_db_session(fake_source, fake_articles)
    session = next(gen)

    def _override():
        yield session

    yield _override

    try:
        next(gen)
    except StopIteration:
        pass


class FakeFeedData:
    def __init__(self, entries):
        self.entries = entries


@pytest.fixture
def test_client(override_get_session):
    app.dependency_overrides[get_session_dependency] = override_get_session
    return TestClient(app)
