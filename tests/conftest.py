"""Test environment: isolated SQLite file, fixed secret, no network (no Chroma, no LLM)."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///./test_aitsm.db"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes-long"
os.environ["CHROMA_PATH"] = "./test_chroma"

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    from core.database import Base, engine
    from models import (  # noqa: F401
        change,
        kb_article,
        kb_feedback,
        service_catalog,
        ticket,
        ticket_comment,
        user,
    )

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    Path("test_aitsm.db").unlink(missing_ok=True)
