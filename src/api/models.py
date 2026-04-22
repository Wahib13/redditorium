from pydantic import BaseModel, ConfigDict, field_validator


class Keyword(BaseModel):
    id: int
    text: str
    model_config = ConfigDict(from_attributes=True)


class Article(BaseModel):
    id: int
    title: str | None
    url: str | None
    summary: str | None
    image: str | None
    model_config = ConfigDict(from_attributes=True)


class KeywordWithArticles(BaseModel):
    id: int | None
    text: str
    articles: list[Article]
    model_config = ConfigDict(from_attributes=True)


class ArticleSearchResult(BaseModel):
    id: int
    title: str | None
    url: str | None
    summary: str | None
    image: str | None
    distance: float



class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


MIN_PASSWORD_LENGTH = 8


class UserCreate(BaseModel):
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        return v


class UserRead(BaseModel):
    id: int
    email: str
    admin: bool
    model_config = ConfigDict(from_attributes=True)
