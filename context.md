

You are an expert full-stack engineer. Build a compact IT Help Desk app with a modern UI and clean backend.

* **Frontend:** React + TypeScript (Vite), TailwindCSS + shadcn/ui
* **Backend:** Python FastAPI
* **DB:** SQLite (file-based) via SQLAlchemy
* **Storage:** Files on disk; conversations and tickets in DB
* **AI/RAG:** **NOT implemented**—use **placeholders** that return a canned response.
* Keep the code simple, documented, and ready for future LangChain/RAG integration.

---

# FEATURES

Roles: **admin**, **technician**, **user**

1. **Tickets**

* User: create tickets, view own tickets
* Technician: list unassigned/assigned; claim, change status (`open → in_progress → resolved → closed`); add internal notes
* Admin: full view + assign + reopen

2. **Documents (Admin)**

* Upload/manage files (pdf/docx/txt/md)
* Parse plaintext (basic) and store in DB (no embeddings / vector store yet)
* Files saved on disk (`storage/uploads`)

3. **Chat**

* Start conversation, send message
* **Placeholder** response: echo a friendly canned message and optionally reference parsed document titles (no retrieval or LLM)
* Store all messages (role/timestamp)
* Later you (human) will replace the placeholder with LangChain/RAG

4. **Auth & RBAC**

* Email/password login → JWT
* Seed users:

  * [admin@ex.com](mailto:admin@ex.com) / Admin123! → admin
  * [tech@ex.com](mailto:tech@ex.com) / Tech123! → technician
  * [user@ex.com](mailto:user@ex.com) / User123! → user

---

# MONOREPO STRUCTURE

```
it-helpdesk/
  backend/
    app/
      main.py
      core/          # settings, security, deps
      api/           # routers: auth, users, docs, tickets, chat, files
      models/        # SQLAlchemy
      schemas/       # Pydantic
      services/      # ticket_service, doc_service, chat_service (placeholder)
      repositories/  # db access
      utils/         # text extractors, hashing, jwt
    storage/
      uploads/       # raw files
    data/
      app.db         # auto-created
    .env.example
    requirements.txt
    README.md
  frontend/
    src/
      pages/         # Login, Chat, Tickets, TicketDetail, Docs, Admin
      components/    # ChatUI, TicketList, TicketForm, FileUploader, RoleGuard, Nav
      api/           # axios clients
      hooks/         # useAuth, useTickets, useChat
      store/
      lib/
    index.html
    vite.config.ts
    package.json
    tailwind.config.cjs
    postcss.config.cjs
    README.md
  README.md
```

---

# BACKEND DETAILS

## requirements.txt

```
fastapi
uvicorn[standard]
sqlalchemy
alembic
pydantic
python-dotenv
python-jose[cryptography]
passlib[bcrypt]
python-multipart
pypdf
python-docx
markdown
```

## .env.example

```
APP_ENV=dev
SECRET_KEY=devsecret_change_me
ACCESS_TOKEN_EXPIRE_MINUTES=120
DB_PATH=./data/app.db
UPLOAD_DIR=./storage/uploads
ALLOWED_ORIGINS=http://localhost:5173
```

## Models (SQLAlchemy)

* **User**: id, email, hashed\_password, role(`admin|technician|user`), created\_at
* **Document**: id, filename, filepath, content\_type, size\_bytes, uploaded\_by, uploaded\_at, status(`pending|parsed|failed`)
* **DocumentText**: id, document\_id, text (parsed plaintext), char\_count, created\_at
* **Ticket**: id, created\_by, assigned\_to (nullable), title, description, status(`open|in_progress|resolved|closed`), priority(`low|medium|high`), created\_at, updated\_at
* **TicketNote**: id, ticket\_id, author\_id, body, is\_internal(bool), created\_at
* **Conversation**: id, user\_id, session\_id(uuid), created\_at
* **Message**: id, conversation\_id, role(`user|assistant|system|tool`), content, metadata(json), created\_at

## Routes (FastAPI)

**Auth**

* `POST /api/auth/login` → {access\_token, user}
* `GET /api/auth/me`

**Docs (admin)**

* `POST /api/docs/upload` → save file, parse text → `DocumentText`, mark status=parsed
* `GET /api/docs` → list
* `DELETE /api/docs/{id}`
* `POST /api/docs/reparse/{id}` → re-run text extraction

**Tickets**

* `POST /api/tickets` (user)
* `GET /api/tickets` (role-aware: admin=all; tech=assigned/unassigned tabs; user=mine)
* `GET /api/tickets/{id}` (role-aware visibility)
* `PATCH /api/tickets/{id}` (status/assignee; enforce permissions)
* `POST /api/tickets/{id}/notes`

**Chat**

* `POST /api/chat/start` → {session\_id}
* `POST /api/chat/message` → {session\_id, message}

  * Calls **chat\_service.placeholder\_reply**: returns canned text + (optional) related document filenames (no semantic search)
  * Stores user/assistant messages
* `GET /api/chat/{session_id}/history`

**Files**

* `GET /api/files/{id}` (admin only)

## Placeholders

### `services/chat_service.py`

