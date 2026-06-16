from contextlib import contextmanager
import logging
import time
from typing import Any, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base

import config

logger = logging.getLogger(__name__)

engine = create_engine(
    config.settings.DATABASE_CONNECTION_STRING,
    echo=config.settings.DEBUG,
)

if config.settings.DEBUG:
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany) -> None:
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())
        logger.warning("SQL query start")

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany) -> None:
        total = time.perf_counter() - conn.info["query_start_time"].pop()
        logger.warning("SQL query end duration=%.3fs", total)

session_maker_instance = sessionmaker(bind=engine)

Base = declarative_base()


@contextmanager
def get_session() -> Generator[Session, Any, None]:
    db = session_maker_instance()
    try:
        yield db
    finally:
        db.close()


def get_session_dependency():
    with get_session() as db:
        yield db
