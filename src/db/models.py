import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, DateTime, String, Text, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

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


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    admin = Column(Boolean, default=False, nullable=False)


class Topic(Base):
    __tablename__ = 'topic'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=True)

    feeds = relationship("Feed", back_populates="topic")


article_keyword = Table(
    'article_keyword', Base.metadata,
    Column('article_id', Integer, ForeignKey('article.id'), primary_key=True),
    Column('keyword_id', Integer, ForeignKey('keyword.id'), primary_key=True),
    Column('score', Float, nullable=True),  # YAKE score; lower = more relevant
)


class Keyword(Base):
    __tablename__ = 'keyword'
    id = Column(Integer, primary_key=True)
    text = Column(Text, unique=True, nullable=False)
    blocked = Column(Boolean, default=False, nullable=False)

    articles = relationship("Article", secondary=article_keyword, back_populates="keywords")



class Config(Base):
    __tablename__ = 'config'
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class Article(Base):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)

    title = Column(String, nullable=True)
    url = Column(String, nullable=True)

    feed_url = Column(String, ForeignKey("feed.url"), nullable=False)
    feed = relationship("Feed")

    source_topic = Column(String, nullable=True)  # the topic that the source website gave this article
    author = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    embedding = Column(Vector(384), nullable=True)

    keywords = relationship("Keyword", secondary=article_keyword, back_populates="articles")
