import os
import pandas as pd
import re
import lmstudio as lms
from typing import List, Dict, Any, Optional, Tuple
import argparse
import logging
import json
from pathlib import Path

# Import needed components
from .cpt_database import CPTCodeDatabase
from .rules_engine import RulesEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ent_cpt_agent")

class CPTCodeDatabase:
    """
    Handles loading, processing, and querying of CPT codes for ENT procedures.
    """
    def __init__(self, file_path: str):
        """
        Initialize the CPT code database from the provided Excel file.
        
        Args:
            file_path: Path to the Excel file containing CPT codes
        """
        self.file_path = file_path
        self.df = None
        self.code_descriptions = {}
        self.code_categories = {}
        self.related_codes = {}
        self.load_data()
    
    def load_data(self) -> None:
        """Load CPT code data from Excel file and process it."""
        logger.info(f"Loading CPT codes from {self.file_path}")
        try:
            self.df = pd.read_excel(self.file_path)
            
            # Process the dataframe to create lookup dictionaries
            for _, row in self.df.iterrows():
                code = str(row.get('CPT Code', '')).strip()
                if code and not pd.isna(code):
                    # Store description
                    self.code_descriptions[code] = row.get('Description', '')
                    
                    # Store category
                    category = row.get('Category', '')
                    if category and not pd.isna(category):
                        if category not in self.code_categories:
                            self.code_categories[category] = []
                        self.code_categories[category].append(code)
                    
                    # Store related codes
                    related = row.get('Related Codes', '')
                    if related and not pd.isna(related):
                        related_codes = [r.strip() for r in str(related).split(',')]
                        self.related_codes[code] = related_codes
            
            logger.info(f"Loaded {len(self.code_descriptions)} CPT codes")
        except Exception as e:
            logger.error(f"Error loading CPT codes: {e}")
            raise
    
    def search_codes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for CPT codes based on a text query.
        
        Args:
            query: Search terms for finding relevant CPT codes
            
        Returns:
            List of matching CPT codes with descriptions
        """
        query = query.lower()
        results = []
        
        for code, description in self.code_descriptions.items():
            if query in description.lower() or query in code:
                results.append({
                    "code": code,
                    "description": description,
                    "related_codes": self.related_codes.get(code, [])
                })
        
        return results
    
    def get_code_details(self, code: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific CPT code.
        
        Args:
            code: The CPT code to look up
            
        Returns:
            Dictionary containing detailed information about the code
        """
        if code not in self.code_descriptions:
            return {"error": f"CPT code {code} not found"}
        
        return {
            "code": code,
            "description": self.code_descriptions.get(code, ""),
            "related_codes": self.related_codes.get(code, [])
        }
    
    def get_codes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all CPT codes belonging to a specific category.
        
        Args:
            category: The category to look up codes for
            
        Returns:
            List of CPT codes in the specified category
        """
        if category not in self.code_categories:
            return []
        
        results = []
        for code in self.code_categories[category]:
            results.append({
                "code": code,
                "description": self.code_descriptions.get(code, ""),
                "related_codes": self.related_codes.get(code, [])
            })
        
        return results
    
    def get_code_validation(self, code: str) -> Dict[str, Any]:
        """
        Validate if a CPT code exists and is valid.
        
        Args:
            code: The CPT code to validate
            
        Returns:
            Dictionary with validation results
        """
        if code in self.code_descriptions:
            return {"valid": True, "description": self.code_descriptions[code]}
        else:
            return {"valid": False, "error": f"Invalid CPT code: {code}"}


class ENTCPTAgent:
    """
    Agent for processing ENT procedure queries and determining appropriate CPT codes.
    """
    def __init__(self, config, conversation_manager=None):
        """
        Initialize the ENT CPT Agent.
        
        Args:
            config: AgentConfig object with configuration settings
            conversation_manager: Optional ConversationManager instance
        """
        self.config = config
        
        # Get configuration values
        self.model_name = config.get("model", "name")
        self.model_temperature = config.get("model", "temperature")
        self.model_max_tokens = config.get("model", "max_tokens")
        self.cpt_db_path = config.get("cpt_database", "file_path")
        
        # Initialize components
        self.cpt_db = CPTCodeDatabase(self.cpt_db_path)
        self.rules_engine = RulesEngine()
        self.conversation_manager = conversation_manager or ConversationManager(
            config.get("agent", "conversation_dir")
        )
        
        # Initialize LM Studio model
        self.model = None
        self.system_prompt = self._create_system_prompt()
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
            raise
    
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
        
        # Use provided conversation or create a temporary one
        if conversation is None:
            chat = lms.Chat(self.system_prompt)
            chat.add_user_message(query)
        else:
            # Convert existing conversation to LM Studio chat
            chat = conversation.to_lmstudio_chat(self.system_prompt)
        
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
        
        return result.content
    
    def run_interactive_session(self) -> None:
        """Run an interactive session where the user can ask questions about CPT codes."""
        print("\nENT CPT Code Assistant")
        print("=" * 50)
        print("Ask questions about ENT procedures and CPT codes.")
        print("Type 'quit' or 'exit' to end the session.")
        print("Type 'new' to start a new conversation.")
        print("=" * 50)
        
        # Create initial conversation
        conversation = self.conversation_manager.create_conversation()
        print(f"\nSession ID: {conversation.session_id}\n")
        
        while True:
            query = input("\nQuestion: ")
            
            # Handle special commands
            if query.lower() in ['quit', 'exit']:
                # Save conversation before exiting
                self.conversation_manager.save_conversation(conversation)
                print("Conversation saved. Goodbye!")
                break
            
            elif query.lower() == 'new':
                # Save current conversation and create a new one
                self.conversation_manager.save_conversation(conversation)
                conversation = self.conversation_manager.create_conversation()
                print(f"\nStarted new conversation. Session ID: {conversation.session_id}\n")
                continue
            
            # Add user message to conversation
            conversation.add_message("user", query)
            
            # Process query
            response = self.process_query(query, conversation)
            
            # Extract CPT codes from response
            codes = self.conversation_manager.extract_cpt_codes(response)
            if codes:
                # Update the last assistant message with found codes
                if conversation.messages and conversation.messages[-1]["role"] == "assistant":
                    conversation.messages[-1]["codes"] = codes
            
            # Save conversation after each interaction
            self.conversation_manager.save_conversation(conversation)
            
            # Display response
            print("\nResponse:")
            print(response)
            
            # Display found CPT codes separately
            if codes:
                print("\nCPT Codes found:")
                for code in codes:
                    description = ""
                    code_info = self.cpt_db.get_code_details(code)
                    if "error" not in code_info:
                        description = code_info.get("description", "")
                    print(f"- {code}: {description}")
            
            print("-" * 50)


def main():
    """Main entry point for the ENT CPT Code Agent."""
    parser = argparse.ArgumentParser(description="ENT CPT Code Agent")
    parser.add_argument(
        "--cpt_db", 
        type=str, 
        default="CPT codes for ENT.xlsx",
        help="Path to the CPT code database Excel file"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="qwen2.5-7b-instruct",
        help="Name of the LM Studio model to use"
    )
    args = parser.parse_args()
    
    try:
        agent = ENTCPTAgent(args.cpt_db, args.model)
        agent.run_interactive_session()
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
    except Exception as e:
        logger.error(f"Error running ENT CPT Agent: {e}")


if __name__ == "__main__":
    main()