```python
# PSEUDO (implement fully):
def placeholder_reply(user_id: int, session_id: str, text: str) -> dict:
    """
    Returns a canned response. 
    Optionally surfaces up to 3 recently parsed document filenames to pretend as 'related'.
    NO embeddings, NO LLM. Pure placeholder.
    """
    related = docs_repo.get_recent_filenames(limit=3)
    reply = (
        "🔧 Placeholder response:\n"
        "- I received: \"{msg}\"\n"
        "- I’ll answer from your uploaded docs later.\n"
    ).format(msg=text)
    if related:
        reply += "\nHere are some docs I might use soon:\n" + "\n".join([f"• {f}" for f in related])
    return {"reply": reply, "citations": [{"filename": f} for f in related]}
```

### `services/doc_service.py`

```python
# On upload or reparse:
# - Save file to UPLOAD_DIR
# - Extract plaintext using:
#     - pdf: pypdf
#     - docx: python-docx
#     - md: python-markdown -> strip HTML tags or keep raw text
#     - txt: read as utf-8
# - Store plaintext in DocumentText
# - Mark Document.status = 'parsed'
```

### Ticket transition rules

* User: can create; can edit title/desc before assigned; cannot set to `closed`; can add public notes
* Technician: claim unassigned; forward status; internal notes
* Admin: assign/reopen/close

---

# FRONTEND DETAILS

## Tech

* Vite + React + TypeScript
* Tailwind + shadcn/ui (Buttons, Cards, Tabs, Dialog, Input, Textarea, Badge, Tooltip, Avatar, Dropdown)
* React Router, React Query, axios

## Pages

* **Login**: simple email/password; quick-fill demo buttons
* **Chat**:

  * Sidebar: past sessions, “New Conversation”
  * Main: chat bubbles, **placeholder** assistant replies, chip list for “citations”
* **Tickets**:

  * User: My tickets + Create Ticket
  * Technician: Tabs (Unassigned, Assigned to me, All), claim + status change + internal notes
  * Admin: All tickets, assign/reopen
* **Documents (Admin)**:

  * Drag & drop upload (multi), table with status, re-parse, delete
* **Top Nav**: role badge, avatar menu, logout
* **Styling**: modern, responsive, dark mode

## API Client

* axios instance with baseURL env + bearer token
* React Query hooks: `useAuth`, `useChat`, `useTickets`, `useDocs`

---

# TODO MARKERS (for future LangChain/RAG)

Add clear TODOs so you (human) can upgrade later:

* `services/chat_service.py`: `# TODO: replace placeholder_reply with LangChain+Retriever pipeline`
* `services/doc_service.py`: `# TODO: add embeddings + vector store persistence; connect to retriever`
* `api/chat.py`: `# TODO: stream responses (SSE/WebSocket) once LLM added`
* `frontend/src/api/chat.ts`: `// TODO: streaming handling`
* `frontend/src/pages/Chat.tsx`: `// TODO: show token stream when enabled`

---

# ACCEPTANCE CRITERIA (NOW, WITHOUT RAG)

1. I can log in as admin/tech/user using seeded creds.
2. Admin uploads a PDF/TXT/MD/DOCX; it’s saved to `storage/uploads`, parsed plaintext stored in DB, status becomes `parsed`.
3. User starts a chat, sends a message; assistant returns **placeholder** reply referencing recent documents; messages are persisted and visible via history.
4. User can create a ticket in UI; ticket appears under “My Tickets”.
5. Technician can view Unassigned, claim a ticket, set status to `in_progress`, add an internal note.
6. Admin can view all tickets and assign/reopen.
7. All APIs enforce JWT + role checks; CORS works from `http://localhost:5173`.

---

# SEED DATA

* Create 3 users on startup with passwords above.
* Optionally insert an example doc (tiny txt) and a demo ticket for each user.

---

# STARTER SNIPPETS (GENERATE FULL CODE)

## Backend: `app/main.py` (skeleton)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api import auth, docs, tickets, chat, files
from .core.db import init_db, seed_demo

app = FastAPI(title="IT Helpdesk (Placeholder AI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    seed_demo()

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(docs.router, prefix="/api/docs", tags=["docs"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
```

## Backend: `app/services/chat_service.py` (placeholder)

```python
from datetime import datetime
from . import ticket_service
from ..repositories import docs_repo, messages_repo

def placeholder_reply(user_id:int, session_id:str, text:str):
    recent = docs_repo.get_recent_filenames(3)
    reply = (
        "🔧 Placeholder response\n"
        f"• You said: “{text}”\n"
        "• I’ll use your uploaded documents to answer once RAG is connected.\n"
    )
    if recent:
        reply += "• Potential sources:\n" + "\n".join([f"  - {f}" for f in recent])
    return {"reply": reply, "citations": [{"filename": f} for f in recent]}
```

## Frontend: Chat (skeleton)

* Send message → show assistant’s placeholder reply
* Show small chips for `citations` filenames

---

# RUN SCRIPTS

Backend:

* `pip install -r requirements.txt`
* `uvicorn app.main:app --reload --port 8000`

Frontend:

* `npm i`
* `npm run dev` (5173)

---

# DELIVERABLES

* Full working app with placeholders for AI/RAG
* Clean code, comments, and clear TODOs for upgrading to LangChain/LangGraph later

**Generate the complete codebase now.**
