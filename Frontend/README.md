# IT HelpDesk Chatbot

An AI-powered IT HelpDesk chatbot built with React.js, Material-UI, TailwindCSS frontend and Python FastAPI backend with OpenAI integration.

## Features

- **Modern UI**: Clean chat interface with conversation history sidebar
- **File Upload**: Upload files to provide context to the chatbot
- **Multi-turn Conversations**: Persistent conversation history
- **Ticket Management**: Full CRUD operations for IT support tickets
- **OpenAI Integration**: GPT-powered responses with function calling
- **Batch Processing**: Efficient OpenAI API usage
- **Function Calling**: Automatic ticket creation and management

## Tech Stack

### Frontend
- React.js 18
- Material-UI (MUI) 5
- TailwindCSS 3
- Axios for API calls

### Backend
- Python 3.8+
- FastAPI
- OpenAI SDK
- JSON file storage for simplicity

## Project Structure

```
/
├── src/                           # React frontend
│   ├── components/                # React components
│   ├── services/                  # API service layer
│   └── ...
├── backend/                       # Python FastAPI backend
│   ├── models/                    # Pydantic models
│   │   ├── chat_models.py
│   │   └── ticket_models.py
│   ├── services/                  # Business logic services
│   │   ├── ticket_service.py
│   │   ├── conversation_service.py
│   │   ├── file_service.py
│   │   └── openai_service.py
│   ├── routers/                   # FastAPI routers
│   │   ├── chat_router.py
│   │   ├── ticket_router.py
│   │   ├── file_router.py
│   │   └── conversation_router.py
│   ├── venv/                      # Virtual environment (created during setup)
│   ├── main.py                    # Main FastAPI application
│   ├── setup.sh                   # Backend setup script
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment variables template
│   ├── uploads/                   # Uploaded files (created at runtime)
│   ├── conversations/             # Conversation storage (created at runtime)
│   └── data/                      # Application data (created at runtime)
├── public/                        # Static files
└── start.sh                       # Startup script
```

## Setup Instructions

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- OpenAI API key

### Option 1: Quick Start (Recommended)

The easiest way to get started is using the automated setup script:

```bash
./start.sh
```

This script will:
1. Automatically set up the Python virtual environment if needed
2. Install all dependencies
3. Start both frontend and backend servers
4. Open the application at `http://localhost:3000`

### Option 2: Manual Setup

#### Backend Setup

1. **Set up virtual environment and install dependencies:**
```bash
cd backend
./setup.sh
```

Or manually:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. **Run the backend server:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate
python main.py
```
The API will be available at `http://localhost:8000`

#### Frontend Setup

1. **Install Node dependencies:**
```bash
npm install
```

2. **Start the React development server:**
```bash
npm start
```
The application will be available at `http://localhost:3000`

## Usage

### Chat Interface
- Start a new conversation by clicking "New Chat"
- Type messages in the input field
- Upload files to provide additional context
- View conversation history in the left sidebar

### File Upload
- Click "Upload Files" to select and upload files
- Uploaded files are automatically included in chat context
- Supports various file types (text files work best)

### Ticket Management
- Click the bug report icon in the header to access ticket management
- Create, edit, and delete IT support tickets
- View ticket status, priority, and assignee information

### AI Assistant Features
- Ask technical questions and get AI-powered responses
- Request ticket creation for issues that need tracking
- Get help with troubleshooting and problem-solving
- The AI can automatically create and manage tickets using function calling

## API Endpoints

### File Management
- `POST /upload` - Upload files to server
- `GET /files` - List uploaded files
- `GET /files/{file_id}/content` - Get file content
- `DELETE /files/{file_id}` - Delete file

### Conversations
- `GET /conversations` - Get list of conversations
- `GET /conversations/{id}/messages` - Get messages from specific conversation
- `DELETE /conversations/{id}` - Delete conversation

### Chat
- `POST /chat` - Send message and get AI response

### Ticket Management
- `GET /tickets` - Get all tickets
- `POST /tickets` - Create new ticket
- `PUT /tickets/{id}` - Update ticket
- `DELETE /tickets/{id}` - Delete ticket
- `GET /tickets/{id}` - Get specific ticket

## Data Storage

The application uses JSON files for data persistence (stored in backend folder):
- `backend/conversations/` - Individual conversation files
- `backend/data/tickets.json` - All tickets data
- `backend/uploads/` - Uploaded files

## OpenAI Function Calling

The chatbot supports the following functions:
- `create_ticket` - Creates new support tickets
- `get_tickets` - Retrieves existing tickets
- `update_ticket` - Updates ticket status and properties

## Development

### Backend Architecture

The backend follows a modular architecture:

- **Models**: Pydantic models for data validation
- **Services**: Business logic and data operations
- **Routers**: API endpoint definitions
- **Main**: FastAPI application setup and configuration

### Virtual Environment Management

The backend uses a Python virtual environment to manage dependencies. This prevents conflicts with system packages:

- **Activation**: `cd backend && source venv/bin/activate`
- **Deactivation**: `deactivate`
- **Setup**: `cd backend && ./setup.sh`

### Environment Variables
- `OPENAI_API_KEY` - Your OpenAI API key (required)

### Troubleshooting

**Python Package Installation Issues:**
If you encounter "externally-managed-environment" errors:
1. Use the provided setup script: `cd backend && ./setup.sh`
2. This creates an isolated virtual environment for the project
3. Never install packages system-wide for this project

**Virtual Environment Issues:**
- Delete `backend/venv` folder and run `./setup.sh` again
- Make sure you're in the backend directory when activating: `cd backend && source venv/bin/activate`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License. 