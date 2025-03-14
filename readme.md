# ENT CPT Code Agent v2.0

An enhanced AI-powered assistant for ENT (Ear, Nose, Throat) CPT code selection and validation using LM Studio's advanced capabilities.

## What's New in Version 2.0

The ENT CPT Code Agent has been completely rebuilt to leverage the latest features from LM Studio:

- **Agent-Based Architecture**: Uses "tools" to perform specialized functions like code search, validation, and analysis
- **Structured Output**: Returns well-structured data for better integration with other systems
- **Enhanced CPT Database Handling**: More robust detection of CPT codes with flexible column naming
- **Improved Rules Engine**: Better handling of bundled codes, bilateral procedures, and other coding rules
- **Streaming Support**: Real-time response generation for a better user experience
- **OpenAI API Compatibility**: Works with any client that uses the OpenAI API format
- **Advanced Error Handling**: More resilient to missing files and corrupt data

## Overview

The ENT CPT Code Agent is a comprehensive tool designed to help medical professionals accurately determine the appropriate CPT codes for ENT procedures according to official coding rules. It uses LM Studio to power an intelligent assistant that can understand natural language descriptions of procedures and recommend the most appropriate codes.

## Features

- **Natural Language Understanding**: Describe procedures in plain English and get accurate code recommendations
- **CPT Code Search**: Search for codes based on keywords or descriptions with enhanced matching
- **Code Validation**: Verify if a CPT code is valid and appropriate for a given procedure
- **Procedure Analysis**: Analyze detailed procedure descriptions to determine the correct codes
- **Code Comparison**: Compare two CPT codes and get explanations of their differences
- **Educational Guidance**: Learn about coding rules, modifiers, and best practices
- **Multiple Interfaces**: Command-line, Web UI, and comprehensive API options
- **Conversation History**: Save and review past conversations for reference
- **Streaming Responses**: Get results in real-time as they're being generated

## Installation

### Prerequisites

- Python 3.8+
- LM Studio desktop application with a suitable model
- CPT codes database (Excel format)

### Step 1: Set Up Environment

```bash
# Clone the repository
git clone https://github.com/dantemerlino/ent-cpt-agent.git
cd ent-cpt-agent

# Create a virtual environment
cd ent-cpt-agent
# python -m venv venv # Only do this the first time you make your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure LM Studio

1. Install LM Studio from the [official website](https://lmstudio.ai/)
2. Launch LM Studio and download a suitable model:
   - Recommended: qwen2.5-14b-instruct (best performance)
   - Alternatives: Llama 3.1-70B, DeepSeek R1 Distill-7B
3. Start the LM Studio server:
   ```bash
   lms server start
   ```

### Step 3: Prepare CPT Database

1. Place your "CPT codes for ENT.xlsx" file in the `data/` directory
2. Ensure the Excel file has the required columns: CPT Code (or similar), Description, Category, Related Codes

### Step 4: Initialize Configuration

```bash
# Initialize default configuration
cp config-example.json config.json
```

Edit the `config.json` file to adjust:
- The model name and parameters
- The path to the CPT database file
- Conversation storage settings
- Server host and port settings
- Tool configurations

## Usage

### Web UI Mode

The easiest way to use the ENT CPT Code Agent is through the Web UI:

```bash
python run_web_ui.py
```

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

The Rules Engine can be extended with new rules by modifying the `initialize_rules` method in `src/agent/rules_engine.py`.

### Environment Variables

The following environment variables can be used to configure the application:

- `CONFIG_PATH`: Path to the configuration file (default: `config.json`)
- `WEB_PORT`: Port for the web UI server (default: `5000`)
- `WEB_HOST`: Host for the web UI server (default: `0.0.0.0`)
- `DEBUG`: Enable debug mode (default: `False`)
- `CPT_DB_PATH`: Path to the CPT database file (overrides config)
- `MODEL_NAME`: Name of the model to use (overrides config)

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