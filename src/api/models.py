from pydantic import BaseModel, ConfigDict, field_validator


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
    id: int | None
    text: str
    articles: list[ArticleInKeyword]
    model_config = ConfigDict(from_attributes=True)


class ArticlesProcessedRequest(BaseModel):
    article_ids: list[int]


class KeywordMappingCreate(BaseModel):
    raw_keyword: str
    canonical_keyword: str


class KeywordMappingRead(BaseModel):
    id: int
    raw_keyword: str
    canonical_keyword: str
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class UserKeywordRuleCreate(BaseModel):
    pattern: str
    keyword: str
    case_sensitive: bool = False


class UserKeywordRuleRead(BaseModel):
    id: int
    pattern: str
    keyword: str
    user_id: int
    case_sensitive: bool
    model_config = ConfigDict(from_attributes=True)


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
