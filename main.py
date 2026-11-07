"""
Smart Parking Lot Management System - Main Entry Point
Run this file to start the web server:
    python main.py
Or:
    python app.py
"""
import os
from app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ("1", "true", "yes")
    print(f"Starting Smart Parking web server on http://127.0.0.1:{port} ...")
    app.run(host="127.0.0.1", port=port, debug=debug_mode)
