"""SQLAlchemy engine and session factory from DATABASE_URL."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.entities import Base
from app.settings import Settings, get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def configure_engine(settings: Settings | None = None) -> Engine:
    global _engine, _SessionLocal
    cfg = settings or get_settings()
    _engine = create_engine(
        cfg.database_url,
        connect_args=_sqlite_connect_args(cfg.database_url),
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        return configure_engine()
    return _engine


def create_schema(engine: Engine | None = None) -> None:
    eng = engine or get_engine()
    Base.metadata.create_all(eng)


def reset_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        configure_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def listen_before_cursor(engine: Engine, callback) -> None:
    event.listen(engine, "before_cursor_execute", callback)


def remove_before_cursor(engine: Engine, callback) -> None:
    event.remove(engine, "before_cursor_execute", callback)
