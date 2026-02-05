import logging
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra='ignore', env_file="../.env")

    CORS_ALLOWED_ORIGINS: List[str] = []
    DATABASE_CONNECTION_STRING: str = ""
    OLLAMA_MODEL: str = "llama3.1:8b"
    # Minimum number of words in an article to be considered for summarization
    MIN_ARTICLE_WORD_COUNT: int = 400


settings = Settings()


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
