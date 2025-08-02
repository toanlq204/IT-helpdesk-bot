#!/bin/bash

# Backend Setup Script for IT HelpDesk Chatbot

echo "🔧 Setting up backend environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if we're on macOS and suggest installing build tools
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v gcc &> /dev/null; then
        echo "⚠️  Build tools not found. Installing Xcode Command Line Tools..."
        echo "Please run: xcode-select --install"
        echo "Then rerun this script."
        read -p "Have you installed Xcode Command Line Tools? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Please install Xcode Command Line Tools first:"
            echo "  xcode-select --install"
            exit 1
        fi
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔋 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip to latest version
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install wheel and setuptools first
echo "🛠️  Installing build tools..."
pip install wheel setuptools

# For macOS with Apple Silicon, we might need to set some environment variables
if [[ "$OSTYPE" == "darwin"* ]] && [[ $(uname -m) == "arm64" ]]; then
    echo "🍎 Detected Apple Silicon Mac, setting build environment..."
    export ARCHFLAGS="-arch arm64"
fi

# Try to install dependencies with better error handling
echo "📚 Installing dependencies..."
if pip install -r requirements.txt; then
    echo "✅ All dependencies installed successfully!"
else
    echo "❌ Some dependencies failed to install. Trying alternative approach..."
    
    # Try installing dependencies one by one, with fallbacks for problematic ones
    echo "🔄 Installing dependencies individually..."
    
    # Install basic dependencies first
    pip install fastapi uvicorn python-multipart python-dotenv aiofiles
    
    # Try to install pydantic with a specific version that's more compatible
    echo "📦 Installing pydantic..."
    if ! pip install "pydantic>=2.0,<2.6"; then
        echo "⚠️  Pydantic 2.x failed, trying pydantic 1.x..."
        pip install "pydantic>=1.10,<2.0"
    fi
    
    # Try to install openai
    echo "🤖 Installing OpenAI..."
    if ! pip install openai; then
        echo "⚠️  Latest OpenAI failed, trying older version..."
        pip install "openai>=0.28,<1.0"
    fi
fi

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo ""
echo "To start the server:"
echo "  python main.py"
echo ""
echo "To deactivate the virtual environment:"
echo "  deactivate"
echo ""

# Test the installation
echo "🧪 Testing installation..."
if python -c "import fastapi, pydantic; print('✅ Core dependencies working!')"; then
    echo "🎉 Setup completed successfully!"
else
    echo "⚠️  There might be some issues with the installation."
    echo "Try running the server and see if it works."
fi 