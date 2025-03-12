#!/usr/bin/env python3
"""
Script to run the web UI for ENT CPT Code Agent.
This script starts the web interface server for the ENT CPT Code Agent using a static ngrok domain.
"""

import os
import logging
import subprocess
from src.web.templates.app import app
from dotenv import load_dotenv
load_dotenv()

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
        
        # Static ngrok domain - load it from environment variable
        static_domain = os.environ.get("STATIC_DOMAIN", None)
        if static_domain is None:
            logger.error("STATIC_DOMAIN environment variable not set.")
            exit(1)        
        logger.info(f"Starting web UI server on {host}:{port} (debug={debug})")
        
        # Start ngrok in a separate process with static domain
        logger.info(f"Starting ngrok tunnel with static domain: {static_domain}")
        ngrok_cmd = f"ngrok http --domain={static_domain} {port}"
        
        # Start ngrok process in the background
        ngrok_process = subprocess.Popen(
            ngrok_cmd.split(), 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        logger.info(f"Ngrok tunnel established at https://{static_domain}")
        
        # Start the Flask application
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Error starting web UI server: {e}")
        exit(1)