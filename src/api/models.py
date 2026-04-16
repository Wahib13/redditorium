from pydantic import BaseModel, ConfigDict


class Keyword(BaseModel):
    id: int
    text: str
    model_config = ConfigDict(from_attributes=True)


class Article(BaseModel):
    id: int
    title: str | None
    url: str | None
    model_config = ConfigDict(from_attributes=True)


class ArticleInKeyword(BaseModel):
    id: int
    title: str | None
    url: str | None
    model_config = ConfigDict(from_attributes=True)


class KeywordWithArticles(BaseModel):
    id: int
    text: str
    articles: list[ArticleInKeyword]
    model_config = ConfigDict(from_attributes=True)


class ArticlesProcessedRequest(BaseModel):
    article_ids: list[int]
