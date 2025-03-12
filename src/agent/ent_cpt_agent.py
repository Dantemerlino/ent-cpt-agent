"""
ENT CPT Agent v2.1 - Enhanced implementation with key indicator and standard charge prioritization.

This module implements a more powerful ENT CPT Code Agent using:
- Agent-based architecture with tool functions
- Structured responses for code validation
- Enhanced parameter management
- Better error handling and database interaction
- Key indicator prioritization
- Standard charge-based sorting

File name and location: ent-cpt-agent/src/agent/ent_cpt_agent.py

"""


import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import pandas as pd
import logging
import json
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import faiss
from pydantic import BaseModel, Field
logger = logging.getLogger("ent_cpt_agent")

class CPTCode(BaseModel):
    """Pydantic model for a CPT code with its details."""
    code: str
    description: str
    related_codes: List[str] = Field(default_factory=list)
    category: str = ""
    key_indicator: bool = False
    standard_charge: float = 0.0
    recommended: bool = True
    reason: str = ""

class CPTSearchResult(BaseModel):
    """Pydantic model for CPT code search results."""
    codes: List[CPTCode]
    query: str
    total_results: int
    status: str = "success"
    message: str = ""

class ProcedureAnalysis(BaseModel):
    """Pydantic model for procedure analysis results."""
    procedure: str
    recommended_codes: List[CPTCode]
    excluded_codes: List[CPTCode] = Field(default_factory=list)
    bilateral: bool = False
    multiple_procedures: bool = False
    bundled_codes: bool = False
    explanation: str
    status: str = "success"

class HealthCheck(BaseModel):
    """Pydantic model for health check responses."""
    status: str = "healthy"
    model: str
    database: str
    database_version: str
    codes_loaded: int
    key_indicators_loaded: int = 0
    standard_charges_loaded: int = 0
    server_version: str = "2.1.0"

