#!/usr/bin/env python3
"""
Main application script for the ENT CPT Code Agent.
This script provides CLI options to run the agent in different modes.
"""

import argparse
import logging
import os
import sys
from typing import Dict, Any

# Import agent components
# In a real application, these would be from your actual modules
from agent_config import AgentConfig, setup_logging
from conversation_manager import ConversationManager
from ent_cpt_agent import ENTCPTAgent
from api_interface import APIInterface

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ENT CPT Code Agent - An AI assistant for ENT procedure coding"
    )
    
    # General arguments
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Logging level (overrides config file)"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Interactive mode
    interactive_parser = subparsers.add_parser(
        "interactive", 
        help="Run in interactive command-line mode"
    )
    
    # Server mode
    server_parser = subparsers.add_parser(
        "server", 
        help="Run as an API server"
    )
    server_parser.add_argument(
        "--host", 
        type=str, 
        default=None,
        help="Host to run the server on (overrides config file)"
    )
    server_parser.add_argument(
        "--port", 
        type=int, 
        default=None,
        help="Port to run the server on (overrides config file)"
    )
    
    # Single query mode
    query_parser = subparsers.add_parser(
        "query", 
        help="Process a single query and exit"
    )
    query_parser.add_argument(
        "text", 
        type=str,
        help="Query text to process"
    )
    
    # Initialize config
    init_parser = subparsers.add_parser(
        "init", 
        help="Initialize default configuration file"
    )
    
    return parser.parse_args()

def run_interactive_mode(agent: ENTCPTAgent):
    """Run the agent in interactive CLI mode."""
    agent.run_interactive_session()

def run_server_mode(agent: ENTCPTAgent, config: AgentConfig, host: str = None, port: int = None):
    """Run the agent as an API server."""
    # Use provided host/port or get from config
    host = host or config.get("server", "host")
    port = port or config.get("server", "port")
    
    # Create and start API server
    api = APIInterface(agent, config, host, port)
    api.start()

def run_single_query(agent: ENTCPTAgent, query: str):
    """Process a single query and print the result."""
    response = agent.process_query(query)
    print(response)

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize configuration
    config = AgentConfig(args.config)
    
    # Handle 'init' command first
    if args.command == "init":
        config.create_default_config()
        print(f"Initialized default configuration at {args.config}")
        return
    
    # Override config with command line arguments if provided
    if args.log_level:
        config.set("agent", "log_level", args.log_level)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger("ent_cpt_agent.main")
    
    try:
        # Initialize conversation manager
        conversation_manager = ConversationManager(
            config.get("agent", "conversation_dir")
        )
        
        # Initialize the agent
        logger.info("Initializing ENT CPT Agent")
        agent = ENTCPTAgent(config, conversation_manager)
        
        # Run the appropriate command
        if args.command == "interactive":
            logger.info("Starting interactive session")
            run_interactive_mode(agent)
        
        elif args.command == "server":
            logger.info("Starting API server")
            # Override config with command line arguments if provided
            host = args.host or config.get("server", "host")
            port = args.port or config.get("server", "port")
            run_server_mode(agent, config, host, port)
        
        elif args.command == "query":
            logger.info(f"Processing single query: {args.text}")
            run_single_query(agent, args.text)
        
        else:
            # No command specified, default to interactive mode
            logger.info("No command specified, starting interactive session")
            run_interactive_mode(agent)
    
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Error running application: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
