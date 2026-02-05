from db.connection import get_session
from db.initialise import initialise_database
from db.models import Source, Feed, Topic

if __name__ == "__main__":
    with get_session() as session:
        source_bbc = Source(name="BBC")
        source_the_guardian = Source(name="THE_GUARDIAN")

        topic_politics = Topic(name="POLITICS")
        topic_technology = Topic(name="TECHNOLOGY")
        topic_business = Topic(name="BUSINESS")
        topic_health = Topic(name="HEALTH")

        default_topics = [
            topic_politics, topic_technology, topic_business, topic_health
        ]

        source_bbc.feeds = [
            Feed(url="https://feeds.bbci.co.uk/news/politics/rss.xml", topic=topic_politics),
            Feed(url="https://feeds.bbci.co.uk/news/technology/rss.xml", topic=topic_technology),
            Feed(url="https://feeds.bbci.co.uk/news/business/rss.xml", topic=topic_business),
            Feed(url="https://feeds.bbci.co.uk/news/health/rss.xml", topic=topic_health)
        ]
        source_the_guardian.feeds = [
            Feed(url="https://www.theguardian.com/politics/rss", topic=topic_politics),
            Feed(url="https://www.theguardian.com/technology/rss", topic=topic_technology),
            Feed(url="https://www.theguardian.com/business/rss", topic=topic_business),
            Feed(url="https://www.theguardian.com/society/health/rss", topic=topic_health)
        ]
        initialise_database(session, [source_bbc, source_the_guardian, *default_topics])
