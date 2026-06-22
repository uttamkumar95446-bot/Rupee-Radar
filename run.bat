@echo off
:: ── RupeeRadar Launcher (Windows) ──
:: Starts both backend and frontend development servers.
:: Usage: double-click run.bat or run from terminal

title RupeeRadar Launcher

echo =====================================
echo        RupeeRadar Launcher
echo =====================================
echo.

:: ── Check Python ──
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.10+ is required but not found.
    pause
    exit /b 1
)
for /f "delims=" %%i in ('python --version') do echo   %%i

:: ── Check Node.js ──
echo [2/4] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js 18+ is required but not found.
    pause
    exit /b 1
)
for /f "delims=" %%i in ('node --version') do echo   %%i

:: ── Setup Backend ──
echo [3/4] Setting up backend...
cd backend

:: Create .env if not exists
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo   Created .env from .env.example
    )
)

:: Install Python deps if needed
python -m pip install -q -r requirements.txt >nul 2>&1
echo   Python dependencies installed

cd ..

:: ── Setup Frontend ──
echo [4/4] Setting up frontend...
cd frontend
if not exist node_modules (
    call npm install --silent >nul 2>&1
    echo   Node dependencies installed
)
cd ..

echo.
echo =====================================
echo  Starting servers...
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo =====================================
echo.
echo Close this window to stop both servers.
echo.

:: Start backend
start "RupeeRadar-Backend" cmd /c "cd backend && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait a moment for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend
start "RupeeRadar-Frontend" cmd /c "cd frontend && npm run dev"

:: Keep window open
echo Both servers are running. Close this window to stop.
pause
