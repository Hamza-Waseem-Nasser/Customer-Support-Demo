"""
FastAPI main application
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, validator
from typing import Optional
import uuid
import os
import logging

from .config import settings
from .agent import get_agent
from .data_setup import setup_sample_database

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Initialize database
try:
    db_file = setup_sample_database()
    logger.info(f"Database initialized: {db_file}")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Customer Support Bot API",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    passenger_id: Optional[str] = "3442 587242"  # Default for demo
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 2000:
            raise ValueError('Message too long (max 2000 characters)')
        return v.strip()

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str = "success"

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Customer Support Bot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": str(uuid.uuid4())}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get the agent
        agent = get_agent()
        
        # Configure the agent run
        config = {
            "configurable": {
                "passenger_id": request.passenger_id,
                "thread_id": session_id,
            }
        }
        
        logger.info(f"Processing chat request for session {session_id}")
        
        # Invoke the agent
        result = agent.invoke(
            {"messages": [("user", request.message)]},
            config
        )
        
        # Extract response
        response_content = result["messages"][-1].content
        
        logger.info(f"Chat response generated for session {session_id}")
        
        return ChatResponse(
            response=response_content,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/chat/continue", response_model=ChatResponse)
async def continue_chat(session_id: str, approve: bool = True):
    """Continue a chat that was interrupted for approval"""
    try:
        agent = get_agent()
        
        config = {
            "configurable": {
                "passenger_id": "3442 587242",  # Default for demo
                "thread_id": session_id,
            }
        }
        
        if approve:
            # Continue with the interrupted action
            result = agent.invoke(None, config)
        else:
            # Reject the action
            result = agent.invoke(
                {
                    "messages": [("user", "I don't want to proceed with that action. Please help me with something else.")]
                },
                config
            )
        
        response_content = result["messages"][-1].content
        
        return ChatResponse(
            response=response_content,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Continue chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error continuing chat: {str(e)}"
        )

@app.get("/chat/{session_id}/status")
async def get_chat_status(session_id: str):
    """Get the status of a chat session"""
    try:
        agent = get_agent()
        
        config = {
            "configurable": {
                "passenger_id": "3442 587242",
                "thread_id": session_id,
            }
        }
        
        # Get the current state
        snapshot = agent.get_state(config)
        
        return {
            "session_id": session_id,
            "has_interrupt": bool(snapshot.next),
            "next_actions": snapshot.next or [],
            "messages_count": len(snapshot.values.get("messages", []))
        }
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking status: {str(e)}"
        )

# Mount static files for the frontend
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
print(f"Looking for frontend at: {static_dir}")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/app")
    async def serve_frontend():
        """Serve the frontend application"""
        index_file = os.path.join(static_dir, "index.html")
        print(f"Looking for index.html at: {index_file}")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        else:
            return {"message": f"Frontend not found at {index_file}"}
else:
    @app.get("/app")
    async def serve_frontend():
        return {"message": f"Frontend directory not found at {static_dir}"}

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
