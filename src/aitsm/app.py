from contextlib import asynccontextmanager

from fastapi import FastAPI

import aitsm.models  # noqa: F401  - registers every table on Base.metadata
from aitsm.core.database import Base, engine
from aitsm.routers import ai, auth, catalog, changes, kb, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="aitsm", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(kb.router, prefix="/kb", tags=["kb"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
app.include_router(changes.router, prefix="/changes", tags=["changes"])


@app.get("/health")
def health():
    return {"status": "ok"}


def main() -> None:
    """Console entry point: serve the API with uvicorn."""
    import os

    import uvicorn

    uvicorn.run(
        "aitsm.app:app",
        host=os.getenv("AITSM_HOST", "127.0.0.1"),
        port=int(os.getenv("AITSM_PORT", "8000")),
    )
