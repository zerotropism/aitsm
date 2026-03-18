# aitsm

Minimal GenAI-native ITSM built with FastAPI.

## Stack

- **Backend** : FastAPI + SQLAlchemy (SQLite)
- **Vector DB** : ChromaDB (semantic search for KB)
- **LLM** : Internal API (`/v2/llm/invoke`)
- **Auth** : JWT (python-jose + bcrypt)

## Features (MVP v1)

- Ticket management (create, read, update, status, priority, assignment)
- Knowledge Base (CRUD + semantic search via ChromaDB)
- AI layer:
  - Automatic ticket triage (category + priority)
  - KB article suggestions from a ticket
  - Draft KB article generation from a resolved ticket (human-in-the-loop)

## Project structure

```
├── core/       # Config, DB engine, JWT, LLM client
├── models/     # SQLAlchemy ORM models
├── schemas/    # Pydantic schemas (API in/out)
├── routers/    # FastAPI routers (one per domain)
├── services/   # Business logic
└── vector/     # ChromaDB client
```

## Getting started

**Requirements** : Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your values (LLM API key, secret key…)

# Start the server
uv run uvicorn main:app --reload
```

API available at [localhost:8000](http://localhost:8000)  
Interactive docs at [localhost:8000/docs](http://localhost:8000/docs)

## Environment variables

See `.env.example` for the full list. Required:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key |
| `LLM_API_URL` | LLM endpoint URL |
| `LLM_API_KEY` | LLM API key |
| `LLM_MODEL_NAME` | Model identifier |
| `LLM_PROVIDER` | Model provider (e.g. `bedrock`) |

## AI workflow

```
New ticket
  → POST /ai/tickets/{id}/triage        # auto category + priority
  → GET  /ai/tickets/{id}/suggest-kb    # top-3 KB articles

Resolved ticket
  → PATCH /tickets/{id}                 # set resolution field
  → POST /ai/tickets/{id}/draft-article # generate KB draft (agent reviews before publish)
```

## Notes

- KB articles are indexed in ChromaDB only when `status` is set to `published`
- The AI always produces suggestions — the agent validates before any action (human-in-the-loop)
- `chroma_data/` and `*.db` are local only, not versioned