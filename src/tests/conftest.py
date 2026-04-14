import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.testclient import TestClient

from api.main import app
from db.connection import get_session_dependency, Base
from db.initialise import initialise_database
from db.models import Article as ArticleDB, Feed, Source, Topic, Keyword

SAMPLE_ARTICLE_TEXT = "sample text"


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
    """Articles with default timestamps (now)"""
    return [
        ArticleDB(
            title="AI Lives Rent Free In My Head",
            url="https://example.com/article1",
            feed=fake_source.feeds[0],
            source_topic="TECHNOLOGY",
            text=SAMPLE_ARTICLE_TEXT
        ),
        ArticleDB(
            title="Python is cool, but my favorite language is Sarcasm",
            url="https://example.com/article2",
            feed=fake_source.feeds[0],
            source_topic="POLITICS",
            text=SAMPLE_ARTICLE_TEXT
        ),
    ]


@pytest.fixture
def fake_articles_with_dates(fake_source):
    """Articles with specific creation dates for testing date filtering"""
    now = datetime.datetime.now()
    today = now.date()
    yesterday = today - datetime.timedelta(days=1)
    two_days_ago = today - datetime.timedelta(days=2)
    week_ago = today - datetime.timedelta(days=7)

    return [
        # Articles from today (within past 24 hours) - use explicit times on today's date
        ArticleDB(
            title="Breaking News Today Morning",
            url="https://example.com/today1",
            feed=fake_source.feeds[0],
            source_topic="TECHNOLOGY",
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(today, datetime.time(10, 0, 0))
        ),
        ArticleDB(
            title="Latest Tech Update",
            url="https://example.com/today2",
            feed=fake_source.feeds[0],
            source_topic="TECHNOLOGY",
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(today, datetime.time(18, 30, 0))
        ),
        # Article from yesterday
        ArticleDB(
            title="Yesterday's Big Story",
            url="https://example.com/yesterday",
            feed=fake_source.feeds[0],
            source_topic="POLITICS",
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(yesterday, datetime.time(10, 0, 0))
        ),
        # Article from 2 days ago
        ArticleDB(
            title="Old News from Two Days Ago",
            url="https://example.com/twodays",
            feed=fake_source.feeds[0],
            source_topic="BUSINESS",
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(two_days_ago, datetime.time(15, 30, 0))
        ),
        # Article from a week ago
        ArticleDB(
            title="Ancient Article from Last Week",
            url="https://example.com/week",
            feed=fake_source.feeds[0],
            source_topic="HEALTH",
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(week_ago, datetime.time(9, 0, 0))
        ),
    ]


def make_test_db_session(fake_source, fake_articles):
    engine = create_engine("sqlite:///:memory:", echo=False)
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
def db_session_with_dated_articles(
        fake_source,
        fake_articles_with_dates,
):
    """Database session with articles that have specific creation dates"""
    for session in make_test_db_session(fake_source, fake_articles_with_dates):
        yield session


@pytest.fixture
def override_get_session(
        fake_source,
        fake_articles
):
    def _override():
        yield from make_test_db_session(fake_source, fake_articles)

    return _override


class FakeFeedData:
    def __init__(self, entries):
        self.entries = entries


@pytest.fixture
def test_client(override_get_session):
    app.dependency_overrides[get_session_dependency] = override_get_session
    return TestClient(app)
