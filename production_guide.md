# Customer Support Bot - Production Implementation Guide

## Security Enhancements

### 1. Authentication & Authorization
```python
# backend/app/core/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

class SecurityManager:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALGORITHM = "HS256"
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def verify_passenger_access(self, user_id: str, passenger_id: str) -> bool:
        # Verify user has access to this passenger_id
        # Implement your business logic here
        return True
```

### 2. Rate Limiting
```python
# backend/app/core/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Usage in routes
@app.post("/api/v1/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, message: ChatMessage):
    # Implementation
    pass
```

### 3. Input Validation
```python
# backend/app/models/chat.py
from pydantic import BaseModel, validator
from typing import Optional
import re

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        if len(v) > 1000:
            raise ValueError('Message too long')
        # Add more validation as needed
        return v.strip()
```

## Enhanced LangGraph Implementation

### 1. Production-Ready State Management
```python
# backend/app/agents/states.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages

class ProductionState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: Optional[dict]
    session_id: str
    user_id: str
    context: Optional[dict]
    audit_trail: list[dict]
```

### 2. Enhanced Tool Implementation
```python
# backend/app/agents/tools/booking_tools.py
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from ..services.audit_service import AuditService

@tool
async def update_flight_booking(
    booking_id: str, 
    new_flight_id: str,
    user_id: str,
    db: Session
) -> str:
    """Update flight booking with enhanced security and auditing"""
    
    # Verify ownership
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user_id
    ).first()
    
    if not booking:
        await AuditService.log_unauthorized_access(user_id, booking_id)
        return "Booking not found or unauthorized"
    
    # Validate business rules
    if not await validate_flight_change(booking, new_flight_id):
        return "Flight change not permitted"
    
    # Update booking
    booking.flight_id = new_flight_id
    db.commit()
    
    # Audit log
    await AuditService.log_booking_update(user_id, booking_id, new_flight_id)
    
    return "Flight updated successfully"
```

## API Implementation

### 1. FastAPI Chat Endpoint
```python
# backend/app/api/v1/chat.py
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from ...core.deps import get_current_user, get_db
from ...agents.customer_support import CustomerSupportAgent

router = APIRouter()

@router.post("/chat")
async def chat(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        agent = CustomerSupportAgent(db=db)
        
        config = {
            "configurable": {
                "user_id": current_user.id,
                "passenger_id": current_user.passenger_id,
                "thread_id": message.session_id or str(uuid.uuid4())
            }
        }
        
        response = await agent.invoke(
            {"messages": [("user", message.message)]},
            config
        )
        
        return {"response": response["messages"][-1].content}
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.websocket("/chat/ws")
async def websocket_chat(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    # WebSocket implementation for real-time chat
    await websocket.accept()
    # Implementation here
```

### 2. React Frontend Implementation
```tsx
// frontend/src/components/ChatInterface.tsx
import React, { useState, useEffect } from 'react';
import { useChatSocket } from '../hooks/useChatSocket';

export const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const { sendMessage, isConnected } = useChatSocket();

    const handleSendMessage = async () => {
        if (inputMessage.trim()) {
            await sendMessage(inputMessage);
            setInputMessage('');
        }
    };

    return (
        <div className="chat-container">
            <div className="messages-area">
                {messages.map((msg, index) => (
                    <MessageBubble key={index} message={msg} />
                ))}
            </div>
            <div className="input-area">
                <input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type your message..."
                />
                <button onClick={handleSendMessage} disabled={!isConnected}>
                    Send
                </button>
            </div>
        </div>
    );
};
```

## Deployment & DevOps

### 1. Docker Configuration
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/customer_support
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: customer_support
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 2. Kubernetes Deployment
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customer-support-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: customer-support-backend
  template:
    metadata:
      labels:
        app: customer-support-backend
    spec:
      containers:
      - name: backend
        image: customer-support-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## Monitoring & Observability

### 1. Logging
```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    format='%(message)s'
)
for handler in logging.getLogger().handlers:
    handler.setFormatter(JSONFormatter())
```

### 2. Metrics
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

chat_requests_total = Counter('chat_requests_total', 'Total chat requests')
chat_response_time = Histogram('chat_response_time_seconds', 'Chat response time')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    if request.url.path == "/api/v1/chat":
        chat_requests_total.inc()
        start_time = time.time()
        response = await call_next(request)
        chat_response_time.observe(time.time() - start_time)
        return response
    return await call_next(request)
```

## Testing Strategy

### 1. Unit Tests
```python
# backend/tests/test_agents.py
import pytest
from app.agents.customer_support import CustomerSupportAgent

@pytest.mark.asyncio
async def test_flight_search():
    agent = CustomerSupportAgent()
    result = await agent.search_flights(
        departure_airport="JFK",
        arrival_airport="LAX"
    )
    assert len(result) > 0
    assert "flight_id" in result[0]
```

### 2. Integration Tests
```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post(
        "/api/v1/chat",
        json={"message": "What time is my flight?"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
```

## Performance Optimization

### 1. Caching Strategy
```python
# backend/app/core/cache.py
import redis
import json
from typing import Optional

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get_user_context(self, user_id: str) -> Optional[dict]:
        cached = self.redis.get(f"user_context:{user_id}")
        return json.loads(cached) if cached else None
    
    async def set_user_context(self, user_id: str, context: dict, ttl: int = 3600):
        self.redis.setex(
            f"user_context:{user_id}",
            ttl,
            json.dumps(context)
        )
```

### 2. Database Optimization
```python
# backend/app/models/__init__.py
from sqlalchemy import Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Add indexes for performance
Index('idx_bookings_user_status', 'user_id', 'status')
Index('idx_chat_sessions_user_updated', 'user_id', 'updated_at')
```

## Security Best Practices

1. **Environment Variables**: Use secrets management
2. **SQL Injection Prevention**: Use parameterized queries
3. **XSS Protection**: Sanitize inputs
4. **CORS Configuration**: Restrict origins
5. **Rate Limiting**: Prevent abuse
6. **Audit Logging**: Track all actions
7. **Data Encryption**: Encrypt sensitive data

## Scalability Considerations

1. **Horizontal Scaling**: Use load balancers
2. **Database Sharding**: Partition by user_id
3. **Caching Layers**: Redis for session data
4. **Message Queues**: For background processing
5. **CDN**: For static assets
6. **Microservices**: Split into domain services

This production implementation provides a robust, scalable, and secure customer support bot system that can handle real-world enterprise requirements.
