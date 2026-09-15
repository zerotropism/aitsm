"""Test environment: isolated SQLite file, fixed secret, no network (no Chroma, no LLM)."""

import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_aitsm.db"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes-long"
os.environ["CHROMA_PATH"] = "./test_chroma"

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    import aitsm.models  # noqa: F401
    from aitsm.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    Path("test_aitsm.db").unlink(missing_ok=True)
