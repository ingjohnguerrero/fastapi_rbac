"""FR-22 / NFR-08: liveness without token and without a DB ping."""

from fastapi.testclient import TestClient

from app.adapters.db import reset_engine
from app.main import app
from app.settings import clear_settings_cache


def test_ac_fr_22_health_no_token_no_db():
    reset_engine()
    clear_settings_cache()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
