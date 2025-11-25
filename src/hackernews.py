import logging
import logging_config

import requests

from database import Story, get_session
from entities.hackernews import HackerNewsItem

logger = logging.getLogger(__name__)

BASE_URL = "https://hacker-news.firebaseio.com/v0"

response = requests.get(
    f"{BASE_URL}/topstories.json"
)

logger.debug(f"{len(response.json())} stories found")

with get_session() as session:
    for story_id in response.json():
        response = requests.get(
            f"{BASE_URL}/item/{story_id}.json"
        )
        hacker_news = HackerNewsItem.from_json(response.json())
        logger.debug(f"processing hacker news item: {hacker_news.id}")
        story = Story(
            hacker_news_id=hacker_news.id,
            title=hacker_news.title,
            url=str(hacker_news.url),
        )
        session.add(story)
    session.commit()
