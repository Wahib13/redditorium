import datetime

from db.models import Article, DailyTrendSummary, Topic
from summary.main import generate_article_summaries, generate_daily_summary
from tests.conftest import FakeLLM, SAMPLE_ARTICLE_TEXT, SAMPLE_ARTICLE_TEXT_SHORT


def test_generate_summary_for_articles(db_session):
    generate_article_summaries(db_session, FakeLLM("llama3.1:8b"))
    for article in db_session.query(Article).all():
        assert article.summary


def test_generate_daily_summary(db_session):
    generate_article_summaries(db_session, FakeLLM("llama3.1:8b"))

    # Generate daily summaries
    generate_daily_summary(db_session, FakeLLM("llama3.1:8b"))

    # Get articles from the last 24 hours
    cutoff = datetime.datetime.now() - datetime.timedelta(days=1)
    recent_articles = db_session.query(Article).filter(Article.created >= cutoff).all()

    # Get unique topics from those articles
    unique_topics = set()
    for article in recent_articles:
        for topic in article.topics:
            unique_topics.add(topic.id)

    expected_topic_count = len(unique_topics)

    # Check that daily summaries were created
    daily_summaries = db_session.query(DailyTrendSummary).all()
    assert len(daily_summaries) == expected_topic_count, f"Should have created a daily summary for each topic ({expected_topic_count} topics)"

    # Check that the correct date is applied
    for summary in daily_summaries:
        assert summary.date == datetime.datetime.now().date()
        assert summary.summary is not None


def test_generate_article_summaries_default_past_24_hours(db_session_with_dated_articles):
    """Test that default behavior only summarizes articles from the past 24 hours"""
    # Generate summaries with default date (past 24 hours)
    generate_article_summaries(db_session_with_dated_articles, FakeLLM("llama3.1:8b"))

    # Get all articles
    all_articles = db_session_with_dated_articles.query(Article).all()

    # Calculate which articles should be within past 24 hours
    cutoff_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
    expected_articles_in_range = [a for a in all_articles if a.created >= cutoff_datetime]

    # Check which articles got summaries
    articles_with_summaries = [a for a in all_articles if a.summary]

    # Verify the correct number of articles were summarized
    assert len(articles_with_summaries) == len(expected_articles_in_range), \
        f"Should summarize {len(expected_articles_in_range)} articles from past 24 hours"

    # Verify that articles within the range got summaries
    for article in expected_articles_in_range:
        assert article.summary, f"Article '{article.title}' should have been summarized"

    # Verify articles outside the range were not summarized
    articles_outside_range = [a for a in all_articles if a.created < cutoff_datetime]
    for article in articles_outside_range:
        assert not article.summary, f"Article '{article.title}' should not have been summarized"

    # article older than 24 hours should not be summarized
    for article in all_articles:
        if article.created < cutoff_datetime:
            assert not article.summary, f"article with title: '{article.title}' created on date: '{article.created}' older than 24 hours should not be summarized"


def test_generate_article_summaries_specific_datetime_yesterday(db_session_with_dated_articles):
    """Test that providing a specific datetime only summarizes articles created after that datetime"""
    yesterday = datetime.datetime.combine(
        datetime.date.today() - datetime.timedelta(days=1),
        datetime.time(10, 32, 0)
    )
    today = datetime.datetime.combine(
        datetime.date.today(),
        datetime.time(10, 32, 0)
    )

    # Generate summaries for articles created >= yesterday at midnight
    generate_article_summaries(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=yesterday)

    # Get all articles
    all_articles = db_session_with_dated_articles.query(Article).all()

    # Calculate expected articles (created >= yesterday)
    expected_articles = [a for a in all_articles if yesterday <= a.created < today]
    articles_before_cutoff = [a for a in all_articles if a.created < yesterday]

    # Verify articles created >= yesterday have summaries
    for article in expected_articles:
        assert article.summary, f"Article '{article.title}' created at {article.created} should have been summarized"

    # Verify articles created before yesterday do not have summaries
    for article in articles_before_cutoff:
        assert not article.summary, f"Article '{article.title}' created at {article.created} should not have been summarized"


