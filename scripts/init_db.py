import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, engine

Base.metadata.create_all(bind=engine)
print("Database tables created.")
