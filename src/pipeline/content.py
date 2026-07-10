import logging

from newspaper import Article as NewspaperArticle
from sqlalchemy.orm import Session, defer

from db.models import Article

logger = logging.getLogger(__name__)


def fetch_article_content(session: Session) -> None:
    # Only load articles missing text, and skip the large embedding column
    # since it isn't needed here.
    articles = (
        session.query(Article)
        .filter(Article.text.is_(None))
        .options(defer(Article.embedding))
        .all()
    )
    for article in articles:
        try:
            newspaper_article = NewspaperArticle(article.url)
            newspaper_article.download()
            newspaper_article.parse()

            article.text = newspaper_article.text
            session.commit()

            logger.debug(f"processed article {article.id}. database title: {article.title} | extracted title: {newspaper_article.title}")
        except Exception as e:
            logger.warning(f"error when parsing article {article.id}: {str(e)}")
