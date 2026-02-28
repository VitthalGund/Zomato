@echo off
REM Backend startup script for Windows

echo Starting Zomato EdgeVision Backend...

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the server
uvicorn main:app --reload --port 8000
