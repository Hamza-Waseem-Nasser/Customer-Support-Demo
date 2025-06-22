@echo off
REM Setup script for Swiss Airlines Customer Support Bot

echo 🛩️ Setting up Swiss Airlines Customer Support Bot...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    pause
    exit /b 1
)

REM Show Python version
echo ✅ Python version:
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Setup environment file
if not exist ".env" (
    echo ⚙️ Creating .env file from template...
    copy ..\.env.example .env
    echo 📝 Please edit backend\.env file and add your API keys
) else (
    echo ✅ .env file already exists
)

cd ..

echo.
echo 🎉 Setup complete!
echo.
echo Next steps:
echo 1. Edit backend\.env and add your API keys
echo 2. Run the server: start-server.bat
echo 3. Or use CLI: start-cli.bat
echo.
echo 📖 For more info, see README.md
pause
