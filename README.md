# aitsm

Minimal GenAI-native ITSM built with FastAPI.

## Stack

- **Backend** : FastAPI + SQLAlchemy (SQLite)
- **Vector DB** : ChromaDB (semantic search for KB)
- **LLM** : Internal API (`/v2/llm/invoke`)
- **Auth** : JWT (python-jose + bcrypt)

## Features (MVP v1)

- **Ticket management** — create, read, update, status, priority, assignment, resolution
- **Service catalog** — typed request forms that auto-create pre-filled tickets
- **Change management** — workflow `draft → review → approved → done` (or `rejected`)
- **Knowledge Base** — CRUD + semantic search via ChromaDB (published articles only)
- **AI layer** (human-in-the-loop throughout):
  - Ticket triage — automatic category + priority suggestion
  - KB suggestion — top-3 articles from an existing ticket
  - Ticket deflection — suggest KB articles before a ticket is submitted
  - Draft KB article — generate a Markdown article from a resolved ticket
  - Suggested reply — draft a response to send to the requester

## Project structure

```
├── core/ # Config, DB engine, JWT, LLM client
├── models/ # SQLAlchemy ORM models
├── routers/ # FastAPI routers (one per domain)
├── schemas/ # Pydantic schemas (API in/out)
├── scripts/ # Utility scripts (seed_admin.py)
├── services/ # Business logic
└── vector/ # ChromaDB client
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
| `LLM_WORKSPACE_ID` | Workspace ID (optional) |
| `CHROMA_PATH` | ChromaDB persistence directory |

## API overview

| Prefix | Description |
|---|---|
| `/auth` | Register, login (JWT) |
| `/tickets` | Ticket CRUD |
| `/catalog` | Service catalog + request submission |
| `/changes` | Change request workflow |
| `/kb` | Knowledge Base CRUD + semantic search |
| `/ai` | AI features (triage, suggest, deflect, draft, reply) |

## AI workflow

```
Before submitting a ticket
  → GET  /ai/deflect?q=...                  # suggest KB articles from free text

New ticket created
  → POST /ai/tickets/{id}/triage            # auto category + priority
  → GET  /ai/tickets/{id}/suggest-kb        # top-3 KB articles for the agent

During resolution
  → POST /ai/tickets/{id}/suggest-reply     # draft a reply for the agent to validate

Ticket resolved
  → PATCH /tickets/{id}                     # set resolution field
  → POST  /ai/tickets/{id}/draft-article    # generate KB draft (agent reviews before publish)
```

## Change worklow

POST /changes                    # create (draft)
POST /changes/{id}/submit        # draft → review
POST /changes/{id}/approve       # review → approved  (admin only)
POST /changes/{id}/reject        # review → rejected  (admin only)
POST /changes/{id}/done          # approved → done    (admin only)

## Notes

- KB articles are indexed in ChromaDB only when `status` is set to `published`
- Archiving an article removes it from ChromaDB (`chroma_id` resets to `null`)
- All AI endpoints return suggestions — the human agent always validates before acting
- `chroma_data/` and `*.db` are local only, not versioned