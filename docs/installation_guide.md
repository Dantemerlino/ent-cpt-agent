# ENT CPT Code Agent - Installation & Setup Guide

This guide will walk you through the installation and setup process for the ENT CPT Code Agent system.

## 1. Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.8+**: Required for running the application
- **pip**: Python package manager
- **LM Studio**: Required for running the language models locally
- **Excel**: For viewing/editing the CPT codes database

## 2. Installation

### 2.1 Clone the Repository

```bash
git clone https://github.com/your-organization/ent-cpt-agent.git
cd ent-cpt-agent
```

### 2.2 Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` file should include:

```
lmstudio
pandas
openpyxl
flask
fastapi
uvicorn
requests
python-dotenv
logging
argparse
```

## 3. Configuration

### 3.1 Initialize Default Configuration

```bash
python main-app.py init
```

This will create a default `config.json` file with the following structure:

```json
{
  "model": {
    "name": "qwen2.5-7b-instruct",
    "temperature": 0.2,
    "max_tokens": 1024,
    "context_length": 8192
  },
  "cpt_database": {
    "file_path": "CPT codes for ENT.xlsx",
    "sheet_name": "Sheet1"
  },
  "agent": {
    "log_level": "INFO",
    "save_conversations": true,
    "conversation_dir": "conversations"
  },
  "server": {
    "host": "localhost",
    "port": 8000,
    "enable_api": false
  }
}
```

### 3.2 Prepare the CPT Codes Database

1. Ensure that the `CPT codes for ENT.xlsx` file is in the root directory
2. The Excel file should have the following columns:
   - CPT Code
   - Description
   - Category
   - Related Codes (comma-separated)

### 3.3 Set Up LM Studio

1. Install and launch LM Studio
2. Download the recommended model (default: qwen2.5-14b-instruct)
3. Ensure LM Studio's Python SDK is properly installed:
   
   ```bash
   pip install lmstudio
   ```

4. Set up LM Studio to run in server mode:
   
   ```bash
   lms server start
   ```

## 4. Running the Application

### 4.1 Interactive Mode

Run the application in interactive command-line mode:

```bash
python main-app.py interactive
```

This will start an interactive session where you can ask questions about ENT procedures and CPT codes.

### 4.2 API Server Mode

Run the application as an API server:

```bash
python main-app.py server --host localhost --port 8000
```

This will start the API server on the specified host and port.

### 4.3 Web UI Mode

Run the web UI application:

```bash
# Set environment variables for API connection
export API_HOST=localhost
export API_PORT=8000
export WEB_PORT=5000
export DEBUG=False

# Run the web UI
python web_ui.py
```

Then open your web browser and navigate to `http://localhost:5000` to access the web UI.

### 4.4 Single Query Mode

Process a single query and exit:

```bash
python main.py query "What is the CPT code for tympanostomy tube insertion?"
```

## 5. Advanced Configuration

### 5.1 Changing the Language Model

You can change the LM Studio model used by the agent in the `config.json` file:

```json
{
  "model": {
    "name": "llama-3.1-8b-instruct",
    "temperature": 0.2,
    "max_tokens": 1024
  }
}
```

Ensure that the model is downloaded and available in LM Studio.

### 5.2 Logging Configuration

You can adjust the logging level in the `config.json` file:

```json
{
  "agent": {
    "log_level": "DEBUG"
  }
}
```

Available logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### 5.3 Conversation Storage

By default, conversations are stored in the `conversations` directory. You can change this in the `config.json` file:

```json
{
  "agent": {
    "save_conversations": true,
    "conversation_dir": "custom_conversations_dir"
  }
}
```

## 6. API Documentation

When running in server mode, the API documentation is available at:

- OpenAPI UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

### 6.1 API Endpoints

- `POST /api/query`: Submit a query to the agent
- `POST /api/search`: Search for CPT codes
- `POST /api/validate`: Validate a CPT code
- `POST /api/analyze`: Analyze a procedure description
- `GET /api/conversations`: List all conversations
- `GET /api/conversations/{session_id}`: Get a specific conversation
- `DELETE /api/conversations/{session_id}`: Delete a specific conversation

## 7. Troubleshooting

### 7.1 Common Issues

#### LM Studio Connection Issues

If you encounter issues connecting to LM Studio:

1. Ensure LM Studio is running in server mode: `lms server start`
2. Check the logs for any error messages: `lms log stream`
3. Verify the model is properly loaded in LM Studio

#### CPT Database Issues

If you encounter issues with the CPT database:

1. Ensure the `CPT codes for ENT.xlsx` file is in the correct location
2. Verify the Excel file has the required columns
3. Check for any error messages in the logs

#### API Connection Issues

If the web UI cannot connect to the API:

1. Ensure the API server is running: `python main.py server`
2. Verify the API host and port settings are correct
3. Check for any firewall issues that might block the connection

### 7.2 Logs

Logs are saved to `ent_cpt_agent.log` by default. You can check this file for detailed error messages and debugging information.

## 8. Contributing

We welcome contributions to improve the ENT CPT Code Agent. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 9. License

This project is licensed under the MIT License - see the LICENSE file for details.
