from pydantic import BaseModel, ConfigDict


class Keyword(BaseModel):
    id: int
    text: str
    model_config = ConfigDict(from_attributes=True)


class Article(BaseModel):
    id: int
    title: str
    url: str
    model_config = ConfigDict(from_attributes=True)
