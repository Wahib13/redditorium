import logging
import time
from typing import List

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from adapters.interfaces import HackerNewsAPIInterface
from common.hackernews import Type
from db.models import Story as StoryModel

logger = logging.getLogger(__name__)


def fetch_stories(
        api_client: HackerNewsAPIInterface,
        session: Session,
        story_ids: List[int] = None
):
    if not story_ids:
        story_ids = api_client.fetch_stories()

    for i, hacker_news_story_id in enumerate(story_ids, start=1):
        logger.info(f"processing hacker news item: {hacker_news_story_id}")
        hacker_news_story = api_client.fetch_story(hacker_news_story_id)

        if hacker_news_story:
            data = {
                "hacker_news_id": hacker_news_story.id,
                "title": hacker_news_story.title,
                "url": str(hacker_news_story.url),
                "type": hacker_news_story.type.value,
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

        if i % 50 == 0:  # wait a bit so the API doesn't reject requests
            time.sleep(10)

    session.commit()
