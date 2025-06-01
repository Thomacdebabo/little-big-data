#!/usr/bin/env python3
"""Main entry point for Little Big Data application."""

import uvicorn
from little_big_data.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "little_big_data.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 