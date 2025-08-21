from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api import auth, docs, tickets, chat, files
from .core.database import init_db, seed_demo

app = FastAPI(title="IT Helpdesk (Placeholder AI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()
    seed_demo()

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(docs.router, prefix="/api/docs", tags=["docs"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/files", tags=["files"])

@app.get("/")
async def root():
    return {"message": "IT Helpdesk API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
