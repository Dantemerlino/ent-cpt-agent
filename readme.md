# ENT CPT Code Agent

An AI-powered assistant for ENT (Ear, Nose, Throat) CPT code selection and validation.

## Overview

The ENT CPT Code Agent is a comprehensive tool designed to help medical professionals accurately determine the appropriate CPT codes for ENT procedures according to official coding rules. It uses LM Studio to power an intelligent assistant that can understand natural language descriptions of procedures and recommend the most appropriate codes.

## Features

- **Natural Language Understanding**: Describe procedures in plain English and get accurate code recommendations
- **CPT Code Search**: Search for codes based on keywords or descriptions
- **Code Validation**: Verify if a CPT code is valid and appropriate for a given procedure
- **Procedure Analysis**: Analyze detailed procedure descriptions to determine the correct codes
- **Educational Guidance**: Learn about coding rules, modifiers, and best practices
- **Multiple Interfaces**: Command-line, Web UI, and API options for different usage scenarios
- **Conversation History**: Save and review past conversations for reference

## Project Structure

```
ent-cpt-agent/
├── config.json               # Configuration file
├── data/                     # Data directory
│   └── CPT codes for ENT.xlsx # CPT code database
├── src/                      # Source code
│   ├── __init__.py           # Package marker
│   ├── main.py               # Main entry point
│   ├── agent/                # Agent components
│   │   ├── __init__.py
│   │   ├── cpt_database.py   # CPT code database handler
│   │   ├── ent_cpt_agent.py  # Main agent implementation
│   │   └── rules_engine.py   # Rule-based code selection logic
│   ├── api/                  # API components
│   │   ├── __init__.py
│   │   └── api_interface.py  # API interface implementation
│   ├── config/               # Configuration handling
│   │   ├── __init__.py
│   │   └── agent_config.py   # Configuration manager
│   ├── conversation/         # Conversation handling
│   │   ├── __init__.py
│   │   └── conversation_manager.py # Conversation state management
│   └── web/                  # Web interface
│       ├── __init__.py
│       ├── web_ui.py         # Web UI implementation
│       └── templates/        # Web templates
│           ├── __init__.py
│           ├── app.py        # Flask application
│           └── index.html    # Main HTML template
├── run_web_ui.py            # Web UI runner script
└── requirements.txt         # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- LM Studio desktop application
- CPT codes database (Excel format)

### Step 1: Set Up Environment

```bash
# Clone the repository
git clone https://github.com/dantemerlino/ent-cpt-agent.git
cd ent-cpt-agent

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure LM Studio