def test_generate_article_summaries_specific_datetime_two_days_ago(db_session_with_dated_articles):
    """Test summarizing articles created after a datetime from 2 days ago"""
    two_days_ago = datetime.datetime.combine(
        datetime.date.today() - datetime.timedelta(days=2),
        datetime.time(10, 32, 0)
    )
    one_day_ago = datetime.datetime.combine(
        datetime.date.today() - datetime.timedelta(days=1),
        datetime.time(10, 32, 0)
    )

    # Generate summaries for articles created >= 2 days ago
    generate_article_summaries(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=two_days_ago)

    # Get all articles
    all_articles = db_session_with_dated_articles.query(Article).all()

    # Calculate expected articles (2 days <= created < one day ago)
    expected_articles = [a for a in all_articles if two_days_ago <= a.created < one_day_ago]
    articles_before_cutoff = [a for a in all_articles if a.created < two_days_ago]

    # Verify articles created >= 2 days ago have summaries
    for article in expected_articles:
        assert article.summary, f"Article '{article.title}' created at {article.created} should have been summarized"

    # Verify articles created before 2 days ago do not have summaries
    for article in articles_before_cutoff:
        assert not article.summary, f"Article '{article.title}' created at {article.created} should not have been summarized"


def test_generate_article_summaries_no_articles_for_datetime(db_session_with_dated_articles):
    """Test that no summaries are generated when no articles exist after a datetime"""
    # Use a datetime far in the future where no articles exist
    future_datetime = datetime.datetime.now() + datetime.timedelta(days=30)

    # Generate summaries for future datetime (should be no articles)
    generate_article_summaries(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=future_datetime)

    # Get all articles
    all_articles = db_session_with_dated_articles.query(Article).all()

    # No articles should have summaries
    articles_with_summaries = [a for a in all_articles if a.summary]
    assert len(articles_with_summaries) == 0, "No articles should be summarized for future datetime"


def test_generate_daily_summary_default_past_24_hours(db_session_with_dated_articles):
    """Test that default behavior creates daily summaries from articles in the past 24 hours"""
    # First, generate article summaries for recent articles (default past 24 hours)
    generate_article_summaries(db_session_with_dated_articles, FakeLLM("llama3.1:8b"))

    # Generate daily summaries with default (past 24 hours)
    generate_daily_summary(db_session_with_dated_articles, FakeLLM("llama3.1:8b"))

    # Check that daily summaries were created
    daily_summaries = db_session_with_dated_articles.query(DailyTrendSummary).all()
    assert len(daily_summaries) > 0, "Should have created at least one daily summary"

    # All daily summaries should be tagged with today's date
    today = datetime.date.today()
    for summary in daily_summaries:
        assert summary.date == today, "Daily summary should be tagged with today's date"
        assert summary.summary is not None

    # Verify that only articles from past 24 hours are linked
    cutoff = datetime.datetime.now() - datetime.timedelta(days=1)
    all_articles = db_session_with_dated_articles.query(Article).all()
    recent_articles = [a for a in all_articles if a.created >= cutoff]
    old_articles = [a for a in all_articles if a.created < cutoff]

    for article in recent_articles:
        if article.summary:  # Only articles with summaries should be linked
            assert article.daily_trend_summary is not None, f"Recent article '{article.title}' should be linked to a daily summary"

    for article in old_articles:
        assert article.daily_trend_summary is None, f"Old article '{article.title}' should not be linked to a daily summary"


def test_generate_daily_summary_specific_datetime_yesterday(db_session_with_dated_articles):
    """Test that providing yesterday's datetime creates summaries from articles after that datetime"""
    yesterday = datetime.datetime.combine(
        datetime.date.today() - datetime.timedelta(days=1),
        datetime.time(10, 32, 0)
    )

    # First, generate article summaries for articles from yesterday onwards
    generate_article_summaries(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=yesterday)

    # Generate daily summaries for articles from yesterday onwards
    generate_daily_summary(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=yesterday)

    # Check that daily summaries were created
    daily_summaries = db_session_with_dated_articles.query(DailyTrendSummary).all()
    assert len(daily_summaries) > 0, "Should have created at least one daily summary"

    # All daily summaries should be tagged with yesterday's date
    for summary in daily_summaries:
        assert summary.date == yesterday.date(), "Daily summary should be tagged with yesterday's date"
        assert summary.summary is not None

    # Verify that articles from yesterday onwards are linked
    all_articles = db_session_with_dated_articles.query(Article).all()
    articles_after_cutoff = [a for a in all_articles if a.created >= yesterday and a.summary]

    for article in articles_after_cutoff:
        assert article.daily_trend_summary is not None, f"Article '{article.title}' from after cutoff should be linked"


