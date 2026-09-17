# aitsm

Minimal GenAI-native ITSM built with FastAPI: tickets, a service catalog, change requests, a
knowledge base with semantic search, and an AI layer that suggests rather than decides. Exposed
both as a REST API and as an MCP server, so an agent can work the same tickets a human does.

## Stack

- **Backend** — FastAPI + SQLAlchemy 2.0 (SQLite)
- **Vector DB** — ChromaDB, embedded, for KB semantic search
- **LLM** — Ollama by default; a hosted gateway backend is available
- **Auth** — JWT (PyJWT + bcrypt)
- **MCP** — FastMCP 4

## Features

- **Ticket management** — create, read, update, status, priority, assignment, resolution
- **Service catalog** — typed request forms that auto-create pre-filled tickets
- **Change management** — workflow `draft → review → approved → done` (or `rejected`)
- **Knowledge Base** — CRUD + semantic search (published articles only)
- **AI layer**, human-in-the-loop throughout:
  - Ticket triage — category and priority suggestion
  - KB suggestion — top-3 articles for an existing ticket
  - Ticket deflection — suggest KB articles before a ticket is submitted
  - Draft KB article — a Markdown article from a resolved ticket
  - Suggested reply — a draft response for the operator to validate

## Getting started

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync

cp .env.example .env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env

uv run aitsm-bootstrap     # database, admin, system user, sample data
uv run aitsm-api           # http://localhost:8000/docs
```

The bootstrap creates an admin account and prints a generated password once — copy it. To set
your own: `uv run python -m aitsm.scripts.seed_admin <email> <password>`.

`SECRET_KEY` is required and must be at least 32 characters. There is no default on purpose: a
missing key fails at startup rather than running with a value everyone knows.

For the AI features, Ollama must be running:

```bash
ollama pull llama3.2:3b
```

## Configuration

Everything lives in `.env`. Only `SECRET_KEY` is required; the rest has working defaults.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | JWT signing key, **required**, 32 characters minimum |
| `LLM_BACKEND` | `ollama` | `ollama` (local) or `gateway` (hosted) |
| `LLM_TIMEOUT` | `60` | Seconds before a model call is abandoned |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama backend |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama backend |
| `LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL_NAME`, `LLM_PROVIDER`, `LLM_WORKSPACE_ID` | — | Gateway backend |
| `MCP_SYSTEM_USER_ID` | — | Written by the bootstrap; the user MCP actions act as |
| `DATABASE_URL`, `CHROMA_PATH` | project root | Set these only to move the data elsewhere |

`DATABASE_URL` and `CHROMA_PATH` default to absolute paths under the project root. Leave them
commented out: a relative path silently gives you a different database depending on the
directory a command was launched from.

### Adding a model backend

`core/llm.py` defines an `LLM` protocol with one method. `OllamaLLM` and `GatewayLLM` implement
it; `get_llm()` picks one from `LLM_BACKEND`. A third backend is a class and a branch.

## Project structure

```
src/aitsm/
├── core/          config, DB engine, JWT, LLM backends
├── models/        SQLAlchemy models — importing the package registers every table
├── schemas/       Pydantic schemas (API in/out)
├── routers/       FastAPI routers, one per domain
├── services/      business logic
├── vector/        ChromaDB client
├── mcp_server/    MCP server
├── scripts/       bootstrap and seeding
├── paths.py       every filesystem location, resolved from the project root
└── app.py         FastAPI application
```

The package is named `mcp_server`, not `mcp`: a top-level `mcp` package shadows the official MCP
SDK depending on `sys.path`, and `import mcp` then resolves to the wrong thing.

## API overview

| Prefix | Description |
|---|---|
| `/auth` | Register, login (JWT) |
| `/tickets` | Ticket CRUD |
| `/catalog` | Service catalog + request submission |
| `/changes` | Change request workflow |
| `/kb` | Knowledge Base CRUD + semantic search |
| `/ai` | AI features (triage, suggest, deflect, draft, reply) |

### Tickets

```
POST   /tickets                          # create (status: open)
PATCH  /tickets/{id}                     # update fields (status, priority, assignee…)

status lifecycle:
  open → in_progress → resolved → closed

POST   /tickets/{id}/comments            # add comment (internal or public)
GET    /tickets/{id}/comments            # list comments (chronological)

GET    /tickets                          # list with filters:
         ?status=open|in_progress|resolved|closed
         ?priority=low|medium|high|critical
         ?sla_breached=true              # tickets past their SLA deadline
```

### Knowledge Base

```
POST   /kb                               # create article (draft)
PATCH  /kb/{id}  {"status": "published"} # publish → indexes in ChromaDB
PATCH  /kb/{id}  {"status": "archived"}  # archive → removes from ChromaDB

GET    /kb/search?q=...                  # semantic search (published articles only)

