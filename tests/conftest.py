"""Test environment: throwaway data directory, fixed secret, no LLM."""

import os
import shutil
import tempfile
from pathlib import Path

_DATA_DIR = Path(tempfile.mkdtemp(prefix="aitsm-tests-"))

os.environ["DATABASE_URL"] = f"sqlite:///{_DATA_DIR / 'aitsm.db'}"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes-long"
os.environ["CHROMA_PATH"] = str(_DATA_DIR / "chroma")

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    import aitsm.models  # noqa: F401
    from aitsm.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    shutil.rmtree(_DATA_DIR, ignore_errors=True)
