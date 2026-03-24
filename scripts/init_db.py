import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    user,
    ticket,
    kb_article,
    service_catalog,
    change,
    ticket_comment,
    kb_feedback,
)  # noqa
from core.database import Base, engine

Base.metadata.create_all(bind=engine)
print("Database tables created.")
