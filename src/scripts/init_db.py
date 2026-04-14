import yaml
from pathlib import Path

from db.connection import get_session
from db.initialise import initialise_database
from db.models import Source, Feed, Topic

SEEDS_PATH = Path(__file__).parent.parent / "seeds.yaml"

if __name__ == "__main__":
    with open(SEEDS_PATH) as f:
        seeds = yaml.safe_load(f)

    # Derive unique topics from feed definitions
    topic_names = {feed["topic"] for source in seeds["sources"] for feed in source["feeds"]}
    topics = {name: Topic(name=name) for name in topic_names}

    sources = []
    for source_data in seeds["sources"]:
        source = Source(name=source_data["name"])
        source.feeds = [
            Feed(url=feed["url"], topic=topics[feed["topic"]])
            for feed in source_data["feeds"]
        ]
        sources.append(source)

    with get_session() as session:
        initialise_database(session, [*topics.values(), *sources])
