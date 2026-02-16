@echo off
REM Script to run LLM Worker Service on Windows

echo Starting LLM Worker Service...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "worker\.deps_installed" (
    echo Installing dependencies...
    pip install -r worker\requirements.txt
    type nul > worker\.deps_installed
)

REM Check if Kafka is running
docker ps | findstr kafka >nul
if errorlevel 1 (
    echo Starting Kafka...
    docker-compose up -d kafka zookeeper
    echo Waiting for Kafka to be ready...
    timeout /t 10 /nobreak
)

REM Run worker
cd worker
python -m worker.main
