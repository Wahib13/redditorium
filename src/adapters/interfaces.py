from abc import ABC, abstractmethod
from typing import List

from common.hackernews import HackerNewsItem


class HackerNewsAPIInterface(ABC):

    @abstractmethod
    def fetch_stories(self, **kwargs) -> List[int]:
        pass

    @abstractmethod
    def fetch_story(self, story_id) -> HackerNewsItem | None:
        pass
