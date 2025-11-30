from typing import List

from pydantic import BaseModel


class Topic(BaseModel):
    id: int
    name: str
    representation: List[str]
    representative_docs: List[str]
