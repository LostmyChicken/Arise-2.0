#!/bin/bash

echo "🚀 Starting Solo Leveling Web Game..."

# Kill any existing processes
echo "🔄 Cleaning up existing processes..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "node.*start" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 2

# Check if ports are free
if lsof -Pi :56092 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port 56092 is still in use. Please kill the process manually."
    lsof -Pi :56092 -sTCP:LISTEN
    exit 1
fi

if lsof -Pi :54156 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port 54156 is still in use. Please kill the process manually."
    lsof -Pi :54156 -sTCP:LISTEN
    exit 1
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
python3 main.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Test backend health
if curl -s http://localhost:56092/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Set environment variables for React
export REACT_APP_API_URL=http://localhost:56092
export PORT=54156
export HOST=0.0.0.0

# Start React app
npm start &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 10

# Test frontend
if curl -s http://localhost:54156 > /dev/null; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend health check failed"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 Solo Leveling Web Game is now running!"
echo "🌐 Frontend: http://localhost:54156"
echo "🔧 Backend API: http://localhost:56092"
echo "📊 API Docs: http://localhost:56092/docs"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop the servers:"
echo "kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all servers"

# Keep script running and handle Ctrl+C
trap 'echo "🛑 Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0' INT

# Wait for processes
wait