POST   /kb/{id}/feedback  {"vote": "useful"|"not_relevant"}
```

### AI

```
Before submitting a ticket
  GET  /ai/deflect?q=...                 # suggest KB articles from free text

New ticket created
  POST /ai/tickets/{id}/triage           # auto category + priority suggestion
  GET  /ai/tickets/{id}/suggest-kb       # top-3 KB articles for the operator

During resolution
  POST /ai/tickets/{id}/suggest-reply    # draft a reply for the operator to validate

Ticket resolved
  PATCH /tickets/{id}                    # set resolution field
  POST  /ai/tickets/{id}/draft-article   # generate KB draft → operator reviews
```

### Service Catalog

```
POST   /catalog                          # create a service item (admin only)
GET    /catalog                          # list active services
GET    /catalog/{id}                     # detail + form_schema

POST   /catalog/{id}/request             # submit a request
         body: {"form_data": {"field": "value"}}
         → auto-creates a pre-filled ticket
```

### Change Management

```
POST   /changes                          # create (draft)
POST   /changes/{id}/submit              # draft → review
POST   /changes/{id}/approve             # review → approved  (admin only)
POST   /changes/{id}/reject              # review → rejected  (admin only)
POST   /changes/{id}/done                # approved → done    (admin only)
```

## End-to-end example — from user request to KB article

```
1. User searches before opening a ticket
   GET  /ai/deflect?q="VPN not working from home"
   → AI returns 2 KB articles → user finds the answer → no ticket created

2. User opens a ticket anyway
   POST /tickets  {"title": "VPN broken", "description": "…"}

3. AI triage runs
   POST /ai/tickets/{id}/triage
   → category "Network", priority "high" suggested → operator validates

4. Operator picks up the ticket
   PATCH /tickets/{id}  {"status": "in_progress", "assignee_id": "…"}
   GET   /ai/tickets/{id}/suggest-kb
   POST  /kb/article-2/feedback  {"vote": "useful"}

5. Operator drafts a reply
   POST /ai/tickets/{id}/suggest-reply

6. Ticket resolved
   PATCH /tickets/{id}  {"status": "resolved", "resolution": "Reinstalled VPN client"}

7. Knowledge loop
   POST  /ai/tickets/{id}/draft-article
   PATCH /kb/{draft_id}  {"status": "published"}
   → indexed in ChromaDB → available for future deflection
```

## MCP server

The same domain, exposed to any MCP-compatible client.

```bash
uv run aitsm-mcp            # stdio
```

Inspect it with [mcp-servers-cli](https://github.com/zerotropism/mcp-servers-cli):

```bash
uvx mcp-servers-cli inspect --stdio "uv run --directory /path/to/aitsm aitsm-mcp"
uvx mcp-servers-cli call list_tickets '{}' --stdio "uv run --directory /path/to/aitsm aitsm-mcp"
```

### Claude Desktop

```json
{
  "mcpServers": {
    "aitsm": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/aitsm", "aitsm-mcp"]
    }
  }
}
```

### Available tools

| Tool | Description |
|---|---|
| `create_ticket` | Create a new ITSM ticket |
| `list_tickets` | List tickets, optionally filtered by status, priority or SLA |
| `get_ticket` | Get full details of a ticket by ID |
| `update_ticket` | Update status, priority, category, resolution or assignee |
| `add_comment` | Add a comment to a ticket (internal or public) |
| `search_kb` | Semantic search across published KB articles |
| `triage_ticket` | AI triage — fill in category and priority |
| `suggest_kb_for_ticket` | Top-3 KB articles relevant to a ticket |
| `deflect` | Suggest KB articles from a free-text query |
| `suggest_reply` | Draft a reply for the requester |
| `draft_kb_article` | Generate a Markdown KB draft from a resolved ticket |

Every filter is optional. A failed call raises an MCP error carrying its message — no tool
returns `{"error": ...}` as a successful result, which a model would have to notice on its own.

## Tests

```bash
uv run pytest
```

No LLM needed. The search scoring test embeds text, so its first run downloads Chroma's
embedding model (see Notes). The tests exercise the JWT round trip, the API auth flow, the MCP
server through an in-memory client, the search scoring on a temporary index, and that every
declared console entry point actually resolves.

## Notes

- KB articles are indexed only when `status` is `published`; archiving removes them from the index
- Semantic search returns a `score` where higher is better, alongside the raw Chroma `distance`
- The embedding function is Chroma's default, all-MiniLM-L6-v2 in ONNX: no `torch`, but the model
  is downloaded once into `~/.cache/chroma/onnx_models`, so the first indexing needs network access
- Every AI endpoint returns a suggestion — the operator validates before anything is applied
- `chroma_data/`, `*.db` and `.env` are local only, never versioned
- Sample data lives in `data/sample_data.yml`
