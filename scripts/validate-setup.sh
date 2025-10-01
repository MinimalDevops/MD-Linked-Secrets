#!/bin/bash

echo "🔍 Validating MD-Linked-Secrets PM2 Setup"
echo "=========================================="

# Check if virtual environment exists
if [ -f ".venv/bin/python" ]; then
    echo "✅ Virtual environment found"
    echo "   Python path: $(readlink -f .venv/bin/python)"
else
    echo "❌ Virtual environment not found"
    echo "   Run: python -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

# Check if PM2 is installed
if command -v pm2 &> /dev/null; then
    echo "✅ PM2 installed: $(pm2 --version)"
else
    echo "❌ PM2 not found"
    echo "   Run: npm install -g pm2"
    exit 1
fi

# Check if backend dependencies are installed
if .venv/bin/pip list | grep -q fastapi; then
    echo "✅ Backend dependencies installed"
else
    echo "❌ Backend dependencies missing"
    echo "   Run: source .venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

# Check if frontend dependencies are installed
if [ -d "frontend/node_modules" ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "❌ Frontend dependencies missing"
    echo "   Run: cd frontend && npm install"
    exit 1
fi

# Check if scripts are executable
if [ -x "pm2-scripts.sh" ] && [ -x "start-backend.sh" ]; then
    echo "✅ PM2 scripts are executable"
else
    echo "❌ Scripts need execution permissions"
    echo "   Run: chmod +x pm2-scripts.sh start-backend.sh"
    exit 1
fi

# Check if logs directory exists (create if not)
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo "✅ Created logs directory"
else
    echo "✅ Logs directory exists"
fi

echo ""
echo "🎉 Setup validation complete!"
echo ""
echo "Ready to start with PM2:"
echo "  ./pm2-scripts.sh start-all    # Start both services"
echo "  ./pm2-scripts.sh status       # Check status"
echo "  ./pm2-scripts.sh logs         # View logs" 