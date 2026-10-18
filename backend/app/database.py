import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL


def build_database_url(raw_url: str) -> URL:
    """Normalize the connection URL without corrupting existing TLS query options."""
    url = make_url(raw_url)
    if url.get_backend_name() != "sqlite" and "charset" not in url.query:
        url = url.set(query={**dict(url.query), "charset": "utf8mb4"})
    return url


SQLALCHEMY_DATABASE_URL = build_database_url(DATABASE_URL)

connect_args = {}
if SQLALCHEMY_DATABASE_URL.get_backend_name() == "sqlite":
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"connect_timeout": 10}

engine_options = {
    "echo": os.getenv("SQL_ECHO", "0") == "1",
    "connect_args": connect_args,
    "pool_pre_ping": True,
}
if SQLALCHEMY_DATABASE_URL.get_backend_name() != "sqlite":
    # TiDB Cloud Starter may close idle connections. Recycle before that happens
    # and keep the Render Free instance's connection count small.
    engine_options.update(
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "240")),
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "5")),
    )

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
