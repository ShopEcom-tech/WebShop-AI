"""
WebShop-AI Agent API Server
FastAPI server that exposes agent endpoints
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str
    language: Optional[str] = "fr"


class ChatResponse(BaseModel):
    success: bool
    message: str
    agent: str
    session_id: str


class InvokeRequest(BaseModel):
    action: str
    params: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    # Startup
    logger.info("🐍 Starting WebShop-AI Agent Server...")
    
    # Initialize orchestrator and register agents
    from .orchestrator import get_orchestrator
    from .agents import get_marie_agent
    
    orchestrator = get_orchestrator()
    
    # Register MARIE agent
    marie = get_marie_agent()
    orchestrator.registry.register("marie", marie)
    
    logger.info("✅ All agents registered")
    logger.info("🚀 WebShop-AI Agent Server ready!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="WebShop-AI Agents",
    description="Multi-agent AI system for Web Shop",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "WebShop-AI Agents",
        "version": "0.1.0",
        "status": "running",
        "language": "Python (FastAPI)",
        "agents": ["MARIE", "JOHN", "HUGO", "LUCAS", "EMMA", "NOAH"]
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/agents/{agent_id}/chat", response_model=ChatResponse)
async def agent_chat(agent_id: str, request: ChatRequest):
    """
    Chat with a specific agent.
    
    Args:
        agent_id: Agent ID (marie, john, hugo, lucas, emma, noah)
        request: Chat request with message and session_id
    """
    from .orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    
    result = await orchestrator.invoke(
        agent_id=agent_id,
        message=request.message,
        session_id=request.session_id,
        context={"language": request.language}
    )
    
    if result.get("success"):
        return ChatResponse(
            success=True,
            message=result["message"],
            agent=result["agent"],
            session_id=result["session_id"]
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Unknown error")
        )


@app.post("/agents/{agent_id}/invoke")
async def invoke_agent(agent_id: str, request: InvokeRequest):
    """
    Invoke an agent with a specific action.
    
    For advanced use cases beyond simple chat.
    """
    from .orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    agent = orchestrator.registry.get(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # TODO: Implement action handling per agent
    return {
        "success": True,
        "agent": agent_id,
        "action": request.action,
        "result": "Action executed"
    }


@app.get("/agents")
async def list_agents():
    """List all available agents"""
    from .orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    agents = orchestrator.registry.list_agents()
    
    return {
        "agents": agents,
        "total": len(agents)
    }


@app.get("/agents/{agent_id}/status")
async def agent_status(agent_id: str):
    """Get agent status"""
    from .orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    agent = orchestrator.registry.get(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "agent_id": agent_id,
        "name": agent.name,
        "role": agent.role,
        "status": "active"
    }


# Entry point for uvicorn
def main():
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True
    )


if __name__ == "__main__":
    main()
