"""
Main module for the ENT CPT Agent.
Contains the ENTCPTAgent class for processing ENT procedure queries.
"""

import os
import logging
import json
import re
import lmstudio as lms
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger("ent_cpt_agent")

# Import required components
from src.agent.cpt_database import CPTCodeDatabase
from src.agent.rules_engine import RulesEngine

class ENTCPTAgent:
    """
    Agent for processing ENT procedure queries and determining appropriate CPT codes.
    """
    def __init__(self, config, conversation_manager=None):
        """
        Initialize the ENT CPT Agent.
        
        Args:
            config: Configuration object or path to config file
            conversation_manager: Optional ConversationManager instance
        """
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
        self.model_temperature = self.config.get("model", "temperature")
        self.model_max_tokens = self.config.get("model", "max_tokens")
        self.cpt_db_path = self.config.get("cpt_database", "file_path")
        
        logger.info(f"Using CPT database path: {self.cpt_db_path}")
        logger.info(f"Using model: {self.model_name}")
        
        # Initialize components (order matters!)
        self.system_prompt = None  # Initialize first to avoid reference issues
        self.model = None
        
        # Import and initialize database and rules engine
        self.cpt_db = CPTCodeDatabase(self.cpt_db_path)
        self.rules_engine = RulesEngine()
        self.conversation_manager = conversation_manager
        
        # Set system prompt
        self.system_prompt = self._create_system_prompt()
        
        # Initialize LM Studio model
        self.initialize_model()
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt for the agent.
        
        Returns:
            System prompt string
        """
        return """
        You are an expert ENT (Ear, Nose, Throat) medical coding assistant specialized in CPT codes. 
        Your goal is to help medical professionals find the correct CPT codes for ENT procedures.
        
        You have access to the following tools:
        1. search_cpt_codes: Search for CPT codes based on a procedure description
        2. validate_cpt_code: Validate if a CPT code exists and is correct
        3. get_category_codes: Get all CPT codes for a specific ENT category
        4. explain_coding_rules: Explain the rules for using a specific CPT code
        5. analyze_procedure: Analyze a procedure description to determine appropriate CPT codes
        
        When recommending CPT codes:
        - Always verify that the procedure description matches the code exactly
        - Check for any modifiers that may be needed (e.g., bilateral procedures)
        - Explain why you're recommending specific codes
        - Consider bundling rules and related codes
        - Format CPT codes clearly using the format: XXXXX (description)
        
        Always provide educational explanations of your reasoning process so
        medical professionals can learn the correct coding principles.
        """
    
    def initialize_model(self) -> None:
        """Initialize the LM Studio model."""
        logger.info(f"Initializing LM Studio model: {self.model_name}")
        try:
            # Configure model with parameters from config
            self.model = lms.llm(self.model_name, config={
                "temperature": self.model_temperature,
                "maxTokens": self.model_max_tokens
            })
            logger.info("Model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            # Continue without raising - the agent will handle missing model gracefully
    
    def search_cpt_codes(self, query: str) -> str:
        """
        Tool function: Search for CPT codes based on a procedure description.
        
        Args:
            query: The procedure or keywords to search for
            
        Returns:
            Formatted search results as a string
        """
        results = self.cpt_db.search_codes(query)
        if not results:
            return f"No CPT codes found matching '{query}'"
        
        response = f"Found {len(results)} CPT codes matching '{query}':\n\n"
        for idx, result in enumerate(results, 1):
            response += f"{idx}. Code {result['code']}: {result['description']}\n"
            if result['related_codes']:
                response += f"   Related codes: {', '.join(result['related_codes'])}\n"
        
        return response
    
    def validate_cpt_code(self, code: str) -> str:
        """
        Tool function: Validate if a CPT code exists and is correct.
        
        Args:
            code: The CPT code to validate
            
        Returns:
            Validation result as a string
        """
        result = self.cpt_db.get_code_validation(code)
        if result["valid"]:
            return f"CPT code {code} is valid: {result['description']}"
        else:
            return result["error"]
    
    def get_category_codes(self, category: str) -> str:
        """
        Tool function: Get all CPT codes for a specific ENT category.
        
        Args:
            category: The ENT category to get codes for
            
        Returns:
            List of codes in the category as a formatted string
        """
        results = self.cpt_db.get_codes_by_category(category)
        if not results:
            return f"No CPT codes found for category '{category}'"
        
        response = f"CPT codes for category '{category}':\n\n"
        for idx, result in enumerate(results, 1):
            response += f"{idx}. Code {result['code']}: {result['description']}\n"
        
        return response
    
    def explain_coding_rules(self, code: str) -> str:
        """
        Tool function: Explain the rules for using a specific CPT code.
        
        Args:
            code: The CPT code to explain rules for
            
        Returns:
            Explanation of coding rules as a string
        """
        # First get the code details
        result = self.cpt_db.get_code_details(code)
        if "error" in result:
            return result["error"]
        
        # Basic code information
        response = f"Coding guidelines for CPT {code}:\n\n"
        response += f"Description: {result['description']}\n\n"
        
        # Get coding tips from rules engine
        tips = self.rules_engine.get_coding_tips(code, result['description'])
        
        response += "Coding guidelines:\n"
        for idx, tip in enumerate(tips, 1):
            response += f"{idx}. {tip}\n"
        
        # Add information about related codes
        if result['related_codes']:
            response += f"\nRelated codes to consider: {', '.join(result['related_codes'])}\n"
            response += "\nAlways check if one of these related codes may be more appropriate based on specific procedure details."
        
        return response
    
    def analyze_procedure(self, procedure_text: str) -> str:
        """
        Tool function: Analyze a procedure description to determine appropriate CPT codes.
        
        Args:
            procedure_text: Description of the ENT procedure
            
        Returns:
            Analysis results as a formatted string
        """
        # Search for potential codes
        search_results = self.cpt_db.search_codes(procedure_text)
        candidate_codes = [result["code"] for result in search_results]
        
        if not candidate_codes:
            return f"No potential CPT codes found for this procedure description. Please provide more details about the procedure."
        
        # Analyze with rules engine
        analysis = self.rules_engine.analyze_procedure(
            procedure_text, candidate_codes, self.cpt_db)
        
        if analysis["status"] != "success":
            return f"Error analyzing procedure: {analysis.get('message', 'Unknown error')}"
        
        # Format the response
        response = f"Analysis of procedure: {procedure_text}\n\n"
        
        # Add recommended codes
        response += "Recommended CPT codes:\n"
        for code in analysis["recommended_codes"]:
            # Get description for the code
            code_info = self.cpt_db.get_code_details(code.split('-')[0])  # Handle codes with modifiers
            description = code_info.get("description", "Unknown") if "error" not in code_info else "Unknown"
            response += f"- {code}: {description}\n"
        
        # Add explanations
        if analysis["explanations"]:
            response += "\nRecommendation details:\n"
            for explanation in analysis["explanations"]:
                if "message" in explanation:
                    response += f"- {explanation['message']}\n"
        
        # Add excluded codes if any
        if analysis["excluded_codes"]:
            response += "\nExcluded codes (may be bundled or inappropriate):\n"
            for code in analysis["excluded_codes"]:
                code_info = self.cpt_db.get_code_details(code)
                description = code_info.get("description", "Unknown") if "error" not in code_info else "Unknown"
                response += f"- {code}: {description}\n"
        
        return response
    
    def process_query(self, query: str, conversation=None) -> str:
        """
        Process a user query about ENT procedures and CPT codes.
        
        Args:
            query: The user's question or procedure description
            conversation: Optional Conversation object to use
            
        Returns:
            Agent's response with CPT code recommendations
        """
        logger.info(f"Processing query: {query}")
        
        # Check if model is initialized
        if self.model is None:
            return "Model not initialized. Please check the model configuration."
        
        # Use provided conversation or create a temporary one
        if conversation is None:
            chat = lms.Chat(self.system_prompt)
            chat.add_user_message(query)
        else:
            # Convert existing conversation to LM Studio chat
            chat = lms.Chat(self.system_prompt)
            
            # Add message history from conversation object if available
            if hasattr(conversation, 'messages'):
                for msg in conversation.messages:
                    if msg["role"] == "user":
                        chat.add_user_message(msg["content"])
                    elif msg["role"] == "assistant":
                        chat.add_assistant_message(msg["content"])
            
            # Add the current query
            chat.add_user_message(query)
        
        # Define the tool functions
        tools = [
            self.search_cpt_codes,
            self.validate_cpt_code,
            self.get_category_codes,
            self.explain_coding_rules,
            self.analyze_procedure
        ]
        
        try:
            # Basic message callback to add response to conversation
            def on_message(msg):
                content = str(msg)  # Convert message to string regardless of structure
                if conversation and hasattr(conversation, 'add_message'):
                    conversation.add_message("assistant", content)
                return content
            
            # Let the model use tools to process the query
            result = self.model.act(
                chat,
                tools,
                on_message=on_message
            )
            
            # Handle different result structures
            response = ""
            if hasattr(result, 'content'):
                response = result.content
            elif hasattr(result, 'response'):
                response = result.response
            elif hasattr(result, 'output'):
                response = result.output
            elif hasattr(result, 'result'):
                if isinstance(result.result, str):
                    response = result.result
                elif hasattr(result.result, 'content'):
                    response = result.result.content
                elif hasattr(result.result, 'message'):
                    response = result.result.message
            else:
                # As a fallback, convert the whole result to string
                response = str(result)
            
            return response
            
        except Exception as e:
            logger.error(f"Error during model.act(): {e}", exc_info=True)
            return f"I encountered an error while processing your query: {str(e)}"
    
    def extract_cpt_codes(self, text: str) -> List[str]:
        """
        Extract CPT codes from text.
        
        Args:
            text: Text to extract CPT codes from
            
        Returns:
            List of extracted CPT codes
        """
        # Pattern for CPT codes (5 digits, optionally followed by modifiers)
        pattern = r'\b\d{5}(?:-\d{1,2})?\b'
        matches = re.findall(pattern, text)
        return matches