#!/usr/bin/env python3
"""
Quick development server script that bypasses configargparse issues.
"""
import os
import sys
from pathlib import Path

# Set environment variables for configuration
os.environ["HOA_SECRET_KEY"] = "dev-secret-key-for-testing"
os.environ["HOA_ALLOWED_RPS"] = "localhost|Local Dev|http://localhost:8000;http://127.0.0.1:8000"
os.environ["HOA_DATABASE_URL"] = f"sqlite:///{Path.home()}/.config/hoa/hoa.db"
os.environ["HOA_ENVIRONMENT"] = "development"
os.environ["HOA_RELOAD"] = "true"
os.environ["HOA_CORS_ENABLED"] = "true"
os.environ["HOA_CORS_ORIGINS"] = '["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5173"]'

# Now import and run
import uvicorn
from hoa.app import create_app

if __name__ == "__main__":
    print("🚀 Starting HOA development server...")
    print(f"📦 Database: {os.environ['HOA_DATABASE_URL']}")
    print(f"🔐 WebAuthn RPs: {os.environ['HOA_ALLOWED_RPS']}")
    print(f"🌐 Server: http://localhost:8000")
    print(f"📝 API Docs: http://localhost:8000/docs")
    print()
    
    # Use factory mode for uvicorn
    uvicorn.run(
        "hoa.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

