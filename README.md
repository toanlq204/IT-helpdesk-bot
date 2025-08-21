# IT Helpdesk Application

A modern IT helpdesk application with role-based access control, ticket management, document management, and AI chat capabilities (placeholder implementation ready for RAG integration).

## Features

- **Authentication & Authorization**: JWT-based auth with role-based permissions (admin, technician, user)
- **Ticket Management**: Create, assign, and track IT support tickets with status transitions
- **Document Management**: Upload and parse documents (PDF, DOCX, TXT, MD) for knowledge base
- **AI Chat Assistant**: Placeholder chat service ready for LangChain/RAG integration
- **Modern UI**: React TypeScript frontend with TailwindCSS and shadcn/ui components

## Architecture

- **Frontend**: React + TypeScript + Vite + TailwindCSS + shadcn/ui
- **Backend**: Python FastAPI with SQLAlchemy ORM
- **Database**: SQLite (file-based)
- **Storage**: Local file system for document uploads

## Quick Start

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Run the application:
```bash
uvicorn app.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Demo Accounts

The application comes with pre-seeded demo accounts:

- **Admin**: `admin@ex.com` / `Admin123!`
- **Technician**: `tech@ex.com` / `Tech123!`
- **User**: `user@ex.com` / `User123!`

## API Documentation

Once the backend is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Role Permissions

### User
- Create tickets
- View own tickets
- Edit own unassigned tickets
- Add public notes to tickets
- Use chat assistant

### Technician
- All user permissions
- View unassigned and assigned tickets
- Claim unassigned tickets
- Update ticket status (except close)
- Add internal notes

### Admin
- All permissions
- View all tickets
- Assign/reassign tickets
- Close/reopen tickets
- Upload and manage documents
- Access document management interface

## Development

### Backend Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core configuration and database
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API route handlers
│   ├── services/            # Business logic services
│   ├── repositories/        # Data access layer
│   └── utils/               # Utility functions
├── data/                    # SQLite database location
├── storage/uploads/         # Uploaded files
└── requirements.txt
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   ├── pages/               # Page components
│   ├── api/                 # API client functions
│   ├── hooks/               # Custom React hooks
│   ├── store/               # State management (Zustand)
│   └── lib/                 # Utility functions
├── public/
└── package.json
```

## Future Enhancements (TODOs)

The application is designed with clear TODO markers for future AI/RAG integration:

- **Backend TODOs**:
  - `services/chat_service.py`: Replace placeholder with LangChain+Retriever pipeline
  - `services/document_parser.py`: Add embeddings + vector store persistence
  - `api/chat.py`: Add streaming responses (SSE/WebSocket)

- **Frontend TODOs**:
  - `api/chat.ts`: Add streaming handling
  - `pages/Chat.tsx`: Show token stream when enabled

## License

This project is for demonstration purposes.
