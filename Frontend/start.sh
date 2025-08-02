#!/bin/bash

# IT HelpDesk Chatbot Startup Script

echo "🚀 Starting IT HelpDesk Chatbot..."

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "⚠️  Virtual environment not found. Setting up backend..."
    cd backend
    ./setup.sh
    cd ..
fi

# Check if .env file exists in backend directory
if [ ! -f "backend/.env" ]; then
    echo "❌ backend/.env file not found. Please create one from backend/.env.example and add your OpenAI API key."
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
mkdir -p backend/uploads backend/conversations backend/data

# Start backend server
echo "🐍 Starting Python backend server..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "⚛️  Starting React frontend server..."
cd ..
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