1. Install LM Studio from the [official website](https://lmstudio.ai/)
2. Launch LM Studio and download a suitable model (default: qwen2.5-14b-instruct)
3. Start the LM Studio server:
   ```bash
   lms server start
   ```

### Step 3: Prepare CPT Database

1. Place your "CPT codes for ENT.xlsx" file in the `data/` directory
2. Ensure the Excel file has the required columns: CPT Code, Description, Category, Related Codes

### Step 4: Initialize Configuration

```bash
# Initialize default configuration
python -m src.main init
```

This creates a `config.json` file with default settings. You can edit this file to adjust:
- The model name and parameters
- The path to the CPT database file
- Conversation storage settings
- Server host and port settings

## Usage

### Interactive Mode

```bash
python -m src.main interactive
```

This starts an interactive session where you can ask questions about ENT procedures and CPT codes.

### API Server Mode

```bash
python -m src.main server --host localhost --port 8000
```

This starts the API server, allowing you to integrate the agent with other applications.

### Web UI

```bash
python run_web_ui.py
```

This starts the web interface server. Navigate to http://localhost:5000 to access the web UI.

### Single Query Mode

```bash
python -m src.main query "What is the CPT code for bilateral myringotomy with tube insertion?"
```

This processes a single query and exits, useful for scripts and automation.

## Example Queries

- "What is the CPT code for tonsillectomy in adults?"
- "Compare CPT codes 69421 and 69424."
- "Explain the coding rules for 31231."
- "Analyze this procedure: Bilateral nasal endoscopy with maxillary antrostomy and tissue removal."
- "What codes are used for endoscopic sinus surgery?"

## Troubleshooting

### Common Issues

1. **LM Studio Connection Error**
   - Ensure LM Studio is running in server mode (`lms server start`)
   - Check the logs: `lms log stream`

2. **CPT Database Not Found**
   - Verify the path in `config.json` points to the correct location
   - Default path is relative to project root: `data/CPT codes for ENT.xlsx`

3. **Import Errors**
   - Make sure to run scripts as modules: `python -m src.main`
   - Check that all `__init__.py` files exist in the directories

4. **Web UI Not Loading**
   - Check if Flask is installed: `pip install flask`
   - Make sure template files are in the correct location

5. **Model Initialization Failed**
   - Verify the model exists in LM Studio
   - Reduce `max_tokens` in config if running into memory issues

### Logs

Check the `ent_cpt_agent.log` file for detailed error messages and debugging information.

## Advanced Configuration

### Changing the Language Model

You can change the LM Studio model used by the agent in the `config.json` file:

```json
{
  "model": {
    "name": "llama-3.1-8b-instruct",
    "temperature": 0.2,
    "max_tokens": 1024,
    "context_length": 8192
  }
}
```

Make sure the model is downloaded and available in LM Studio.

### Customizing the Web UI

The web interface can be customized by modifying:
- `src/web/templates/index.html` for the UI layout and styling
- `src/web/templates/app.py` for backend functionality

### Adding Custom Rules

The `RulesEngine` class in `src/agent/rules_engine.py` can be extended with new rules:

```python
# Example: Add a new rule for modifier 59
rule = CodeRule(
    rule_id="R006",
    description="Check for distinct procedural services (modifier 59)",
    conditions=[
        {"type": "distinct_procedure", "keywords": ["separate", "distinct", "different site"]}
    ],
    priority=5
)
rules_engine.add_rule(rule)
```

### Environment Variables

The following environment variables can be used to configure the application:

- `CONFIG_PATH`: Path to the configuration file (default: `config.json`)
- `WEB_PORT`: Port for the web UI server (default: `5000`)
- `WEB_HOST`: Host for the web UI server (default: `0.0.0.0`)
- `DEBUG`: Enable debug mode (default: `False`)

## API Documentation

The ENT CPT Code Agent provides a RESTful API for integration with other applications.

### Authentication

Currently, the API does not require authentication. For production use, consider adding API key validation.

### API Endpoints

#### Query Endpoint

```
POST /api/query
```

Request body:
```json
{
  "query": "What is the CPT code for tonsillectomy?",
  "session_id": "optional-session-id"
}
```

Response:
```json
{
  "status": "success",
  "message": "The CPT code for tonsillectomy depends on the patient's age...",
  "data": {
    "codes": ["42820", "42821"]
  },
  "session_id": "session-id"
}
```

#### Search Endpoint

```
POST /api/search
```

Request body:
```json
{
  "search_term": "endoscopy"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "codes": [
      {
        "code": "31231",
        "description": "Nasal endoscopy, diagnostic",
        "related_codes": ["31233", "31235"]
      },
      // More codes...
    ],
    "count": 10
  }
}
```

#### Validate Endpoint

```
POST /api/validate
```

Request body:
```json
{
  "code": "31231"
}
```

Response:
```json
{
  "status": "success",
  "message": "Nasal endoscopy, diagnostic",
  "data": {
    "valid": true,
    "description": "Nasal endoscopy, diagnostic"
  }
}
```

#### Analyze Endpoint

```
POST /api/analyze
```

Request body:
```json
{
  "procedure_text": "Bilateral myringotomy with tube insertion",
  "candidate_codes": ["69433", "69436"]
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "procedure_text": "Bilateral myringotomy with tube insertion",
    "recommended_codes": ["69436"],
    "excluded_codes": ["69433"],
    "explanations": [
      {
        "rule_id": "R002",
        "code": "69436",
        "message": "Code 69436 is appropriate for bilateral myringotomy with tube insertion under general anesthesia."
      }
    ]
  }
}
```

#### Health Check Endpoint

```
GET /api/health
```

Response:
```json
{
  "status": "success",
  "message": "Service is healthy",
  "details": {
    "model": "qwen2.5-14b-instruct",
    "database": "data/CPT codes for ENT.xlsx",
    "conversation_dir": "conversations"
  }
}
```

## Integration Examples

### Python

```python
import requests
import json

API_URL = "http://localhost:8000/api"

# Query the agent
response = requests.post(
    f"{API_URL}/query",
    json={
        "query": "What is the CPT code for septoplasty?",
        "session_id": None
    }
)
result = response.json()
print(result["message"])

# Use the returned session ID for follow-up questions
session_id = result["session_id"]
response = requests.post(
    f"{API_URL}/query",
    json={
        "query": "What if it's combined with turbinate reduction?",
        "session_id": session_id
    }
)
print(response.json()["message"])
```

### JavaScript

```javascript
async function queryAgent(question, sessionId = null) {
  const response = await fetch('http://localhost:8000/api/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: question,
      session_id: sessionId
    })
  });
  
  return await response.json();
}

// Example usage
async function main() {
  const result = await queryAgent('What is the CPT code for nasal endoscopy?');
  console.log(result.message);
  
  // Use the returned session ID for follow-up questions
  const sessionId = result.session_id;
  const followUp = await queryAgent('What if a biopsy is taken?', sessionId);
  console.log(followUp.message);
}

main();
```

## Extending the Project

The ENT CPT Code Agent is designed to be extensible. Here are some ways to enhance it:

1. **Add Support for More Specialties**: Adapt the framework to support other medical specialties beyond ENT.

2. **Enhance the Database**: Add more fields to the CPT code database, such as:
   - Reimbursement rates
   - Payer-specific guidelines
   - Historical coding data

3. **Integrate with EMR Systems**: Add connectors to popular Electronic Medical Record systems.

4. **Improve Model Capabilities**: Fine-tune the language model on medical coding scenarios.

5. **Add User Authentication**: Implement user accounts and secure API access.

## Contributing

We welcome contributions to improve the ENT CPT Code Agent. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure everything is working
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses LM Studio for AI language model processing
- Special thanks to the medical coding community for guidance
- Contributors who have helped improve the codebase
