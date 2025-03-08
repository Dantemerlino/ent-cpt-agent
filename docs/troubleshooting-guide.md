# Troubleshooting Guide for ENT CPT Code Agent

This guide addresses common issues when setting up and running the ENT CPT Code Agent.

## Common Error #1: Module Import Errors

### Symptoms
```
ImportError: cannot import name 'RulesEngine' from 'src.agent.ent_cpt_agent'
```
or
```
ImportError: attempted relative import with no known parent package
```

### Solution

1. **Fix Class Definition Locations**:
   - Ensure `CPTCodeDatabase` is only defined in `src/agent/cpt_database.py`
   - Ensure `RulesEngine` is only defined in `src/agent/rules_engine.py`
   - Ensure `ENTCPTAgent` is only defined in `src/agent/ent_cpt_agent.py`

2. **Add Proper Imports**:
   - In `src/agent/ent_cpt_agent.py`, add:
     ```python
     from .cpt_database import CPTCodeDatabase
     from .rules_engine import RulesEngine
     ```

3. **Run as a Module**:
   - Always run the main script as a module: `python -m src.main` instead of `python src/main.py`

## Common Error #2: Flask App Not Found

### Symptoms
```
NameError: name 'app' is not defined
```

### Solution

1. **Create Flask App Definition**:
   - Create a file at `src/web/templates/app.py` with a Flask app definition
   - Add `from src.web.templates.app import app` to `run_web_ui.py`

2. **Alternative Solution**:
   - Define Flask app directly in `run_web_ui.py`:
     ```python
     from flask import Flask
     app = Flask(__name__, template_folder='src/web/templates')
     ```

## Common Error #3: CPT Database Not Found

### Symptoms
```
FileNotFoundError: [Errno 2] No such file or directory: 'CPT codes for ENT.xlsx'
```

### Solution

1. **Check File Location**:
   - Ensure the Excel file is in the correct location (project root or data directory)

2. **Update Config Path**:
   - Modify `config.json` to use the correct path:
     ```json
     "cpt_database": {
       "file_path": "data/CPT codes for ENT.xlsx",
       "sheet_name": "Sheet1"
     }
     ```

3. **Use Absolute Path**:
   - If issues persist, use an absolute path in the config file

## Common Error #4: LM Studio Connection Issues

### Symptoms
```
ConnectionError: Failed to connect to LM Studio server
```

### Solution

1. **Start LM Studio Server**:
   ```bash
   lms server start
   ```

2. **Check Model Availability**:
   - Ensure the model specified in `config.json` is downloaded in LM Studio
   - Try a different model if issues persist

3. **Verify Installation**:
   ```bash
   pip install lmstudio
   ```

## Common Error #5: Multiple Class Definitions

### Symptoms
```
ImportError: cannot import name 'CPTCodeDatabase' from 'src.agent.cpt_database'
```
But you see the class defined in multiple files.

### Solution

1. **Check File Contents**:
   - Make sure each class is defined only once in the appropriate file
   - Remove duplicate class definitions

2. **Clean Project Structure**:
   ```
   src/agent/cpt_database.py → CPTCodeDatabase class only
   src/agent/rules_engine.py → RulesEngine class only
   src/agent/ent_cpt_agent.py → ENTCPTAgent class only
   ```

## Common Error #6: Web UI Template Issues

### Symptoms
```
TemplateNotFound: index.html
```

### Solution

1. **Check Template Location**:
   - Ensure `index.html` is in the correct directory (`src/web/templates/`)

2. **Update Template Folder Path**:
   ```python
   app = Flask(__name__, 
              template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__))))
   ```

## Common Error #7: Session Handling Issues

### Symptoms
- Conversation history not maintained
- New session created for each query

### Solution

1. **Create Conversations Directory**:
   ```bash
   mkdir conversations
   ```

2. **Check Permissions**:
   - Ensure the application has write permissions to the conversations directory

3. **Verify Session ID Handling**:
   - Ensure the session ID is being passed correctly between requests

## Quick Fixes Checklist

1. ✅ Create proper imports in `ent_cpt_agent.py`
2. ✅ Create Flask app in `src/web/templates/app.py`
3. ✅ Update imports in `run_web_ui.py`
4. ✅ Verify CPT database path in `config.json`
5. ✅ Start LM Studio server before running the application
6. ✅ Run the main script as a module (`python -m src.main`)
7. ✅ Create all necessary directories (`data/`, `conversations/`)

## Debug Mode

To get more detailed error information, enable debug mode:

```bash
# For the web UI
export DEBUG=true
python run_web_ui.py

# For the API server
python -m src.main server --debug
```

## Advanced Debugging

If you're still experiencing issues, try:

1. **Check Logs**:
   - Review `ent_cpt_agent.log` for detailed error messages

2. **Run with Verbose Logging**:
   ```bash
   python -m src.main --log-level DEBUG interactive
   ```

3. **Validate Project Structure**:
   ```bash
   find src -type f -name "*.py" | sort
   ```

4. **Test Each Component Separately**:
   ```bash
   # Test database loading
   python -c "from src.agent.cpt_database import CPTCodeDatabase; db = CPTCodeDatabase('data/CPT codes for ENT.xlsx'); print(f'Loaded {len(db.code_descriptions)} codes')"
   
   # Test rules engine
   python -c "from src.agent.rules_engine import RulesEngine; engine = RulesEngine(); print(f'Loaded {len(engine.rules)} rules')"
   ```

If you continue to experience issues, please check the GitHub repository for the most up-to-date troubleshooting information or open an issue with the specific error details.
