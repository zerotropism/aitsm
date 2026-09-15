from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from aitsm.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for every model. Tables register themselves on import."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
