from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, HttpUrl, ValidationError


class Type(Enum):
    JOB = "job"
    STORY = "story"
    COMMENT = "comment"
    POLL = "poll"
    POLLOPT = "pollopt"


class HackerNewsItem(BaseModel):
    id: int
    type: Type
    by: Optional[str] = None
    time: Optional[datetime] = None
    text: Optional[str] = None
    dead: Optional[bool] = None
    deleted: Optional[bool] = None
    parent: Optional[int] = None
    poll: Optional[int] = None
    kids: Optional[List[int]] = None
    url: Optional[HttpUrl] = None
    score: Optional[int] = None
    title: Optional[str] = None
    parts: Optional[List[int]] = None
    descendants: Optional[int] = None

    @classmethod
    def from_json(cls, data: dict):
        if "time" in data and isinstance(data["time"], int):
            data["time"] = datetime.fromtimestamp(data["time"])
        try:
            return cls(**data)
        except ValidationError as e:
            print("Validation error:", e)
            return None
