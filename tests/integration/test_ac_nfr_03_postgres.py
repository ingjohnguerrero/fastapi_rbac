"""AC-NFR-03: same app against PostgreSQL via DATABASE_URL (skip if no Docker)."""

import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.adapters.db import reset_engine
from app.cli import run_init
from app.main import app
from app.settings import Settings, clear_settings_cache

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker missing")

ROOT = Path(__file__).resolve().parents[2]
SECRET = "postgres-nfr-secret"
ADMIN_PASSWORD = "pg-admin-pass"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _docker_ok() -> bool:
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def test_ac_nfr_03_postgres_login(monkeypatch):
    if not _docker_ok():
        pytest.skip("docker daemon not available")

    port = _free_port()
    name = f"fastapi-rbac-pg-{port}"
    run = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            name,
            "-e",
            "POSTGRES_USER=rbac",
            "-e",
            "POSTGRES_PASSWORD=rbac",
            "-e",
            "POSTGRES_DB=rbac",
            "-p",
            f"127.0.0.1:{port}:5432",
            "postgres:16",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if run.returncode != 0:
        pytest.skip(f"could not start postgres: {run.stderr}")

    url = f"postgresql+psycopg://rbac:rbac@127.0.0.1:{port}/rbac"
    cfg = Settings(
        jwt_secret=SECRET,
        database_url=url,
        admin_username="admin",
        admin_email="admin@example.com",
        admin_password=ADMIN_PASSWORD,
        _env_file=None,
    )
    try:
        ready = False
        deadline = time.time() + 40
        while time.time() < deadline:
            reset_engine()
            try:
                if run_init(cfg) == 0:
                    ready = True
                    break
            except OperationalError:
                pass
            time.sleep(1)
        if not ready:
            pytest.skip("postgres never became ready")

        monkeypatch.setenv("JWT_SECRET", SECRET)
        monkeypatch.setenv("DATABASE_URL", url)
        clear_settings_cache()
        from app.adapters.db import configure_engine

        configure_engine(cfg)
        client = TestClient(app)
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": ADMIN_PASSWORD},
        )
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        reset_engine()
        clear_settings_cache()
