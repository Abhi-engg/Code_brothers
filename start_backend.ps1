# PowerShell script to start the backend server
Write-Host "Starting Writing Assistant Backend Server..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Start the FastAPI server with auto-reload
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
