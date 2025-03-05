from flask import Flask, render_template, request, jsonify, session
import uuid
import logging
import os
import requests
import json
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ent_cpt_agent_web")

# Configuration
API_HOST = os.environ.get("API_HOST", "localhost")
API_PORT = int(os.environ.get("API_PORT", "8000"))
API_BASE_URL = f"http://{API_HOST}:{API_PORT}/api"

@app.route('/')
def index():
    """Render the main page."""
    # Generate a session ID if not present
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html', session_id=session['session_id'])

@app.route('/api/query', methods=['POST'])
def query():
    """Process a query and return the response."""
    data = request.json
    query_text = data.get('query', '')
    session_id = data.get('session_id', session.get('session_id'))
    
    if not query_text:
        return jsonify({
            'status': 'error',
            'message': 'No query provided'
        }), 400
    
    try:
        # Forward the request to the agent API
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={
                'query': query_text,
                'session_id': session_id
            }
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f"API error: {response.status_code}"
            }), 500
        
        return jsonify(response.json())
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Search for CPT codes."""
    data = request.json
    search_term = data.get('search_term', '')
    
    if not search_term:
        return jsonify({
            'status': 'error',
            'message': 'No search term provided'
        }), 400
    
    try:
        # Forward the request to the agent API
        response = requests.post(
            f"{API_BASE_URL}/search",
            json={'search_term': search_term}
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f"API error: {response.status_code}"
            }), 500
        
        return jsonify(response.json())
    
    except Exception as e:
        logger.error(f"Error searching codes: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate a CPT code."""
    data = request.json
    code = data.get('code', '')
    
    if not code:
        return jsonify({
            'status': 'error',
            'message': 'No code provided'
        }), 400
    
    try:
        # Forward the request to the agent API
        response = requests.post(
            f"{API_BASE_URL}/validate",
            json={'code': code}
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f"API error: {response.status_code}"
            }), 500
        
        return jsonify(response.json())
    
    except Exception as e:
        logger.error(f"Error validating code: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze an ENT procedure description."""
    data = request.json
    procedure_text = data.get('procedure_text', '')
    candidate_codes = data.get('candidate_codes', [])
    
    if not procedure_text:
        return jsonify({
            'status': 'error',
            'message': 'No procedure text provided'
        }), 400
    
    try:
        # Forward the request to the agent API
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json={
                'procedure_text': procedure_text,
                'candidate_codes': candidate_codes
            }
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f"API error: {response.status_code}"
            }), 500
        
        return jsonify(response.json())
    
    except Exception as e:
        logger.error(f"Error analyzing procedure: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get a list of all conversations."""
    try:
        # Forward the request to the agent API
        response = requests.get(f"{API_BASE_URL}/conversations")
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f"API error: {response.status_code}"
            }), 500
        
        return jsonify(response.json())
    
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """Get details of a specific conversation."""
    try:
        # Forward the request to the agent API
        response = requests.get(f"{API_BASE_URL}/conversations/{session_id}")
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return jsonify({
                'status': 'error',
                'message': f"API error: {response.status_code}"
            }), 500
        
        return jsonify(response.json())
    
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/new_session', methods=['POST'])
def new_session():
    """Create a new session."""
    # Generate a new session ID
    session['session_id'] = str(uuid.uuid4())
    
    return jsonify({
        'status': 'success',
        'session_id': session['session_id']
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Try to connect to the agent API
        response = requests.get(f"{API_BASE_URL}/conversations")
        
        if response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f"API connection error: {response.status_code}"
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Web UI and API connection are healthy'
        })
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f"API connection error: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get("WEB_PORT", "5000"))
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=port, debug=os.environ.get("DEBUG", "False").lower() == "true")