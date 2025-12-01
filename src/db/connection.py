from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

import config

engine = create_engine(config.DATABASE_CONNECTION_STRING)
session_maker_instance = sessionmaker(bind=engine)

Base = declarative_base()


@contextmanager
def get_session() -> Session:
    db = session_maker_instance()
    try:
        yield db
    finally:
        db.close()
