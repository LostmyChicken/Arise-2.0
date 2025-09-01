@echo off
echo 🚀 Starting Arise Web Game...

echo 📡 Starting backend server...
cd backend
start "Backend Server" python main.py

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo 🌐 Starting frontend server...
cd ..\frontend
start "Frontend Server" npm start

echo.
echo ✅ Both servers are starting up!
echo 📡 Backend: http://localhost:8000
echo 🌐 Frontend: http://localhost:3000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause > nul
