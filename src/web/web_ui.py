#!/usr/bin/env python3
"""
Script to run the enhanced web UI for ENT CPT Code Agent v2.0.

This script initializes the agent, configures it appropriately, and starts the 
web server with the improved API interface.

File name and location: ent-cpt-agent/src/web/web_ui.py

"""

import os
import sys
import logging
import argparse
import asyncio
import uuid
from pathlib import Path

# Add project root to path for imports
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import required components
from src.config.agent_config import AgentConfig, setup_logging
from src.conversation.conversation_manager import ConversationManager
from src.agent.ent_cpt_agent import ENTCPTAgent
from src.api.api_interface import APIInterface

def parse_arguments():
    """Parse command line arguments for the web UI runner."""
    parser = argparse.ArgumentParser(
        description="ENT CPT Code Agent Web UI - v2.0"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--host", 
        type=str, 
        default=None,
        help="Host to run the server on (overrides config file)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=None,
        help="Port to run the server on (overrides config file)"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Logging level (overrides config file)"
    )
    
    parser.add_argument(
        "--database", 
        type=str, 
        default=None,
        help="Path to CPT code database (overrides config file)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the Web UI application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize configuration
    config = AgentConfig(args.config)
    
    # Override config with command line arguments if provided
    if args.log_level:
        config.set("agent", "log_level", args.log_level)
    
    if args.database:
        config.set("cpt_database", "file_path", args.database)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger("ent_cpt_agent_web_ui")
    
    try:
        logger.info("Starting ENT CPT Code Agent Web UI v2.0")
        
        # Initialize conversation manager
        conversation_dir = config.get("agent", "conversation_dir")
        logger.info(f"Initializing conversation manager with directory: {conversation_dir}")
        os.makedirs(conversation_dir, exist_ok=True)
        conversation_manager = ConversationManager(conversation_dir)
        
        # Initialize the agent
        logger.info("Initializing ENT CPT Agent")
        agent = ENTCPTAgent(config, conversation_manager)
        
        # Get host and port for the server
        host = args.host or config.get("server", "host")
        port = args.port or config.get("server", "port")
        
        # Create API interface
        logger.info(f"Creating API interface on {host}:{port}")
        api_interface = APIInterface(agent, config, host, port)
        
        # Start the server
        logger.info("Starting API server")
        api_interface.start()
        
    except KeyboardInterrupt:
        logger.info("Web UI terminated by user")
    except Exception as e:
        logger.error(f"Error running Web UI: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())