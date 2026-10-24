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

# Load environment variables from .env file
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)


def normalize_database_url(raw_url: str) -> str:
    """
    Ensure passwords with special characters (e.g. '@', ':', '#') are safely URL-encoded
    for SQLAlchemy without exposing credentials in logs.
    """
    if not raw_url or not raw_url.startswith("mysql"):
        return raw_url

    prefix, sep, rest = raw_url.partition("://")
    if not sep or "@" not in rest:
        return raw_url

    # Split from the rightmost '@' so host:port/db is cleanly isolated
    user_info, at_sep, host_info = rest.rpartition("@")
    if ":" in user_info:
        username, col_sep, password = user_info.partition(":")
        # URL-encode the password safely
        safe_password = urllib.parse.quote(urllib.parse.unquote(password), safe="")
        return f"{prefix}://{username}:{safe_password}@{host_info}"
    return raw_url


RAW_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/venturemind")
DATABASE_URL = normalize_database_url(RAW_DATABASE_URL)


def ensure_database_exists(db_url: str):
    """
    Ensure the target MySQL database exists without dropping or overwriting existing data.
    """
    if not db_url.startswith("mysql"):
        return

    url_obj = make_url(db_url)
    db_name = url_obj.database
    if not db_name:
        return

    import pymysql

    # Connect to MySQL server root instance without database specified
    connection = pymysql.connect(
        host=url_obj.host or "localhost",
        port=url_obj.port or 3306,
        user=url_obj.username or "root",
        password=url_obj.password or "",
        charset="utf8mb4"
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}';")
            existing = cursor.fetchone()
            if not existing:
                cursor.execute(
                    f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
                connection.commit()
    finally:
        connection.close()


# Create SQLAlchemy engine with connection pooling
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides an independent database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize MySQL database tables safely without destroying existing data."""
    if DATABASE_URL.startswith("mysql"):
        ensure_database_exists(DATABASE_URL)

    # Import models so Base registers metadata
    try:
        import backend.models.startup     # noqa: F401
        import backend.models.chat        # noqa: F401
        import backend.models.validation  # noqa: F401
    except ImportError:
        import models.startup      # noqa: F401
        import models.chat         # noqa: F401
        import models.validation   # noqa: F401

    Base.metadata.create_all(bind=engine)