def test_generate_daily_summary_specific_datetime_today(db_session_with_dated_articles):
    """Test that providing today's datetime creates summaries from articles after that datetime"""
    today = datetime.datetime.combine(
        datetime.date.today(),
        datetime.time(10, 32, 0)
    )

    # First, generate article summaries for today
    generate_article_summaries(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=today)

    # Generate daily summaries for today
    generate_daily_summary(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=today)

    # Check that daily summaries were created
    daily_summaries = db_session_with_dated_articles.query(DailyTrendSummary).all()
    assert len(daily_summaries) > 0, "Should have created at least one daily summary"

    # All daily summaries should be tagged with today's date
    for summary in daily_summaries:
        assert summary.date == today.date()
        assert summary.summary is not None

    # Verify that today's articles are linked
    all_articles = db_session_with_dated_articles.query(Article).all()
    today_articles = [a for a in all_articles if a.created >= today]

    for article in today_articles:
        if article.summary:  # Only articles with summaries should be linked
            assert article.daily_trend_summary is not None, f"Today's article '{article.title}' should be linked"


def test_generate_daily_summary_no_articles_with_summaries(db_session_with_dated_articles):
    """Test that no daily summaries are created when articles don't have summaries"""
    yesterday = datetime.datetime.combine(
        datetime.date.today() - datetime.timedelta(days=1),
        datetime.time(0, 0, 0)
    )

    # Don't generate article summaries first - articles will have no summaries
    # Try to generate daily summaries anyway
    generate_daily_summary(db_session_with_dated_articles, FakeLLM("llama3.1:8b"), date=yesterday)

    # No daily summaries should be created since articles have no summaries
    daily_summaries = db_session_with_dated_articles.query(DailyTrendSummary).all()
    assert len(daily_summaries) == 0, "Should not create daily summaries when articles have no summaries"


def test_generate_article_summaries_skips_short_articles(db_session, fake_source):
    """Test that articles with fewer than MIN_ARTICLE_LENGTH words or fewer are skipped during summarization."""
    # Get the source from the database (it was added via fixtures)
    source = db_session.query(Article).first().source

    # Add a short article
    short_article = Article(
        title="Short Article",
        url="https://example.com/short",
        source_topic="technology",
        source=source,
        text=SAMPLE_ARTICLE_TEXT_SHORT
    )
    db_session.add(short_article)

    # Add a long article
    long_article = Article(
        title="Long Article",
        url="https://example.com/long",
        source_topic="technology",
        source=source,
        text=SAMPLE_ARTICLE_TEXT  # 6 lines
    )
    db_session.add(long_article)
    db_session.commit()

    # Generate summaries
    generate_article_summaries(db_session, FakeLLM("llama3.1:8b"))

    # Refresh from database
    db_session.refresh(short_article)
    db_session.refresh(long_article)

    # Short article should not have a summary
    assert short_article.summary is None, "Article with 5 lines should not be summarized"

    # Long article should have a summary
    assert long_article.summary is not None, "Article with more than 5 lines should be summarized"


def test_generate_article_summaries_skips_empty_text(db_session, fake_source):
    """Test that articles with no text are skipped during summarization"""
    # Get the source from the database (it was added via fixtures)
    source = db_session.query(Article).first().source

    # Add an article with no text
    empty_article = Article(
        title="Empty Article",
        url="https://example.com/empty",
        source_topic="technology",
        source=source,
        text=None
    )
    db_session.add(empty_article)
    db_session.commit()

    # Generate summaries
    generate_article_summaries(db_session, FakeLLM("llama3.1:8b"))

    # Refresh from database
    db_session.refresh(empty_article)

    # Empty article should not have a summary
    assert empty_article.summary is None, "Article with no text should not be summarized"
