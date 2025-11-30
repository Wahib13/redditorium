import logging
from typing import List

from sqlalchemy.dialects.sqlite import insert

from adapters.interfaces import HackerNewsAPIInterface
from db.connection import get_session
from db.models import Story as StoryModel

logger = logging.getLogger(__name__)


def fetch_stories(api_client: HackerNewsAPIInterface, limit: int = None):
    with get_session() as session:
        stories: List[int] = api_client.fetch_stories()
        if limit:
            stories = stories[:limit]
        for i, hacker_news_story_id in enumerate(stories, start=1):
            logger.info(f"processing hacker news item: {hacker_news_story_id}")
            hacker_news_story = api_client.fetch_story(hacker_news_story_id)

            data = {
                "hacker_news_id": hacker_news_story.id,
                "title": hacker_news_story.title,
                "url": str(hacker_news_story.url),
            }
            stmt = insert(StoryModel).values(
                **data
            ).on_conflict_do_update(
                index_elements=["hacker_news_id"],
                set_=data,
            )

            session.execute(stmt)

            if i % 100 == 0:
                session.commit()

        session.commit()
