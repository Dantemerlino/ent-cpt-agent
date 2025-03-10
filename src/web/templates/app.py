"""
Flask application for the ENT CPT Code Agent Web UI.
This file defines the Flask app and routes for interacting with the ENT CPT Agent.
File name and location: ent-cpt-agent/src/web/templates/app.py
"""

import os
import json
import logging
import sys
import pandas as pd
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Configure path to ensure imports work correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # Add project root to path

# Import agent components
from src.config.agent_config import AgentConfig
from src.conversation.conversation_manager import ConversationManager
from src.agent.ent_cpt_agent import ENTCPTAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ent_cpt_agent_web")

# Initialize Flask app with correct template folder
template_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=template_dir)

# Global variables for agent and configuration
config = None
agent = None
initialization_error = None
agent_initialized = False

# Initialize the agent function
def init_agent():
    """Initialize the agent with configuration."""
    global config, agent, initialization_error, agent_initialized
    
    # Skip if already initialized
    if agent_initialized:
        return True
    
    try:
        logger.info("Starting agent initialization")
        
        # Initialize configuration
        config_path = os.environ.get("CONFIG_PATH", "config.json")
        logger.info(f"Loading configuration from {config_path}")
        config = AgentConfig(config_path)
        
        # Initialize conversation manager
        conversation_dir = config.get("agent", "conversation_dir")
        logger.info(f"Initializing conversation manager with directory: {conversation_dir}")
        conversation_manager = ConversationManager(conversation_dir)
        
        # Initialize agent
        logger.info("Initializing ENT CPT Agent")
        agent = ENTCPTAgent(config, conversation_manager)
        logger.info("Agent initialized successfully")
        initialization_error = None
        agent_initialized = True
        return True
    except Exception as e:
        logger.error(f"Error initializing agent: {e}", exc_info=True)
        initialization_error = str(e)
        agent = None
        agent_initialized = False
        return False

# Attempt to initialize the agent at startup
init_agent()

# Define a before_request handler for newer Flask versions
@app.before_request
def ensure_agent_initialized():
    """Ensure the agent is initialized before handling any request."""
    if not agent_initialized and not request.endpoint == 'static':
        init_agent()

@app.route('/')
def index():
    """Render the main page."""
    # Check if agent is initialized
    if agent is None:
        # Return an error page if agent initialization failed
        return render_template('error.html', 
                              error="Agent initialization failed", 
                              details=initialization_error)
    
    try:
        # Generate a new session ID
        conversation = agent.conversation_manager.create_conversation()
        session_id = conversation.session_id
        
        return render_template('index.html', session_id=session_id)
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        return render_template('error.html', 
                               error="Failed to create conversation", 
                               details=str(e))

