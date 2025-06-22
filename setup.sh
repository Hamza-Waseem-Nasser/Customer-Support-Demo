#!/bin/bash
# Setup script for Swiss Airlines Customer Support Bot

echo "🛩️ Setting up Swiss Airlines Customer Support Bot..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check Python version
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate || .venv\Scripts\activate

# Install dependencies
echo "📚 Installing dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp ../.env.example .env
    echo "📝 Please edit backend/.env file and add your API keys"
else
    echo "✅ .env file already exists"
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your API keys"
echo "2. Run the server: ./start-server.sh (Linux/Mac) or start-server.bat (Windows)"
echo "3. Or use CLI: ./start-cli.bat"
echo ""
echo "📖 For more info, see README.md"
