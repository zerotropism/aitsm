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

# Bootstrap DB + users + sample data (first time only)
PYTHONPATH=. uv run python scripts/bootstrap.py

# Start the server
uv run uvicorn main:app --reload

# Start the MCP server (separate terminal)
PYTHONPATH=. uv run fastmcp dev mcp/server.py
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
| `MCP_SYSTEM_USER_ID` | Auto-set by bootstrap — user for MCP actions |

## API overview

| Prefix | Description |
|---|---|
| `/auth` | Register, login (JWT) |
| `/tickets` | Ticket CRUD |
| `/catalog` | Service catalog + request submission |
| `/changes` | Change request workflow |
| `/kb` | Knowledge Base CRUD + semantic search |
| `/ai` | AI features (triage, suggest, deflect, draft, reply) |

## Workflows

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
                                         # agent feedback → updates useful_count / not_relevant_count
```

### AI (human-in-the-loop throughout)

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
  POST  /ai/tickets/{id}/draft-article   # generate KB draft → operator reviews before publish
```

### Service Catalog

```
POST   /catalog                          # create a service item (admin only)
GET    /catalog                          # list active services
GET    /catalog/{id}                     # detail + form_schema

POST   /catalog/{id}/request            # submit a request
         body: {"form_data": {"field": "value"}}
         → auto-creates a pre-filled ticket:
             title             = service.name
             category          = service.category
             priority          = service.default_priority
             service_id        linked for traceability
```

### Change Management

```
POST   /changes                          # create (draft)
POST   /changes/{id}/submit             # draft → review
POST   /changes/{id}/approve            # review → approved  (admin only)
POST   /changes/{id}/reject             # review → rejected  (admin only)
POST   /changes/{id}/done               # approved → done    (admin only)
```

---

### End-to-end example — from user request to KB article

```
1. User searches before opening a ticket
   GET  /ai/deflect?q="VPN not working from home"
   → AI returns 2 KB articles → user finds the answer → no ticket created

2. User opens a ticket anyway
   POST /tickets  {"title": "VPN broken", "description": "…"}
   → ticket created (status: open)

3. AI triage runs automatically
   POST /ai/tickets/{id}/triage
   → category: "Network", priority: "high" suggested → operator validates

4. Operator picks up the ticket
   PATCH /tickets/{id}  {"status": "in_progress", "assignee_id": "…"}
   GET   /ai/tickets/{id}/suggest-kb
   → top-3 KB articles surfaced → operator finds a partial fix in article #2
   POST  /kb/article-2/feedback  {"vote": "useful"}

5. Operator drafts a reply to the user
   POST /ai/tickets/{id}/suggest-reply
   → AI drafts a reply → operator edits and sends

6. Ticket resolved
   PATCH /tickets/{id}  {"status": "resolved", "resolution": "Reinstalled VPN client"}

7. Knowledge loop — new KB article generated
   POST  /ai/tickets/{id}/draft-article
   → AI generates a Markdown draft from the ticket + resolution
   → operator reviews and edits the draft
   PATCH /kb/{draft_id}  {"status": "published"}
   → article indexed in ChromaDB → available for future deflection
```

## MCP server

aitsm exposes an MCP server via FastMCP, usable from any MCP-compatible client
(Claude Desktop, Cursor, custom agents, or the FastMCP CLI).

### Start the server

```bash
PYTHONPATH=. uv run fastmcp dev mcp/server.py
```

### Test with the FastMCP CLI

```bash
# List available tools
PYTHONPATH=. uv run fastmcp list mcp/server.py

# Call a tool directly
PYTHONPATH=. uv run fastmcp call mcp/server.py list_tickets
PYTHONPATH=. uv run fastmcp call mcp/server.py deflect --query "impossible de me connecter au VPN"
```

### Inspect interactively

```bash
PYTHONPATH=. uv run fastmcp inspect mcp/server.py
```

### Claude Desktop configuration

In `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aitsm": {
      "command": "uv",
      "args": ["run", "python", "mcp/server.py"],
      "cwd": "/path/to/aitsm"
    }
  }
}
```

### Available tools

| Tool | Description |
|---|---|
| `create_ticket` | Create a new ITSM ticket |
| `list_tickets` | List tickets with optional filters (status, priority, sla_breached) |
| `get_ticket` | Get full details of a ticket by ID |
| `update_ticket` | Update ticket fields (status, priority, category, resolution, assignee) |
| `add_comment` | Add a comment to a ticket (internal or public) |
| `search_kb` | Semantic search across published KB articles |
| `triage_ticket` | AI triage — auto-fill category and priority on a ticket |
| `suggest_kb_for_ticket` | Suggest top-3 KB articles relevant to a ticket |
| `deflect` | Suggest KB articles from a free-text query (before ticket creation) |
| `suggest_reply` | Draft a reply to send to the requester (agent validates before sending) |
| `draft_kb_article` | Generate a Markdown KB draft from a resolved ticket |

## Notes

- KB articles are indexed in ChromaDB only when `status` is set to `published`
- Archiving an article removes it from ChromaDB (`chroma_id` resets to `null`)
- All AI endpoints return suggestions — the human operator always validates before acting
- `chroma_data/` and `*.db` are local only, not versioned
- Sample data is defined in `sample_data.yml` and loaded via `seed_data.py`