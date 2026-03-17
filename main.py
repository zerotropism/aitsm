from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import Base, engine
from models import kb_article, ticket, user  # noqa: F401
from routers import auth, kb, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="aitsm", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(kb.router, prefix="/kb", tags=["kb"])


@app.get("/health")
def health():
    return {"status": "ok"}
