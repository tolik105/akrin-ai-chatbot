"""
Main FastAPI application for AKRIN AI Chatbot
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import logging
from prometheus_client import make_asgi_app

from src.api.routers import chat, admin, health, knowledge
from src.core.config import Settings
from src.utils.logging import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging(__name__)

# Load settings
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AKRIN AI Chatbot API...")
    
    # Initialize connections, models, etc.
    # TODO: Initialize vector store connection
    # TODO: Load NLP models
    # TODO: Connect to databases
    
    yield
    
    # Shutdown
    logger.info("Shutting down AKRIN AI Chatbot API...")
    # TODO: Close connections, cleanup resources


# Create FastAPI app
app = FastAPI(
    title="AKRIN AI Chatbot API",
    description="High-performance AI-powered customer service chatbot",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(health.router, prefix="/api/health", tags=["health"])

# WebSocket routes
from src.api import websocket
app.include_router(websocket.router)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted successfully at /static")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")
    # Try alternative path
    import os
    static_path = os.path.join(os.getcwd(), "static")
    logger.info(f"Trying alternative static path: {static_path}")
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AKRIN AI Chatbot API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/chat-widget.html")
async def chat_widget():
    """Serve chat widget from root for backward compatibility"""
    from fastapi.responses import FileResponse
    return FileResponse("static/chat-widget.html")


@app.get("/agent-dashboard.html") 
async def agent_dashboard():
    """Serve agent dashboard from root for backward compatibility"""
    from fastapi.responses import FileResponse
    return FileResponse("static/agent-dashboard.html")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True if settings.app_env == "development" else False
    )