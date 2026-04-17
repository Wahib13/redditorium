import pytest

from db.models import Article
from pipeline.feed_data import stream_rss_entries, save_new_article
from tests.conftest import FakeFeedData


def _parse_fn(entries):
    """Factory: returns a parse_fn that always yields the given entries."""
    def _parse(_url):
        return FakeFeedData(entries)
    return _parse


@pytest.mark.anyio
async def test_new_articles_are_saved(db_session, fake_entries, fake_source):
    collected: list[int] = []

    async def collect(article_id: int):
        collected.append(article_id)

    await stream_rss_entries(db_session, on_new_article=collect, parse_fn=_parse_fn(fake_entries))

    assert len(collected) == len(fake_entries)
    for entry in fake_entries:
        assert db_session.query(Article).filter_by(url=entry["link"]).first() is not None


@pytest.mark.anyio
async def test_new_articles_skips_duplicates(db_session, fake_source, fake_articles):
    # fake_articles are already persisted in db_session by the conftest fixture
    entries = [{"link": a.url, "title": a.title} for a in fake_articles]
    article_count_before = db_session.query(Article).count()
    collected: list[int] = []

    async def collect(article_id: int):
        collected.append(article_id)

    await stream_rss_entries(db_session, on_new_article=collect, parse_fn=_parse_fn(entries))

    assert len(collected) == 0
    assert db_session.query(Article).count() == article_count_before


def test_save_new_article_creates_article(db_session, fake_source):
    feed = fake_source.feeds[0]
    article = save_new_article(db_session, feed, "https://new.com/x", "New Article")
    assert article is not None
    assert article.id is not None
    assert article.title == "New Article"
    assert article.source_topic == feed.topic.name


def test_save_new_article_skips_duplicate(db_session, fake_source, fake_articles):
    feed = fake_source.feeds[0]
    result = save_new_article(db_session, feed, fake_articles[0].url, "duplicate")
    assert result is None
