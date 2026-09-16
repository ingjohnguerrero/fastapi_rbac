"""AC-FR-33: no Gherkin / Behave / Cucumber / pytest-bdd in v0.1."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


_SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}


def _keep(path: Path) -> bool:
    return not any(part in _SKIP_PARTS for part in path.parts)


def test_ac_fr_33_no_feature_files():
    features = [p for p in ROOT.rglob("*.feature") if _keep(p)]
    assert features == []
    forbidden = {"behave.ini", "cucumber.yml"}
    names = {p.name.lower() for p in ROOT.rglob("*") if p.is_file() and _keep(p)}
    assert names.isdisjoint(forbidden)
    for path in ROOT.rglob("*"):
        if _keep(path) and path.is_file() and "pytest-bdd" in path.name.lower():
            raise AssertionError(f"pytest-bdd artifact present: {path}")
