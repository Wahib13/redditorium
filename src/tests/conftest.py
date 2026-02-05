from typing import List, Dict
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.testclient import TestClient

from adapters.interfaces import LLMClient
from api.main import app
from config import settings
from db.connection import get_session_dependency, Base
from db.initialise import initialise_database
from db.models import Article as ArticleDB, Feed, FeedType, SourceName, Source, Topic, DailyTrendSummary

# Article text with more than MIN_ARTICLE_WORD_COUNT words for summary generation tests
SAMPLE_ARTICLE_TEXT = """This is the first line of the article.
This is the second line with more content.
The third line provides additional context.
Fourth line continues the narrative.
Fifth line adds more details.
Sixth line ensures we have enough content for summarization.""" + " extra words " * settings.MIN_ARTICLE_WORD_COUNT

# Article text with fewer than MIN_ARTICLE_WORD_COUNT
SAMPLE_ARTICLE_TEXT_SHORT = "word " * (settings.MIN_ARTICLE_WORD_COUNT - 1)


@pytest.fixture
def fake_source():
    source_bbc = Source(name=SourceName.BBC)
    source_bbc.feeds = [
        Feed(url="https://feed.test", feed_type=FeedType.POLITICS),
    ]
    return source_bbc


@pytest.fixture
def fake_topics():
    return [
        Topic(name=FeedType.TECHNOLOGY.value),
        Topic(name=FeedType.POLITICS.value),
        Topic(name=FeedType.BUSINESS.value),
        Topic(name=FeedType.HEALTH.value),
    ]


@pytest.fixture
def fake_articles(fake_topics, fake_source):
    """Articles with default timestamps (now)"""
    return [
        ArticleDB(
            title="AI Lives Rent Free In My Head",
            url="https://example.com/article1",
            topics=[fake_topics[0]],
            source=fake_source,
            source_topic=FeedType.TECHNOLOGY.value,
            text=SAMPLE_ARTICLE_TEXT
        ),
        ArticleDB(
            title="Python is cool, but my favorite language is Sarcasm",
            url="https://example.com/article2",
            topics=[fake_topics[1]],
            source=fake_source,
            source_topic=FeedType.POLITICS.value,
            text=SAMPLE_ARTICLE_TEXT
        ),
    ]


@pytest.fixture
def fake_articles_with_dates(fake_topics, fake_source):
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
            topics=[fake_topics[0]],
            source=fake_source,
            source_topic=FeedType.TECHNOLOGY.value,
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(today, datetime.time(10, 0, 0))
        ),
        ArticleDB(
            title="Latest Tech Update",
            url="https://example.com/today2",
            topics=[fake_topics[0]],
            source=fake_source,
            source_topic=FeedType.TECHNOLOGY.value,
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(today, datetime.time(18, 30, 0))
        ),
        # Article from yesterday
        ArticleDB(
            title="Yesterday's Big Story",
            url="https://example.com/yesterday",
            topics=[fake_topics[1]],
            source=fake_source,
            source_topic=FeedType.POLITICS.value,
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(yesterday, datetime.time(10, 0, 0))
        ),
        # Article from 2 days ago
        ArticleDB(
            title="Old News from Two Days Ago",
            url="https://example.com/twodays",
            topics=[fake_topics[2]],
            source=fake_source,
            source_topic=FeedType.BUSINESS.value,
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(two_days_ago, datetime.time(15, 30, 0))
        ),
        # Article from a week ago
        ArticleDB(
            title="Ancient Article from Last Week",
            url="https://example.com/week",
            topics=[fake_topics[3]],
            source=fake_source,
            source_topic=FeedType.HEALTH.value,
            text=SAMPLE_ARTICLE_TEXT,
            created=datetime.datetime.combine(week_ago, datetime.time(9, 0, 0))
        ),
    ]


def make_test_db_session(fake_source, fake_topics, fake_articles):
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()

    session_maker_instance = sessionmaker(bind=connection)
    session: Session = session_maker_instance()

    initialise_database(session, [*fake_topics, fake_source, *fake_articles])

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_session(
        fake_source,
        fake_topics,
        fake_articles,
):
    for session in make_test_db_session(fake_source, fake_topics, fake_articles):
        yield session


@pytest.fixture
def db_session_with_dated_articles(
        fake_source,
        fake_topics,
        fake_articles_with_dates,
):
    """Database session with articles that have specific creation dates"""
    for session in make_test_db_session(fake_source, fake_topics, fake_articles_with_dates):
        yield session


