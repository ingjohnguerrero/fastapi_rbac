"""Terminal init: schema, catalog, first admin. Does not require uvicorn."""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

try:
    from pydantic import ValidationError
    from sqlalchemy.orm import Session

    from app.adapters.db import configure_engine, create_schema, get_engine
    from app.services.seed import admin_exists, create_first_admin, seed_catalog
    from app.settings import Settings, clear_settings_cache
except ModuleNotFoundError:
    print(
        "error: Python dependencies are not installed for this interpreter "
        f"({sys.executable}).",
        file=sys.stderr,
    )
    print(
        "Run ./scripts/init.sh (creates .venv and installs requirements.txt), or:",
        file=sys.stderr,
    )
    print(
        "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt "
        "&& .venv/bin/python -m app.cli init",
        file=sys.stderr,
    )
    raise SystemExit(1) from None


def _redact_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.password:
        netloc = parsed.netloc.replace(f":{parsed.password}", ":***")
        return parsed._replace(netloc=netloc).geturl()
    return url


def run_init(settings: Settings | None = None) -> int:
    try:
        cfg = settings or Settings(_env_file=".env")
    except ValidationError:
        print("error: JWT_SECRET is required", file=sys.stderr)
        return 1

    if not cfg.jwt_secret:
        print("error: JWT_SECRET is required", file=sys.stderr)
        return 1

    try:
        engine = configure_engine(cfg)
        create_schema(engine)
    except Exception as exc:
        print(f"error: cannot reach store: {exc}", file=sys.stderr)
        return 1

    session = Session(get_engine())
    try:
        seed_catalog(session)
        if admin_exists(session):
            session.commit()
            print(f"store: {_redact_url(cfg.database_url)}")
            print("init: admin already exists; skipped (password unchanged)")
            print("hint: unset ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD; they are not needed at runtime")
            return 0
        if not cfg.admin_username or not cfg.admin_email or not cfg.admin_password:
            print("error: ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD are required for first admin", file=sys.stderr)
            session.rollback()
            return 1
        create_first_admin(
            session,
            username=cfg.admin_username,
            email=cfg.admin_email,
            password=cfg.admin_password,
        )
        session.commit()
        print(f"store: {_redact_url(cfg.database_url)}")
        print("init: first administrator created")
        print("hint: remove ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD from .env after first setup")
        return 0
    except Exception as exc:
        session.rollback()
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create schema, seed catalog, insert first admin")
    args = parser.parse_args(argv)
    if args.command == "init":
        clear_settings_cache()
        return run_init()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