@app.route('/api/query', methods=['POST'])
def query_api():
    """API endpoint for querying the agent."""
    # Check if agent is initialized
    if agent is None:
        return jsonify({"status": "error", "message": "Agent not initialized"}), 500
    
    try:
        data = request.json
        query = data.get('query')
        session_id = data.get('session_id')
        
        if not query:
            return jsonify({"status": "error", "message": "No query provided"})
        
        # Get or create session
        conversation_manager = agent.conversation_manager
        
        if session_id and conversation_manager.get_conversation(session_id):
            conversation = conversation_manager.get_conversation(session_id)
        else:
            conversation = conversation_manager.create_conversation()
            session_id = conversation.session_id
        
        # Add user message to conversation
        conversation.add_message("user", query)
        
        # Process the query
        response = agent.process_query(query, conversation)
        
        # Extract CPT codes from response
        codes = conversation_manager.extract_cpt_codes(response)
        
        # Add assistant message to conversation
        conversation.add_message("assistant", response, codes)
        
        # Save conversation
        conversation_manager.save_conversation(conversation)
        
        return jsonify({
            "status": "success",
            "message": response,
            "data": {
                "codes": codes
            },
            "session_id": session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_codes():
    """API endpoint for searching CPT codes."""
    # Check if agent is initialized
    if agent is None:
        return jsonify({"status": "error", "message": "Agent not initialized"}), 500
    
    try:
        data = request.json
        search_term = data.get('search_term')
        
        if not search_term:
            return jsonify({"status": "error", "message": "No search term provided"})
        
        results = agent.cpt_db.search_codes(search_term)
        
        return jsonify({
            "status": "success",
            "data": {
                "codes": results,
                "count": len(results)
            }
        })
    
    except Exception as e:
        logger.error(f"Error searching codes: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_code():
    """API endpoint for validating CPT codes."""
    # Check if agent is initialized
    if agent is None:
        return jsonify({"status": "error", "message": "Agent not initialized"}), 500
    
    try:
        data = request.json
        code = data.get('code')
        
        logger.info(f"Validating CPT code: {code}")
        
        if not code:
            return jsonify({"status": "error", "message": "No code provided"})
        
        # Check if cpt_db has get_code_validation method
        if not hasattr(agent.cpt_db, 'get_code_validation'):
            logger.error("CPT database does not have get_code_validation method")
            
            # Fallback to direct database lookup
            try:
                # If cpt_db is a DataFrame, check if code exists directly
                if isinstance(agent.cpt_db, pd.DataFrame):
                    code_match = agent.cpt_db[agent.cpt_db['CPT_code'].astype(str) == str(code)]
                    
                    if not code_match.empty:
                        description = code_match.iloc[0]['description']
                        key_indicator_raw = code_match.iloc[0].get('key_indicator', 'No')
                        key_indicator = str(key_indicator_raw).strip().lower() in ("yes", "true", "1")
                        standard_charge = code_match.iloc[0].get('standard_charge', 0.0)
                        
                        result = {
                            "valid": True,
                            "code": code,
                            "description": description,
                            "key_indicator": key_indicator,
                            "standard_charge": float(standard_charge)
                        }
                    else:
                        result = {
                            "valid": False,
                            "code": code,
                            "error": f"Invalid CPT code: {code}"
                        }
                else:
                    result = {
                        "valid": False,
                        "code": code,
                        "error": "Database is not properly configured"
                    }
            except Exception as db_error:
                logger.error(f"Error with fallback database lookup: {db_error}")
                result = {
                    "valid": False,
                    "code": code,
                    "error": f"Database error: {str(db_error)}"
                }
        else:
            # Use the proper validation method
            result = agent.cpt_db.get_code_validation(code)
        
        logger.info(f"Validation result for {code}: {result}")
        
        return jsonify({
            "status": "success" if result.get("valid", False) else "error",
            "message": result.get("description") if result.get("valid", False) else result.get("error"),
            "data": result
        })
    
    except Exception as e:
        logger.error(f"Error validating code: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_procedure():
    """API endpoint for analyzing a procedure description."""
    # Check if agent is initialized
    if agent is None:
        return jsonify({"status": "error", "message": "Agent not initialized"}), 500
    
    try:
        data = request.json
        procedure_text = data.get('procedure_text')
        candidate_codes = data.get('candidate_codes')
        
        if not procedure_text:
            return jsonify({"status": "error", "message": "No procedure text provided"})
        
        # If candidate codes weren't provided, search for them
        if not candidate_codes:
            search_results = agent.cpt_db.search_codes(procedure_text)
            candidate_codes = [result["code"] for result in search_results]
        
        # Analyze the procedure using the rules engine
        analysis = agent.rules_engine.analyze_procedure(
            procedure_text, candidate_codes, agent.cpt_db)
        
        return jsonify({
            "status": "success",
            "data": analysis
        })
    
    except Exception as e:
        logger.error(f"Error analyzing procedure: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/new_session', methods=['POST'])
def new_session():
    """Create a new conversation session."""
    # Check if agent is initialized
    if agent is None:
        return jsonify({"status": "error", "message": "Agent not initialized"}), 500
    
    try:
        conversation = agent.conversation_manager.create_conversation()
        
        return jsonify({
            "status": "success",
            "message": "New session created",
            "session_id": conversation.session_id
        })
    
    except Exception as e:
        logger.error(f"Error creating new session: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the API is working."""
    try:
        # Check if agent is initialized
        if agent is None:
            return jsonify({
                "status": "warning",
                "message": "Agent not initialized",
                "details": initialization_error
            })
        
        # Check if database is loaded
        if not hasattr(agent, 'cpt_db') or (hasattr(agent, 'cpt_db') and isinstance(agent.cpt_db, pd.DataFrame) and agent.cpt_db.empty):
            return jsonify({
                "status": "warning",
                "message": "CPT database not loaded"
            })
        
        # Check if model is initialized
        if not hasattr(agent, 'client') or agent.client is None:
            return jsonify({
                "status": "warning",
                "message": "LM Studio model not initialized"
            })
        
        return jsonify({
            "status": "success",
            "message": "Service is healthy",
            "details": {
                "model": agent.model_name,
                "database": agent.cpt_db_path,
                "conversation_dir": agent.conversation_manager.conversation_dir
            }
        })
    
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# Debug endpoint to help diagnose issues
@app.route('/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to get information about the application state."""
    return jsonify({
        "agent_initialized": agent_initialized,
        "agent_is_none": agent is None,
        "initialization_error": initialization_error,
        "has_config": config is not None,
        "template_dir": template_dir,
        "cwd": os.getcwd(),
        "python_path": sys.path,
        "environment_variables": {k: v for k, v in os.environ.items() if k.startswith(("CONFIG", "WEB", "DEBUG"))}
    })

if __name__ == '__main__':
    """
    This section only executes when the file is run directly.
    In production, use the run_web_ui.py script instead.
    """
    port = int(os.environ.get("WEB_PORT", "5000"))
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    # Try to initialize the agent again if needed
    if not agent_initialized:
        init_agent()
    
    print(f"Starting web server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)