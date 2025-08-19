#!/bin/bash

# IT HelpDesk Chatbot Startup Script

echo "🚀 Starting IT HelpDesk Chatbot..."

# Get the script directory and go to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Check if backend virtual environment exists
if [ ! -d "Backend/venv" ]; then
    echo "⚠️  Virtual environment not found. Setting up backend..."
    cd Backend
    if [ -f "setup.sh" ]; then
        ./setup.sh
    else
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    cd ..
fi

# Check if .env file exists in backend directory
if [ ! -f "Backend/.env" ]; then
    echo "❌ Backend/.env file not found. Please create one from backend/.env.example and add your OpenAI API key."
    exit 1
fi

# Function to check if port is in use
check_port() {
    lsof -ti:$1 > /dev/null 2>&1
}

# Kill existing processes on our ports
echo "🧹 Cleaning up existing processes..."
if check_port 3000; then
    echo "Stopping process on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

if check_port 8000; then
    echo "Stopping process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

# Create necessary directories in backend
mkdir -p Backend/uploads Backend/conversations Backend/data

# Start backend server
echo "🐍 Starting Python backend server..."
cd Backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "⚛️  Starting React frontend server..."
cd ../Frontend

# Check if frontend dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install frontend dependencies"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
fi

npm start &
FRONTEND_PID=$!

echo ""
echo "🎉 Both servers started successfully!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Cleanup complete"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for processes
wait