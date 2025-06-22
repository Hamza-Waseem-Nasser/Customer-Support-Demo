@echo off
echo Starting Customer Support Bot MVP...

cd backend
echo Installing Python dependencies...
pip install -r requirements.txt

echo Starting the backend server...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
