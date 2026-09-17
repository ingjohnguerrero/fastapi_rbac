"""AC-NFR-05: JWT_SECRET / DATABASE_URL are not baked into the image."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile"


def test_ac_nfr_05_dockerfile_has_no_secrets():
    text = DOCKERFILE.read_text()
    assert "JWT_SECRET" not in text
    assert "ENV DATABASE_URL" not in text
    assert ".env" not in text


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker missing")
def test_ac_nfr_05_built_image_filesystem():
    info = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if info.returncode != 0:
        pytest.skip("docker daemon not available")
    tag = "fastapi-rbac-nfr-05"
    build = subprocess.run(
        ["docker", "build", "-t", tag, str(ROOT)],
        capture_output=True,
        text=True,
    )
    if build.returncode != 0:
        pytest.skip(f"docker build unavailable: {build.stderr[-500:]}")
    probe = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "sh",
            tag,
            "-c",
            "test ! -f /app/.env && ! grep -R 'JWT_SECRET=' /app 2>/dev/null",
        ],
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
