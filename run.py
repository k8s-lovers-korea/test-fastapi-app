#!/usr/bin/env python3
"""
Script to run the FastAPI application with proper configuration
"""

import uvicorn
from config import Config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info" if not Config.DEBUG else "debug"
    )