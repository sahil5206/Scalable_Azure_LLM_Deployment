@echo off
REM Start all services for local development on Windows

echo Starting LLM Inference Platform...
echo ==================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Start Kafka and Zookeeper
echo Starting Kafka and Zookeeper...
docker-compose up -d kafka zookeeper

REM Wait for Kafka to be ready
echo Waiting for Kafka to be ready...
timeout /t 10 /nobreak >nul

REM Start Worker (in background)
echo Starting Worker service...
cd worker
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

REM Start worker in background
start "LLM Worker" cmd /c "python -m worker.main"
cd ..

REM Start Web Frontend
echo Starting Web Frontend...
cd web
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo.
echo ==================================
echo All services started!
echo ==================================
echo Web UI: http://localhost:8000
echo Worker Health: http://localhost:8081/health
echo Worker Metrics: http://localhost:8080/metrics
echo.
echo Press Ctrl+C to stop
echo.

python -m web.main

cd ..
