import feedparser

from db.models import Article
from ingestion.main import fetch_rss_entries
from tests.conftest import FakeFeedData


def test_new_articles(db_session, fake_source, monkeypatch):
    fake_entries = [
        {"link": "https://example.com/a1", "title": "Article 1"},
        {"link": "https://example.com/a2", "title": "Article 2"},
    ]

    def fake_parse(url):
        return FakeFeedData(fake_entries)

    monkeypatch.setattr(feedparser, "parse", fake_parse)

    # Act
    articles = fetch_rss_entries(db_session)

    # Assert
    assert len(articles) == 2

    urls = {a.url for a in articles}
    assert urls == {
        "https://example.com/a1",
        "https://example.com/a2",
    }

    for article in articles:
        assert article.source == fake_source
        assert article.source_topic == "POLITICS"


def test_new_articles_skips_duplicates(db_session, fake_source, monkeypatch):
    existing = Article(
        url="https://example.com/a1",
        title="Existing",
        source_topic="TECHNOLOGY",
        source=fake_source,
    )

    db_session.add(existing)
    db_session.commit()

    fake_entries = [
        {"link": "https://example.com/a1", "title": "Duplicate"},
    ]

    monkeypatch.setattr(
        feedparser,
        "parse",
        lambda _: FakeFeedData(fake_entries),
    )

    articles = fetch_rss_entries(db_session)

    assert articles == []
