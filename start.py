#!/usr/bin/env python3
import os
import argparse
import webbrowser
import time
import uvicorn
import threading
from pathlib import Path

def open_browser(host, port, delay=1.5):
    """Open web browser after a short delay to ensure server is running"""
    time.sleep(delay)
    url = f"http://{host}:{port}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)

def ensure_required_directories():
    """Create any required directories if they don't exist"""
    for directory in ["data/sample", "results"]:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point for the trading analysis system"""
    parser = argparse.ArgumentParser(description="AI-Powered Trading Analysis System")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Create required directories
    ensure_required_directories()

    # Print welcome message
    print("\n" + "="*70)
    print("       🚀 AI-Powered Trading Analysis System 📈")
    print("="*70)
    print("\n▶️ Starting server...")
    print(f"▶️ Access the application at http://{args.host}:{args.port}")
    print("▶️ Press CTRL+C to stop the server")
    print("\n")

    # Open browser in a separate thread if requested
    if not args.no_browser:
        browser_thread = threading.Thread(
            target=open_browser, 
            args=(args.host, args.port)
        )
        browser_thread.daemon = True
        browser_thread.start()

    # Start the FastAPI server
    uvicorn.run(
        "app:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload
    )

if __name__ == "__main__":
    main() 