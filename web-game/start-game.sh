#!/bin/bash

echo "🎮 Starting Arise - Solo Leveling Web Game..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the web-game directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected structure: web-game/backend and web-game/frontend"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Start backend
echo "🚀 Starting Backend (FastAPI)..."
cd backend

if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found in backend directory"
    exit 1
fi

# Install backend dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Start backend server
if check_port 56092; then
    echo "   Starting on http://localhost:56092"
    python main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
else
    echo "   Backend already running on port 56092"
fi

# Start frontend
echo "🎨 Starting Frontend (React)..."
cd ../frontend

if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend directory"
    exit 1
fi

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend server
if check_port 54156; then
    echo "   Starting on http://localhost:54156"
    BROWSER=none PORT=54156 npm start > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
else
    echo "   Frontend already running on port 54156"
fi

# Wait for servers to start
echo "⏳ Waiting for servers to start..."
sleep 10

# Check if servers are responding
echo "🔍 Checking server health..."

# Check backend
if curl -s http://localhost:56092/api/health > /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend health check failed"
fi

# Check frontend
if curl -s http://localhost:54156 > /dev/null; then
    echo "✅ Frontend is serving!"
else
    echo "❌ Frontend health check failed"
fi

echo ""
echo "🎮 GAME IS READY!"
echo "=========================================="
echo "🌐 Open your browser and go to:"
echo "   http://localhost:54156"
echo ""
echo "📊 API Documentation:"
echo "   http://localhost:56092/docs"
echo ""
echo "📝 Logs:"
echo "   Backend: tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop the servers:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or use: pkill -f 'python main.py' && pkill -f 'react-scripts'"
echo ""
echo "🎯 Ready to become the Shadow Monarch!"