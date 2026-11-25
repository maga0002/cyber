"""Databasekeuze: PostgreSQL als die bereikbaar is, anders SQLite."""
import logging
import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text

db = SQLAlchemy()
log = logging.getLogger(__name__)


def _normalize_pg_url(url: str) -> str:
    # Heroku-achtige URL's beginnen met postgres://, SQLAlchemy wil postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def postgres_bereikbaar(url: str, timeout: int = 3) -> bool:
    try:
        engine = create_engine(url, connect_args={"connect_timeout": timeout})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception as exc:  # noqa: BLE001 - elke fout betekent: terugvallen
        log.warning("PostgreSQL niet bereikbaar (%s), terugvallen op SQLite.", exc)
        return False


def kies_database_uri(instance_path: str) -> tuple[str, str]:
    """Geeft (uri, type) terug, waarbij type 'postgresql' of 'sqlite' is."""
    pg_url = os.environ.get("DATABASE_URL", "").strip()
    if pg_url:
        pg_url = _normalize_pg_url(pg_url)
        if postgres_bereikbaar(pg_url):
            return pg_url, "postgresql"

    sqlite_pad = os.environ.get("SQLITE_PATH") or os.path.join(instance_path, "cyber.db")
    os.makedirs(os.path.dirname(os.path.abspath(sqlite_pad)), exist_ok=True)
    return f"sqlite:///{os.path.abspath(sqlite_pad)}", "sqlite"
