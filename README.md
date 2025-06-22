# 🛩️ Swiss Airlines Customer Support Bot

A modern AI-powered customer support system built with **LangGraph**, **FastAPI**, and **Google Gemini**. Features both web interface and command-line access for comprehensive customer service automation.

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6B6B?style=flat)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🤖 **AI-Powered Agent** - Built with LangGraph for complex conversation flows
- ✈️ **Flight Management** - Search, update, and cancel flight bookings
- 🏨 **Hotel Bookings** - Search and book accommodations
- 🚗 **Car Rentals** - Find and reserve rental vehicles
- 🎯 **Trip Recommendations** - Discover activities and excursions
- 📋 **Policy Lookup** - Real-time company policy consultation
- 🔍 **Web Search** - Current information with Tavily integration
- 👤 **Human-in-the-Loop** - Approval required for sensitive actions
- 💾 **Session Management** - Persistent conversation state
- 🌐 **Modern Web UI** - Clean, responsive chat interface
- 💻 **CLI Interface** - Command-line access for developers

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- At least one LLM API key (Gemini, OpenAI, or Anthropic)

### Automated Setup (Recommended)

1. **Clone the repository**:
```bash
git clone https://github.com/Hamza-Waseem-Nasser/Customer-Support-Demo.git
cd Customer-Support-Demo
```

2. **Run setup script**:
```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

3. **Add your API keys**:
   - Edit `backend/.env` and add your API keys
   - At least one LLM API key is required (Gemini, OpenAI, or Anthropic)

4. **Start the application**:
```bash
# Web Interface
start-server.bat        # Windows
./start-server.sh       # Linux/Mac

# CLI Interface  
start-cli.bat          # Windows
```

### Manual Setup

1. **Clone and setup**:
```bash
git clone https://github.com/Hamza-Waseem-Nasser/Customer-Support-Demo.git
cd Customer-Support-Demo
```

2. **Create virtual environment**:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp ../.env.example .env
# Edit .env and add your API keys
```

5. **Start the server**:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

6. **Open the interface**:
   - Web UI: Open `frontend/index.html` in your browser
   - API Docs: http://localhost:8000/docs

### Option 3: Docker

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- API: http://localhost:8000

## 🏗️ Architecture

```
Customer-Support/
├── backend/                 # Python backend
│   ├── app/
│   │   ├── main.py         # FastAPI server
│   │   ├── agent.py        # LangGraph agent
│   │   ├── tools.py        # AI tools
│   │   └── config.py       # Settings
│   └── cli.py              # CLI interface
├── frontend/               # Web interface
└── start-*.bat/sh         # Launcher scripts
```

## 🛠️ Technology Stack

- **Backend**: Python, FastAPI, LangGraph, LangChain
- **AI Models**: Google Gemini, OpenAI GPT, Anthropic Claude
- **Database**: SQLite (demo), PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript
- **Search**: Tavily API
- **Deployment**: Docker, Docker Compose

## 📚 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /chat` - Chat with the AI agent
- `GET /health` - Health check
- `GET /app` - Serve web interface

## 🎯 Example Interactions

- *"What time is my flight to Basel?"*
- *"I need to change my flight to next week"*  
- *"Book me a hotel in Zurich for 3 nights"*
- *"Find car rentals near the airport"*
- *"What's the policy on flight changes?"*

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes* |
| `OPENAI_API_KEY` | OpenAI API key | Yes* |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes* |
| `TAVILY_API_KEY` | Tavily search API key | No |
| `VERBOSE_LOGGING` | Enable detailed logging | No |

*At least one LLM API key is required

### Sample Data

The project includes a sample SQLite database with:
- Flight bookings
- Hotels and car rentals  
- Trip recommendations
- Passenger information

## 🚀 Deployment

### Development
```bash
python -m uvicorn app.main:app --reload
```

### Production
```bash
docker-compose -f docker-compose.yml up -d
```

See `production_guide.md` for detailed production setup.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Travel data from LangChain tutorials

## 📞 Support

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/swiss-airlines-support-bot/issues)
- 📖 Docs: See `quick_start_guide.md`

---

⭐ Star this repo if you find it helpful!

## Features

- ✅ **Flight Management**: Search and update flight bookings
- ✅ **Hotel Bookings**: Search and book hotels
- ✅ **Car Rentals**: Find and reserve rental cars
- ✅ **Trip Recommendations**: Discover activities and excursions
- ✅ **Policy Lookup**: Get company policy information
- ✅ **Web Search**: Search current information with Tavily
- ✅ **Human-in-the-Loop**: Approval required for sensitive actions
- ✅ **Session Management**: Persistent conversation state
- ✅ **Modern UI**: Clean, responsive chat interface

## API Endpoints

### Chat
- `POST /chat` - Send a message to the bot
- `POST /chat/continue` - Continue after approval request
- `GET /chat/{session_id}/status` - Check session status

### Utility
- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Configuration

The application uses the following APIs:
- **Tavily**: Web search (already configured)
- **Google Gemini**: Primary LLM (already configured)
- **SQLite**: Sample travel database (auto-downloaded)

## Sample Interactions

Try these questions:
- "What time is my flight?"
- "Can I change my flight to next week?"
- "Find me a hotel in my destination city"
- "What car rental options are available?"
- "What activities can I do there?"
- "What's the policy on flight changes?"

## Architecture

```
Frontend (HTML/JS) ← HTTP → FastAPI ← LangGraph → Tools
                                         ↓
                                   SQLite Database
```

## Next Steps

1. **Test the system** with various queries
2. **Add authentication** for multi-user support
3. **Integrate PostgreSQL** for production
4. **Add monitoring** and logging
5. **Deploy to cloud** (AWS, GCP, Azure)

## Troubleshooting

- **Database issues**: The app will auto-download the sample database
- **API errors**: Check your API keys in the `.env` file
- **Port conflicts**: Change ports in the configuration if needed
- **CORS issues**: Add your domain to `cors_origins` in config

## Support

The bot demonstrates advanced AI agent patterns:
- Multi-tool integration
- State management with checkpointing
- Human oversight for sensitive operations
- Error handling and recovery
- Session persistence
