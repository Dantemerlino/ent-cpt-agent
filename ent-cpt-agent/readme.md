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

## Installation

### Prerequisites

- Python 3.8+
- LM Studio desktop application
- CPT codes database (Excel format)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/Dantemerlino/ent-cpt-agent.git
cd ent-cpt-agent

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize default configuration
python -m src.main init
```

For detailed installation instructions, see the [Installation Guide](docs/installation_guide.md).

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
python -m src.web.web_ui
```

This starts the web interface server. Navigate to http://localhost:5000 to access the web UI.

### Single Query Mode

```bash
python -m src.main query "What is the CPT code for bilateral myringotomy with tube insertion?"
```

This processes a single query and exits, useful for scripts and automation.

## Documentation

- [Installation Guide](docs/installation_guide.md): Detailed installation instructions
- [Usage Examples](docs/usage_examples.md): Examples of how to use the agent
- [API Documentation](docs/api_docs.md): Documentation for the REST API
- [Project summary](docs/PROJECT_SUMMARY.md): Project summary

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses LM Studio for AI language model processing
- Special thanks to the medical coding community for guidance
