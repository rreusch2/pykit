#!/bin/bash

echo "🚀 Starting ParleyApp ChatKit Server Setup"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install the chatkit package in development mode
echo "🔗 Installing ChatKit package..."
pip install -e .

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env with your actual values"
fi

# Start the server
echo ""
echo "🎯 Starting Professor Lock ChatKit Server..."
echo "=========================================="
echo "📊 Server will be available at:"
echo "   http://localhost:8000"
echo ""
echo "📝 Endpoints:"
echo "   - ChatKit: http://localhost:8000/chatkit"
echo "   - Health:  http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Run the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
