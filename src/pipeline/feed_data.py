import feedparser

from db.models import Article, Source


def fetch_rss_entries(session):
    articles_to_insert = []

    for source in session.query(Source).all():
        for feed in source.feeds:
            feed_data = feedparser.parse(feed.url)
            print(feed_data.entries)
            for entry in feed_data.entries:
                url = entry.get("link")
                title = entry.get("title")

                # Simple deduplication: skip if URL already in DB
                exists = session.query(Article).filter_by(url=url).first()
                if exists:
                    continue

                article = Article(
                    url=url,
                    title=title,
                    source_topic=feed.topic.name,
                    feed=feed
                )
                articles_to_insert.append(article)

    return articles_to_insert


def save_articles(articles, session):
    session.add_all(articles)
    session.commit()
    print(f"Inserted {len(articles)} new articles")
