import logging

import os

HACKER_NEWS_BASE_URL = os.environ.get("HACKER_NEWS_BASE_URL")
DATABASE_CONNECTION_STRING = os.environ.get("DATABASE_CONNECTION_STRING")


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
