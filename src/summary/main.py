import datetime
import logging

from sqlalchemy.orm import Session

from adapters.interfaces import LLMClient
from config import settings
from db.models import Article, Topic, DailyTrendSummary

logger = logging.getLogger(__name__)


def create_system_prompt_for_topic_summary(topic: str):
    return f"""You will be given multiple summaries of different articles. Combine them all into one single concise paragraph. 
    Consider these articles as under the topic: {topic}.
    Output only one paragraph.
    Do not give me the summaries of each article."""


def create_system_prompt_for_article_summary(n_sentences: int):
    return f"""
You are a news summarization system.

Rules:
- Be factual and neutral
- No speculation or opinions
- No rhetorical language
- No emojis
- No preambles like "This article discusses"
- Maximum number of sentences: {n_sentences}

Goal:
Help readers understand what happened and why it matters.
""".strip()


def generate_summary(
        text: str,
        llm_client: LLMClient,
        system_prompt: str,
):
    response = llm_client.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    system_prompt
                ),
            },
            {
                "role": "user",
                "content": (
                    text
                ),
            },
        ],
        stream=False,
    )

    return response


def generate_article_summaries(
        session: Session,
        llm_client: LLMClient,
        date: datetime.datetime = None
):
    """
    Generate summaries for articles created after a specific datetime.

    Args:
        session: Database session
        llm_client: LLM client for generating summaries
        date: Datetime to filter articles from. If None, defaults to past 24 hours from now.
              If provided, generates summaries for articles created >= that datetime.
    """
    if date is None:
        # Default: articles from the past 24 hours
        cutoff_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
    else:
        cutoff_datetime = date

    articles = session.query(Article).filter(Article.created >= cutoff_datetime).all()
    logger.info(f"Filtering articles created >= {cutoff_datetime}")
    logger.info(f"Found {len(articles)} articles to summarize")

    for i, article in enumerate(articles):
        logger.info(f"summarising article {i + 1}/{len(articles)}. id: {article.id}, title: {article.title}")

        if not article.text:
            logger.info(f"Skipping article {article.id}: no text found")
            continue

        if article.text and len(article.text.split()) <= settings.MIN_ARTICLE_WORD_COUNT:
            logger.info(f"Skipping article {article.id}: only {len(article.text.split())} words (minimum {settings.MIN_ARTICLE_WORD_COUNT} required)")
            continue

        article.summary = generate_summary(
            f"Summarize the following article. in one sentence\n\n{article.text}",
            llm_client,
            create_system_prompt_for_article_summary(n_sentences=1),
        )
        session.commit()


def generate_daily_summary(
        session: Session,
        llm_client: LLMClient,
        date: datetime.datetime = None
):
    """
    Generate daily topic summaries combining article summaries.

    Args:
        session: Database session
        llm_client: LLM client for generating summaries
        date: Datetime to filter articles from. If None, defaults to past 24 hours from now.
              If provided, generates summaries for articles created >= that datetime.
              The DailyTrendSummary will be tagged with today's date if None, or the date component of the provided datetime.
    """
    if date is None:
        # Default: articles from the past 24 hours
        cutoff_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
        summary_date = datetime.date.today()
    else:
        cutoff_datetime = date
        summary_date = date.date()

    logger.info(f"Generating daily summaries for articles created >= {cutoff_datetime}")

    topics = session.query(Topic).all()
    for i, topic in enumerate(topics):
        logger.info(f"summarising topic {i + 1}/{len(topics)}. id: {topic.id}, title: {topic.name}")

        # Query articles for this topic created after cutoff datetime
        topic_articles = session.query(Article).filter(
            Article.source_topic == topic.name,
            Article.created >= cutoff_datetime
        ).all()

        logger.info(f"{len(topic_articles)} found for topic: {topic.name}")

        if len(topic_articles) == 0:
            logger.info(f"No articles found for topic {topic.name}, skipping")
            continue

        # Filter out articles without summaries
        articles_with_summaries = [a for a in topic_articles if a.summary]
        if len(articles_with_summaries) == 0:
            logger.warning(f"No articles with summaries found for topic {topic.name}, skipping")
            continue

        topic_summaries = " ".join(article.summary for article in articles_with_summaries)
        daily_topic_summary = generate_summary(
            topic_summaries,
            llm_client,
            create_system_prompt_for_topic_summary(topic.name)
        )
        daily_summary = DailyTrendSummary(
            topic=topic,
            summary=daily_topic_summary,
            date=summary_date,
        )
        for article in articles_with_summaries:
            article.daily_trend_summary = daily_summary
        session.add(daily_summary)
        session.commit()