@pytest.fixture
def fake_articles_with_summaries(fake_topics, fake_source):
    """Articles with summaries for API testing"""
    now = datetime.datetime.now()
    today = now.date()
    yesterday = today - datetime.timedelta(days=1)

    return [
        # Today's tech articles with summaries
        ArticleDB(
            title="AI Breakthrough in 2026",
            url="https://example.com/ai-breakthrough",
            topics=[fake_topics[0]],  # Technology
            source=fake_source,
            source_topic=FeedType.TECHNOLOGY.value,
            summary="Scientists achieve major AI breakthrough.",
            created=datetime.datetime.combine(today, datetime.time(9, 0, 0))
        ),
        ArticleDB(
            title="New Programming Language Released",
            url="https://example.com/new-lang",
            topics=[fake_topics[0]],  # Technology
            source=fake_source,
            source_topic=FeedType.TECHNOLOGY.value,
            summary="A new programming language is released.",
            created=datetime.datetime.combine(today, datetime.time(14, 0, 0))
        ),
        # Today's politics articles with summaries
        ArticleDB(
            title="Government Announces Policy Change",
            url="https://example.com/policy",
            topics=[fake_topics[1]],  # Politics
            source=fake_source,
            source_topic=FeedType.POLITICS.value,
            summary="Government announces major policy shift.",
            created=datetime.datetime.combine(today, datetime.time(11, 0, 0))
        ),
        # Yesterday's articles with summaries
        ArticleDB(
            title="Yesterday's Tech News",
            url="https://example.com/yesterday-tech",
            topics=[fake_topics[0]],  # Technology
            source=fake_source,
            source_topic=FeedType.TECHNOLOGY.value,
            summary="Tech news from yesterday.",
            created=datetime.datetime.combine(yesterday, datetime.time(10, 0, 0))
        ),
        ArticleDB(
            title="Yesterday's Business Report",
            url="https://example.com/yesterday-business",
            topics=[fake_topics[2]],  # Business
            source=fake_source,
            source_topic=FeedType.BUSINESS.value,
            summary="Business report from yesterday.",
            created=datetime.datetime.combine(yesterday, datetime.time(15, 0, 0))
        ),
    ]


@pytest.fixture
def fake_daily_summaries(fake_topics, fake_articles_with_summaries):
    """Daily trend summaries for API testing"""
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    # Create daily summaries and link articles
    tech_summary_today = DailyTrendSummary(
        date=today,
        summary="Today's technology highlights: AI breakthroughs and new programming languages.",
        topic=fake_topics[0],  # Technology
    )
    # Link today's tech articles (first 2 articles)
    fake_articles_with_summaries[0].daily_trend_summary = tech_summary_today
    fake_articles_with_summaries[1].daily_trend_summary = tech_summary_today

    politics_summary_today = DailyTrendSummary(
        date=today,
        summary="Today's political news: Major policy changes announced.",
        topic=fake_topics[1],  # Politics
    )
    # Link today's politics article
    fake_articles_with_summaries[2].daily_trend_summary = politics_summary_today

    tech_summary_yesterday = DailyTrendSummary(
        date=yesterday,
        summary="Yesterday's tech news summary.",
        topic=fake_topics[0],  # Technology
    )
    # Link yesterday's tech article
    fake_articles_with_summaries[3].daily_trend_summary = tech_summary_yesterday

    business_summary_yesterday = DailyTrendSummary(
        date=yesterday,
        summary="Yesterday's business summary.",
        topic=fake_topics[2],  # Business
    )
    # Link yesterday's business article
    fake_articles_with_summaries[4].daily_trend_summary = business_summary_yesterday

    return [
        tech_summary_today,
        politics_summary_today,
        tech_summary_yesterday,
        business_summary_yesterday,
    ]


@pytest.fixture
def override_get_session(
        fake_source,
        fake_topics,
        fake_articles
):
    def _override():
        yield from make_test_db_session(fake_source, fake_topics, fake_articles)

    return _override


class FakeFeedData:
    def __init__(self, entries):
        self.entries = entries


class FakeLLM(LLMClient):
    def __init__(self, model: str):
        ...

    def chat(self, messages: List[Dict[str, str]], stream=False, **kwargs) -> str:
        return "Fake response"


@pytest.fixture
def override_get_session_with_summaries(
        fake_source,
        fake_topics,
        fake_articles_with_summaries,
        fake_daily_summaries,
):
    """Override with articles that have summaries and daily trend summaries"""
    def _override():
        yield from make_test_db_session(
            fake_source,
            fake_topics,
            [*fake_articles_with_summaries, *fake_daily_summaries]
        )

    return _override


@pytest.fixture
def test_client(override_get_session):
    app.dependency_overrides[get_session_dependency] = override_get_session
    return TestClient(app)


@pytest.fixture
def test_client_with_summaries(override_get_session_with_summaries):
    """Test client with daily summaries data"""
    app.dependency_overrides[get_session_dependency] = override_get_session_with_summaries
    return TestClient(app)
