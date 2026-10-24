
import os
import sys
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

current_dir = Path(__file__).resolve().parent.parent
parent_dir = current_dir.parent

for p in [str(current_dir), str(parent_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load local .env when available; Vercel uses environment variables.
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)


def normalize_database_url(raw_url: str) -> str:
    """Safely encode the password portion of a MySQL URL."""
    if not raw_url or not raw_url.startswith("mysql"):
        return raw_url

    prefix, sep, rest = raw_url.partition("://")
    if not sep or "@" not in rest:
        return raw_url

    user_info, _, host_info = rest.rpartition("@")
    if ":" in user_info:
        username, _, password = user_info.partition(":")
        safe_password = urllib.parse.quote(
            urllib.parse.unquote(password), safe=""
        )
        return f"{prefix}://{username}:{safe_password}@{host_info}"

    return raw_url


RAW_DATABASE_URL = os.getenv("DATABASE_URL")

if not RAW_DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Configure it in your deployment environment."
    )

DATABASE_URL = normalize_database_url(RAW_DATABASE_URL)

if DATABASE_URL.startswith("mysql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=2,
        max_overflow=0,
    )
elif DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Provide a database session for a request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create missing tables in the already-existing database."""
    try:
        import backend.models.startup  # noqa: F401
        import backend.models.chat  # noqa: F401
        import backend.models.validation  # noqa: F401
    except ImportError:
        import models.startup  # noqa: F401
        import models.chat  # noqa: F401
        import models.validation  # noqa: F401

    Base.metadata.create_all(bind=engine)