class ENTCPTAgent:
    """
    Agent for processing ENT procedure queries and determining appropriate CPT codes.
    Uses LM Studio to enhance natural language understanding and code selection.
    Now with key indicator and standard charge prioritization.
    """
    def __init__(self, config, conversation_manager=None):
        """Initialize the ENT CPT Agent."""
        logger.info(f"Initializing ENTCPTAgent with config type: {type(config)}")
        
        # Handle string config path
        if isinstance(config, str):
            from src.config.agent_config import AgentConfig
            logger.info(f"Loading config from path: {config}")
            self.config = AgentConfig(config)
        else:
            # Config is already an object
            self.config = config
            
        # Get configuration values
        self.model_name = self.config.get("model", "name")
        self.model_temperature = float(self.config.get("model", "temperature"))
        self.model_max_tokens = int(self.config.get("model", "max_tokens"))
        self.cpt_db_path = self.config.get("cpt_database", "file_path")
        
        
        # Initialize OpenAI client for LM Studio
        server_config = self.config.get("server")

        base_url = server_config.get("lm_studio_base_url", "http://localhost:1234/v1")
        api_key = server_config.get("lm_studio_api_key", "lm-studio")
        
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        logger.info(f"Connected to LM Studio at {base_url}")
      
        # Initialize components
        self.cpt_db = None
        self.procedure_search = None
        self.validate_cpt_code = None
        self.analyze_procedure = None
        self.get_explanation = None
        try:
            # First try to import from same directory
            from src.agent.cpt_database import CPTCodeDatabase
            self.cpt_db = CPTCodeDatabase(self.cpt_db_path)
        except ImportError:
            try:
                # Try relative import
                from .cpt_database import CPTCodeDatabase
                self.cpt_db = CPTCodeDatabase(self.cpt_db_path)
            except ImportError:
                try:
                    # Try direct import (if in same directory)
                    import sys
                    import os
                    sys.path.append(os.path.dirname(__file__))
                    from cpt_database import CPTCodeDatabase
                    self.cpt_db = CPTCodeDatabase(self.cpt_db_path)
                except ImportError:
                    raise ImportError("Could not import CPTCodeDatabase. Make sure cpt_database.py is in the correct location.")
            
        self.rules_engine = None
        try:
            # First try to import from same directory
            from src.agent.rules_engine import RulesEngine
            self.rules_engine = RulesEngine()
        except ImportError:
            try:
                # Try relative import
                from .rules_engine import RulesEngine
                self.rules_engine = RulesEngine()
            except ImportError:
                try:
                    # Try direct import (if in same directory)
                    import sys
                    import os
                    sys.path.append(os.path.dirname(__file__))
                    from rules_engine import RulesEngine
                    self.rules_engine = RulesEngine()
                except ImportError:
                    raise ImportError("Could not import RulesEngine. Make sure rules_engine.py is in the correct location.")
            
        self.conversation_manager = conversation_manager
        
        logger.info("ENTCPTAgent v2.1 initialized successfully with key indicator and standard charge support")
        # Load CPT codes database
        self.cpt_db = pd.read_excel(self.cpt_db_path)
        
        # Initialize embedding model
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Load or create FAISS index
        self.faiss_index, self.embeddings = self._init_faiss_index()

    def _init_faiss_index(self):
        BASE_DIR = Path(__file__).resolve().parents[2]  # Moves two directories up from ent_cpt_agent.py
        embedding_path = BASE_DIR / 'data' / 'cpt_embeddings.npy'
        index_path = BASE_DIR / 'data' / 'faiss_index.idx'

        if embedding_path.exists() and index_path.exists():
            embeddings_array = np.load(str(embedding_path))
            faiss_index = faiss.read_index(str(index_path))
            logger.info("Loaded pre-built FAISS index.")
        else:
            descriptions = self.cpt_db['description'].tolist()
            embeddings = self.embed_model.encode(descriptions, show_progress_bar=True)
            embeddings_array = np.array(embeddings).astype('float32')

            # Initialize FAISS index
            faiss_index = faiss.IndexFlatL2(embeddings_array.shape[1])
            faiss_index.add(embeddings_array)

            # Save embeddings and index
            np.save(embedding_path, embeddings_array)
            faiss.write_index(faiss_index, str(index_path))

            logger.info("Created new FAISS index and embeddings.")

        return faiss_index, embeddings_array
    def _call_llm(self, messages: List[Dict[str, str]], config: Optional[Dict[str, Any]] = None) -> str:
            """
            Call the LLM with messages and configuration.
            
            Args:
                messages: A list of message dictionaries (role, content)
                config: Optional configuration parameters
                
            Returns:
                The LLM's response text
            """
            try:
                # Apply default configuration values
                call_config = {
                    "temperature": self.model_temperature,
                    "max_tokens": self.model_max_tokens
                }
                
                # Override with any provided configuration
                if config:
                    call_config.update(config)
                
                # Call the model
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    **call_config
                )
                
                # Return the text content
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
                return f"Error: {str(e)}"
    
    def procedure_search(self, query: str) -> Dict[str, Any]:
        """
        Search for CPT codes based on a query, with prioritization by key indicators and standard charges.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            # Use the search_codes method from CPTCodeDatabase which searches across all columns
            limit = 10
            results = self.cpt_db.search_codes(query, limit=limit)
    
            # Convert results to CPTCode objects, mapping Excel columns to expected fields
            cpt_codes = []
            for result in results:
                # Map the Excel columns to our expected fields
                code = result.get("CPT_code") or result.get("code")
                description = result.get("description", "")
                category = result.get("category", "")
    
                # Convert key_indicator to boolean (e.g., "Yes" becomes True)
                key_indicator_raw = result.get("key_indicator", "No")
                key_indicator = str(key_indicator_raw).strip().lower() in ("yes", "true", "1")
    
                # Get standard charge from the appropriate column (e.g., "standard_charge|gross")
                standard_charge = result.get("standard_charge")
    
                # Create CPTCode object
                cpt_code = CPTCode(
                    code=str(code),
                    description=description,
                    related_codes=result.get("related_codes", []),
                    category=category,
                    key_indicator=key_indicator,
                    standard_charge=float(standard_charge)
                )
                cpt_codes.append(cpt_code)
    
            # Create search result
            search_result = CPTSearchResult(
                codes=cpt_codes,
                query=query,
                total_results=len(results),
            )
    
            return {"status": "success", "data": search_result.dict()}
    
        except Exception as e:
            logger.error(f"Error searching for CPT codes: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query": query,
                "total_results": 0,
                "codes": []
            }
    
    def semantic_search(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search against CPT descriptions.
        """
        query_embedding = self.embed_model.encode([query])
        distances, indices = self.faiss_index.search(query_embedding, top_n)
        
        results = []
        for idx in indices[0]:
            code_info = self.cpt_db.iloc[idx]
            result = {
                "code": str(code_info['CPT_code']),
                "description": code_info['description'],
                "category": code_info['category'],
                "key_indicator": code_info.get('key_indicator', False),
                "standard_charge": code_info.get('standard_charge', 0.0)
            }
            results.append(result)

        return results
    def health_check(self) -> Dict[str, Any]:
        """
        Get health and status information about the agent, including key indicator and standard charge metrics.
        
        Returns:
            Dictionary with health information
        """
        try:
            # Get database stats
            db_stats = {}
            # Change this line - use .empty attribute to check if DataFrame is empty
            total_codes = len(self.cpt_db) if hasattr(self, 'cpt_db') and not self.cpt_db.empty else 0
            
            # Fix these lines too - you need to access these as DataFrame attributes, not properties
            # If these are actually columns in your DataFrame:
            key_indicators = self.cpt_db['key_indicator'].sum() if hasattr(self, 'cpt_db') and not self.cpt_db.empty else 0
            standard_charges = len(self.cpt_db[self.cpt_db['standard_charge'] > 0]) if hasattr(self, 'cpt_db') and not self.cpt_db.empty else 0
            
            health = HealthCheck(
                status="healthy",
                model=self.model_name,
                database=self.cpt_db_path,
                database_version=getattr(self.cpt_db, "version", "Unknown"),
                codes_loaded=total_codes,
                key_indicators_loaded=key_indicators,
                standard_charges_loaded=standard_charges
            )
            
            return health.dict()
        
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "error",
                "message": str(e),
                "model": self.model_name,
                "database": self.cpt_db_path,
                "codes_loaded": 0
            }
            
    
    def get_method_for_attribute(self, obj, attribute_name):
        """
        Helper method to find a method that might have a different name but related function.
        """
        possible_methods = [
            attribute_name,
            f"get_{attribute_name}",
            f"get_{attribute_name}s",
            f"list_{attribute_name}s",
            f"list_{attribute_name}"
        ]
        
        for method_name in possible_methods:
            if hasattr(obj, method_name) and callable(getattr(obj, method_name)):
                return getattr(obj, method_name)
        
        return None
        
    def process_query(self, query: str, conversation=None) -> str:
        logger.info(f"Processing query with semantic search: {query}")
        try:
            # Get conversation history if available
            messages = []
            
            # Step 1: Run the user's query through an LLM, asking the model to translate into specific ENT procedure terms
            translate_prompt = (
                f"Translate the following query into specific otolaryngology procedure terminology for CPT coding purposes. " 
                f"Focus on exact procedure names, anatomical sites, and technical terms used in ENT CPT coding. " 
                f"Be concise. Do not add any preamble or conclusion. Use standard medical terminology. " 
                f"Query: {query}"
            )
            messages.append({"role": "user", "content": translate_prompt})
            response1 = self._call_llm(messages)
            
            # Check if we got a valid response from the LLM
            if not response1 or "Error:" in response1:
                logger.warning(f"Failed to get a valid translation from LLM: {response1}")
                logger.warning("Falling back to original query for semantic search")
                response1 = query
            
            # Step 2: Semantic search for CPT codes based on the LLM output from Step 1
            logger.info(f"Using enhanced query from LLM: {response1}")

            top_matches = self.semantic_search(response1, top_n=15)

            # Format DB results into prompt
            db_prompt = "\n".join(
                f"- Code: {code['code']}, Description: {code['description']}, "
                f"Category: {code['category']}, "
                f"Key Indicator: {'Yes' if code['key_indicator'] else 'No'}, "
                f"Standard Charge: ${code['standard_charge']:.2f}"
                for code in top_matches
            )
            
            # Enhanced system message with semantic search results (based on the translated query)
            system_message = (
                "You are the ENT CPT Code Agent, an AI specializing in ENT CPT coding. "
                "Using the following relevant CPT codes identified by semantic search, "
                "select and recommend MULTIPLE appropriate codes that could be applicable to the procedure:\n"
                f"{db_prompt}\n\n"
                "Always provide at least 2-3 possible CPT codes with explanations for each. "
                "Start with the most appropriate code, then provide alternatives that could also apply. "
                "Prioritize Key Indicator codes, but include other relevant options. "
                "Format your response with clear headings for each CPT code option (e.g., 'OPTION 1: CPT 42420', 'OPTION 2: CPT 42425'). "
                "Always include the CPT code numbers in your response, and explain when each would be appropriate."
            )

            # If we have a conversation with history, extract previous messages
            if conversation:
                # Try different approaches to get messages
                get_messages_method = self.get_method_for_attribute(conversation, "messages")
                
                conversation_messages = []
                if get_messages_method:
                    # Try to get messages using the method we found
                    try:
                        conversation_messages = get_messages_method()
                    except:
                        # If it fails as a method, try it as an attribute
                        if hasattr(conversation, 'messages'):
                            conversation_messages = conversation.messages
                elif hasattr(conversation, 'messages'):
                    conversation_messages = conversation.messages
                
                if conversation_messages:
                    # Check if we already have a system message
                    has_system = False
                    for msg in conversation_messages:
                        if isinstance(msg, dict) and msg.get('role') == 'system':
                            has_system = True
                            break
                    
                    # Add system message if not already present
                    if not has_system:
                        messages.append({"role": "system", "content": system_message})
                    
                    # Add all conversation messages
                    for msg in conversation_messages:
                        if isinstance(msg, dict):
                            role = msg.get('role')
                            content = msg.get('content')
                            
                            # Skip system messages as we've already handled them
                            if role == 'system':
                                continue
                                
                            # Only include user and assistant messages
                            if role in ['user', 'assistant'] and content:
                                messages.append({"role": role, "content": content})
                    
                    # Add the new user query if it's not the last user message
                    if not messages or messages[-1].get('role') != 'user':
                        messages.append({"role": "user", "content": query})
                else:
                    # No conversation messages found, create new
                    messages = [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query}
                    ]
            else:
                # No conversation object, create new messages
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query}
                ]
            
            # Make a simple LLM call without tools
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.model_temperature,
                max_tokens=self.model_max_tokens
            )
            
            final_response = response.choices[0].message.content
            
            # Extract CPT codes from the final response
            cpt_codes = self.extract_cpt_codes(final_response)
            
            # Log the identified codes for reference
            logger.info(f"Semantic search identified codes: {[c['code'] for c in top_matches]}")

            # Add to conversation history if provided
            if conversation and hasattr(conversation, 'add_message'):
                conversation.add_message("assistant", final_response, cpt_codes)
            
            return final_response

        except Exception as e:
            logger.error(f"Semantic search or processing error: {e}")
            error_response = f"I apologize, but I encountered an error while processing your query: {str(e)}"
            
            # Add to conversation history if provided
            if conversation and hasattr(conversation, 'add_message'):
                conversation.add_message("assistant", error_response)
            
            return error_response
    
    def extract_cpt_codes(self, text: str) -> List[str]:
        """Extract CPT codes from text."""
        if not isinstance(text, str):
            text = str(text)
            
        pattern = r'\b\d{5}(?:-\d{1,2})?\b'
        matches = re.findall(pattern, text)
        return matches
    
    def run_interactive_session(self):
        """Run an interactive session with the agent, highlighting key indicators and standard charges."""
        print("\nENT CPT Code Agent v2.1 Interactive Session")
        print("Enhanced with key indicator prioritization and standard charge information")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                query = input("Query > ")
                if query.lower() in ['exit', 'quit']:
                    break
                
                print("\nProcessing...")
                response = self.process_query(query)
                print(f"\n{response}\n")
                
                # Extract and display CPT codes with their key indicator and standard charge status
                cpt_codes = self.extract_cpt_codes(response)
                if cpt_codes:
                    print("CPT Codes Summary:")
                    for code in cpt_codes:
                        # Handle codes with modifiers
                        base_code = code.split('-')[0]
                        
                        # Get code details
                        details = self.cpt_db.get_code_details(base_code)
                        if "error" not in details:
                            description = details.get("description", "")
                            key_indicator = details.get("key_indicator", False)
                            standard_charge = details.get("standard_charge", 0.0)
                            
                            # Format the display
                            ki_status = "✓ KEY INDICATOR" if key_indicator else ""
                            charge_info = f"${standard_charge:.2f}" if standard_charge > 0 else "N/A"
                            
                            print(f"- {code}: {description}")
                            if ki_status:
                                print(f"  {ki_status}")
                            print(f"  Standard Charge: {charge_info}")
                            print()
                
            except KeyboardInterrupt:
                print("\nSession terminated by user")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue