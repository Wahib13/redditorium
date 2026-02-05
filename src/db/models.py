import datetime

from sqlalchemy import Column, Integer, DateTime, String, Text, JSON, ForeignKey, Date, Table
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SAEnum
from enum import Enum

from db.connection import Base


class Feed(Base):
    __tablename__ = 'feed'
    url = Column(String, primary_key=True)
    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    source = relationship("Source")

    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=False)
    topic = relationship("Topic", back_populates="feeds")


class Source(Base):
    __tablename__ = 'source'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    feeds = relationship("Feed", back_populates="source")

    articles = relationship("Article", back_populates="source")


article_topic = Table(
    "article_topic",
    Base.metadata,
    Column("article_id", ForeignKey("article.id"), primary_key=True),
    Column("topic_id", ForeignKey("topic.id"), primary_key=True),
)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)


class Topic(Base):
    __tablename__ = 'topic'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=True)

    articles = relationship("Article", secondary=article_topic, back_populates="topics")
    feeds = relationship("Feed", back_populates="topic")


class Article(Base):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)

    daily_trend_summary_id = Column(Integer, ForeignKey("daily_trend_summary.id"), nullable=True)
    daily_trend_summary = relationship("DailyTrendSummary", back_populates="articles")

    comments = relationship("Comment", cascade="all, delete", order_by="Comment.id")

    title = Column(String, nullable=True)
    url = Column(String, nullable=True)

    source_id = Column(Integer, ForeignKey("source.id"), nullable=False)
    source = relationship("Source")

    source_topic = Column(String, nullable=True)  # the topic that the source website gave this article. nullable because some sources may not have it.
    author = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    topics = relationship("Topic", secondary=article_topic, back_populates="articles")


class Comment(Base):
    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True)

    article_id = Column(Integer, ForeignKey("article.id"), nullable=False)
    article = relationship("Article", back_populates="comments")

    author = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    created = Column(DateTime, nullable=False)
    sentiment = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)


class DailyTrendSummary(Base):
    __tablename__ = 'daily_trend_summary'

    id = Column(Integer, primary_key=True)

    date = Column(Date, nullable=False)
    summary = Column(Text, nullable=True)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=False)
    topic = relationship("Topic")

    articles = relationship("Article", back_populates="daily_trend_summary")
