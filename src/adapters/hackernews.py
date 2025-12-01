import logging
from typing import List

import requests
from pydantic import TypeAdapter

from adapters.interfaces import HackerNewsAPIInterface
from common.hackernews import HackerNewsItem
from config import HACKER_NEWS_BASE_URL

logger = logging.getLogger(__name__)


class HackerNewsAPIClient(HackerNewsAPIInterface):

    def fetch_stories(
            self,
            endpoint="topstories"
    ) -> List[int]:
        response = requests.get(
            f"{HACKER_NEWS_BASE_URL}/{endpoint}.json"
        )
        logger.debug(response.json())
        ids = TypeAdapter(List[int]).validate_python(response.json())
        return ids

    def fetch_story(self, story_id) -> HackerNewsItem:
        response = requests.get(
            f"{HACKER_NEWS_BASE_URL}/item/{story_id}.json"
        )
        logger.debug(response.json())
        return HackerNewsItem.from_json(response.json())
