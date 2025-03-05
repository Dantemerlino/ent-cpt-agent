#!/usr/bin/env python3
"""
Web UI server for the ENT CPT Code Agent.
This script starts the web interface server for the ENT CPT Code Agent.
"""

import os
import logging
from flask import Flask
from src.web.templates import app  # Import the Flask app or define it here

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ent_cpt_agent_web_ui")

# If app is not imported, define it here
# app = Flask(__name__, template_folder='src/web/templates')

if __name__ == "__main__":
    try:
        # Get port from environment variable or use default
        port = int(os.environ.get("WEB_PORT", "5000"))
        host = os.environ.get("WEB_HOST", "0.0.0.0")
        debug = os.environ.get("DEBUG", "False").lower() == "true"
        
        logger.info(f"Starting web UI server on {host}:{port} (debug={debug})")
        
        # Start the Flask application
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Error starting web UI server: {e}")
        exit(1)