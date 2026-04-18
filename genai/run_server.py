"""
run_server.py — Entry point for the GenAI Resolution Microservice.

Usage:
    python run_server.py
"""

import uvicorn
from config import config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info",
    )
