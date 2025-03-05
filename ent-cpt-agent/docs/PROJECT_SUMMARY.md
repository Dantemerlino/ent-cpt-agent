# ENT CPT Code Agent - Project Summary

## Project Overview

The ENT CPT Code Agent is a comprehensive AI-powered assistant designed to help medical professionals accurately determine the appropriate CPT codes for ENT (Ear, Nose, Throat) procedures according to official coding guidelines. The system leverages LM Studio to provide an intelligent interface that can understand natural language descriptions of procedures and recommend the most appropriate codes based on medical coding rules.

## Key Components

### 1. CPT Code Database

The `CPTCodeDatabase` class manages the loading, storing, and querying of CPT codes from an Excel file. It provides functionality for:
- Searching for codes by description or keywords
- Retrieving code details and validating codes
- Organizing codes by category
- Identifying related codes

### 2. Rules Engine

The `RulesEngine` class implements medical coding rules for CPT code selection, handling:
- Bundled procedures (codes that should not be reported together)
- Bilateral procedures (requiring modifier 50)
- Multiple procedures (requiring modifier 51)
- Medical necessity validation
- Custom rule creation and application

### 3. Conversation Manager

The `ConversationManager` and `Conversation` classes handle user interactions, managing:
- Conversation history storage and retrieval
- Message tracking and organization
- Conversion between internal representation and LM Studio chat format
- CPT code extraction from conversation text

### 4. Agent Core

The `ENTCPTAgent` class serves as the central component, integrating:
- The LM Studio model for natural language understanding
- Tool functions for CPT code operations
- Query processing and response generation
- Interactive session management

### 5. API Interface

The `APIInterface` class provides a REST API for the agent, offering endpoints for:
- Submitting queries to the agent
- Searching for and validating CPT codes
- Analyzing procedure descriptions
- Managing conversation sessions

### 6. Web UI

A web-based user interface built with Flask that provides:
- A chat interface for interacting with the agent
- Tools for code search, validation, and analysis
- Conversation history management
- Detected code tracking and display

## Architecture Design

The project follows a modular architecture with clear separation of concerns:

1. **Data Layer**: CPT code database and persistence
2. **Business Logic Layer**: Rules engine and agent core
3. **Presentation Layer**: API interface and web UI
4. **Integration Layer**: LM Studio integration

Components communicate through well-defined interfaces, allowing for:
- Independent testing and development
- Easy replacement or enhancement of individual components
- Flexible deployment options (CLI, API, web)

## Integration with LM Studio

The system integrates with LM Studio through its Python SDK. Key integration points:

### LLM Initialization

```python
# Configure and load the model
self.model = lms.llm(self.model_name, config={
    "temperature": self.model_temperature,
    "maxTokens": self.model_max_tokens
})
```

### Tool Function Registration

The agent provides tool functions that the language model can use:
- `search_cpt_codes`: Search for CPT codes based on a procedure description
- `validate_cpt_code`: Validate if a CPT code exists and is correct
- `get_category_codes`: Get all CPT codes for a specific category
- `explain_coding_rules`: Explain the rules for using a specific CPT code
- `analyze_procedure`: Analyze a procedure description to determine appropriate codes

### Query Processing

```python
# Define the tool functions
tools = [
    self.search_cpt_codes,
    self.validate_cpt_code,
    self.get_category_codes,
    self.explain_coding_rules,
    self.analyze_procedure
]

# Let the model use tools to process the query
result = self.model.act(
    chat,
    tools,
    on_message=lambda msg: conversation.add_message("assistant", msg.content) if conversation else None
)
```

## Getting Started

1. Install the requirements: `pip install -r requirements.txt`
2. Initialize the configuration: `python main.py init`
3. Place the CPT code database file in the data directory
4. Run the application in interactive mode: `python main.py interactive`

## Development Workflow

To further develop and extend the project:

1. **Setup the Development Environment**:
   ```bash
   # Clone the repository
   git clone <repository-url> ent-cpt-agent
   cd ent-cpt-agent
   
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

2. **Run Tests**:
   ```bash
   # Run all tests
   python -m unittest discover
   
   # Run specific test file
   python -m unittest tests.test_cpt_database
   ```

3. **Add New Features**:
   - Create or modify code in the `src` directory
   - Add tests in the `tests` directory
   - Update documentation as needed

4. **Build and Package**:
   ```bash
   # Build the package
   python setup.py sdist bdist_wheel
   
   # Install locally for testing
   pip install -e .
   ```

## Extending the Project

The ENT CPT Code Agent is designed to be extensible. Here are some ways to enhance it:

1. **Add New Rules**: Create new `CodeRule` instances in the `RulesEngine` for additional coding guidelines.

2. **Enhance the Database**: Add more fields to the CPT code database to support additional information, such as:
   - Reimbursement rates
   - Payer-specific guidelines
   - Historical coding data

3. **Improve the UI**: Enhance the web interface with additional features:
   - Visualization of coding relationships
   - Interactive procedure diagrams
   - Documentation templates

4. **Extend to Other Specialties**: Adapt the framework to support other medical specialties beyond ENT.

## Deployment Options

The ENT CPT Code Agent supports multiple deployment scenarios:

1. **Standalone Application**: Run the interactive CLI or web UI locally for individual users.

2. **API Server**: Deploy as a service that other applications can integrate with via REST API.

3. **Embedded Component**: Integrate the core logic into existing electronic medical record (EMR) systems.

## Conclusion

The ENT CPT Code Agent provides a comprehensive solution for ENT procedure coding assistance. Its modular design, integration with LM Studio, and extensible architecture make it a powerful tool for medical professionals and coding specialists.
