# Project Structure

```
Customer-Support/
├── backend/                    # Python backend application
│   ├── app/                   # Main application package
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI server
│   │   ├── agent.py          # LangGraph agent implementation
│   │   ├── tools.py          # AI agent tools
│   │   ├── config.py         # Configuration settings
│   │   └── data_setup.py     # Database setup utilities
│   ├── cli.py                # Command-line interface
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Container configuration
│   ├── .env                 # Environment variables
│   └── travel2.sqlite       # SQLite database
├── frontend/                 # Web interface
│   └── index.html           # Single-page application
├── start-server.bat         # Windows server launcher
├── start-server.sh          # Linux/Mac server launcher
├── start-cli.bat           # Windows CLI launcher
├── docker-compose.yml      # Docker orchestration
├── production_guide.md     # Production deployment guide
├── quick_start_guide.md    # Quick start instructions
└── README.md              # Main documentation
```

## Key Files

- **`backend/cli.py`** - Command-line chat interface
- **`backend/app/main.py`** - Web API server
- **`backend/app/agent.py`** - Core AI agent logic
- **`backend/app/tools.py`** - Customer support tools
- **`frontend/index.html`** - Web chat interface
- **`start-cli.bat`** - Quick CLI access (Windows)
- **`start-server.bat`** - Quick server start (Windows)

## Usage

- **Web Interface**: Run `start-server.bat` then open `frontend/index.html`
- **CLI Interface**: Run `start-cli.bat` for terminal-based chat
- **Docker**: Run `docker-compose up` for containerized deployment
