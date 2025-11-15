from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, Text, JSON, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

engine = create_engine("sqlite:///../test.sqlite")
Session = sessionmaker(bind=engine)

Base = declarative_base()


class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    subreddit_id = Column(Integer, ForeignKey("subreddit.id"), nullable=False)
    subreddit = relationship("Subreddit", back_populates="posts")

    daily_trend_summary_id = Column(Integer, ForeignKey("daily_trend_summary.id"), nullable=True)
    daily_trend_summary = relationship("DailyTrendSummary", back_populates=...)

    comments = relationship("Comment", cascade="all, delete", order_by="Comment.id")

    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    author = Column(String, nullable=True)
    score = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    num_comments = Column(Integer, nullable=False)
    created = Column(DateTime, nullable=False)
    sentiment = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)


class Subreddit(Base):
    __tablename__ = 'subreddit'

    posts = relationship("Post", cascade="all, delete", order_by="Post.id")

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    subscribers = Column(Integer, nullable=False)
    category = Column(String, nullable=True)
    created = Column(DateTime, nullable=False)


class Comment(Base):
    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True)

    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    post = relationship("Post", back_populates="comments")

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
    dominant_topics = Column(JSON, nullable=True)
    predicted_trends = Column(JSON, nullable=True)


Base.metadata.create_all(engine)
