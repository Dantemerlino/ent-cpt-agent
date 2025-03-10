#!/usr/bin/env python3
"""
Script to run the web UI for ENT CPT Code Agent.
This script starts the web interface server for the ENT CPT Code Agent.
"""

import os
import logging
from src.web.templates.app import app
from pyngrok import ngrok  

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ent_cpt_agent_web_ui")

if __name__ == "__main__":
    try:
        # Get port from environment variable or use default
        port = int(os.environ.get("WEB_PORT", "5000"))
        host = os.environ.get("WEB_HOST", "0.0.0.0")
        debug = os.environ.get("DEBUG", "False").lower() == "true"
        
        logger.info(f"Starting web UI server on {host}:{port} (debug={debug})")
        # Open an ngrok tunnel for the Flask app
        tunnel = ngrok.connect(port, "http")
        logger.info(f"Ngrok tunnel established at {tunnel.public_url}")
        # Start the Flask application
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Error starting web UI server: {e}")
        exit(1)