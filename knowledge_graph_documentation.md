# ENT CPT Code Agent - Knowledge Graph Documentation

This document provides an overview of the ENT CPT Code Agent system architecture based on the knowledge graph created through system exploration.

## System Overview

The **ENT CPT Code Agent** is an AI-powered assistant designed to help medical professionals accurately determine appropriate CPT (Current Procedural Terminology) codes for ENT (Ear, Nose, Throat) procedures according to official coding guidelines. The system uses LM Studio to provide an intelligent interface that can understand natural language descriptions of procedures and recommend the most appropriate codes based on medical coding rules.

## Key Components

### Core Components

| Component | Description |
|-----------|-------------|
| **ENTCPTAgent** | Central component that integrates the LM Studio model for natural language understanding, provides tool functions for CPT code operations, processes queries and generates responses. |
| **CPTCodeDatabase** | Manages loading, storing, and querying of CPT codes from an Excel file, providing functionality for searching codes by description or keywords, retrieving code details, and validating codes. |
| **RulesEngine** | Implements medical coding rules for CPT code selection, handling bundled procedures, bilateral procedures, multiple procedures, and medical necessity validation. |
| **ConversationManager** | Manages conversation history storage and retrieval, tracks messages, and extracts CPT codes from conversation text. |
| **Conversation** | Represents individual conversations between users and the agent, including message history and metadata. |

### Configuration & Data Components

| Component | Description |
|-----------|-------------|
| **AgentConfig** | Manages configuration settings for the system, handling loading, saving, and accessing configuration from a JSON file. |
| **CPT Data Storage** | Stores CPT code data in Excel format, contains code descriptions, categories, and related information. |
| **CPT Codes** | 5-digit numeric codes used for medical procedure billing and coding, specific to ENT procedures. |
| **FAISS Index** | Used for semantic search of CPT codes, stores embeddings of CPT code descriptions for efficient similarity search. |

### Interface Components

| Component | Description |
|-----------|-------------|
| **Web UI** | Web-based user interface built with Flask, providing a chat interface for interacting with the agent. |
| **Web Server** | Flask-based web server that hosts the Web UI, supporting ngrok tunneling for remote access. |
| **API Interface** | REST API for the ENT CPT Code Agent, providing endpoints for submitting queries, searching and validating codes, and analyzing procedures. |
| **Tools** | Functions provided to the language model for specific tasks, used by ENTCPTAgent to perform specific actions. |

### Integration Components

| Component | Description |
|-----------|-------------|
| **LM Studio Integration** | The system integrates with LM Studio through its Python SDK, using OpenAI client to connect to LM Studio's local API endpoint. |

## Component Relationships

### System Structure

- The **ENT CPT Code Agent** contains all major components: CPTCodeDatabase, RulesEngine, ENTCPTAgent, ConversationManager, Web UI, API Interface, AgentConfig, Web Server, Tools, and CPT Data Storage.
- The system uses **LM Studio Integration** for natural language understanding and response generation.

### Data Flow

- **ENTCPTAgent** uses CPTCodeDatabase, RulesEngine, ConversationManager, LM Studio Integration, AgentConfig, Tools, and FAISS Index.
- **CPTCodeDatabase** stores CPT Codes and accesses CPT Data Storage.
- **CPTCodeDatabase** provides CPT Code Search Results.
- **ENTCPTAgent** generates CPT Code Search Results.
- **ConversationManager** manages Conversation objects and stores Conversation History.

### Interface Interactions

- **Web UI** communicates with ENTCPTAgent, displays CPT Code Search Results and Conversation History.
- **Web UI** runs on Web Server and exposes API Interface.
- **Web Server** hosts API Interface.
- **API Interface** provides access to ENTCPTAgent and exposes Tools.

## System Workflow

1. User submits a query about ENT procedures through the Web UI or API Interface.
2. The query is processed by ENTCPTAgent, which uses LM Studio Integration for natural language understanding.
3. ENTCPTAgent leverages CPTCodeDatabase to search for relevant CPT codes using keyword search and semantic search (FAISS Index).
4. RulesEngine analyzes the procedure description and candidate codes to determine appropriate codes based on coding guidelines.
5. ENTCPTAgent generates a response with recommended CPT codes and explanations.
6. ConversationManager tracks the interaction in Conversation History.
7. The response is returned to the user through the same interface that received the query.

## Configuration

The system is configured via a config.json file managed by AgentConfig. Key configuration settings include:

- Model parameters (name, temperature, max_tokens)
- CPT database file path
- Conversation directory path
- Server host and port settings

## Running the Application

The main entry point for the application is run_web_ui.py, which starts the Web Server with the following default settings:

- Host: 0.0.0.0 (configurable via WEB_HOST environment variable)
- Port: 5000 (configurable via WEB_PORT environment variable)
- Debug mode: False (configurable via DEBUG environment variable)

The application also supports ngrok tunneling for remote access.

---

This documentation provides a high-level overview of the ENT CPT Code Agent system architecture based on knowledge graph exploration. For detailed implementation details, refer to the source code and comments in the respective files.
