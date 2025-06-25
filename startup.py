#!/usr/bin/env python3
"""
Production startup script for AKRIN AI Chatbot
Handles missing modules gracefully
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Use the PORT environment variable from Render
    port = int(os.environ.get("PORT", 8000))
    
    # Import and run the app
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )