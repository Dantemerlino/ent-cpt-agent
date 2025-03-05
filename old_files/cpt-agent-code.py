import os
import pandas as pd
import re
import lmstudio as lms
from typing import List, Dict, Any, Optional, Tuple
import argparse
import logging
import json
from pathlib import Path

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
    def __init__(self, cpt_db_path: str, model_name: str = "qwen2.5-7b-instruct"):
        """
        Initialize the ENT CPT Agent.
        
        Args:
            cpt_db_path: Path to the CPT code database Excel file
            model_name: Name of the LM Studio model to use
        """
        self.cpt_db = CPTCodeDatabase(cpt_db_path)
        self.model_name = model_name
        self.model = None
        self.chat = None
        self.initialize_model()
    
    def initialize_model(self) -> None:
        """Initialize the LM Studio model."""
        logger.info(f"Initializing LM Studio model: {self.model_name}")
        try:
            self.model = lms.llm(self.model_name)
            # Create a system prompt that explains the agent's purpose
            system_prompt = """
            You are an expert ENT (Ear, Nose, Throat) medical coding assistant. 
            Your goal is to help medical professionals find the correct CPT codes for ENT procedures.
            Use the available tools to search for codes, validate codes, and explain coding rules.
            Always provide explanations for your code recommendations based on official coding guidelines.
            """
            self.chat = lms.Chat(system_prompt)
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
        # Note: This is a placeholder. In a real implementation, this would
        # contain actual coding rules from a medical coding reference.
        result = self.cpt_db.get_code_details(code)
        if "error" in result:
            return result["error"]
        
        response = f"Coding guidelines for CPT {code}:\n\n"
        response += f"Description: {result['description']}\n\n"
        response += "General coding rules:\n"
        response += "1. Ensure the procedure documented matches the code description exactly\n"
        response += "2. Check for any required modifiers\n"
        response += "3. Verify medical necessity is documented\n"
        response += "4. Confirm the procedure is not bundled with another code\n"
        
        if result['related_codes']:
            response += f"\nCheck related codes that might be more appropriate: {', '.join(result['related_codes'])}"
        
        return response
    
    def process_query(self, query: str) -> str:
        """
        Process a user query about ENT procedures and CPT codes.
        
        Args:
            query: The user's question or procedure description
            
        Returns:
            Agent's response with CPT code recommendations
        """
        logger.info(f"Processing query: {query}")
        
        # Add the user message to the chat
        self.chat.add_user_message(query)
        
        # Define the tool functions
        tools = [
            self.search_cpt_codes,
            self.validate_cpt_code,
            self.get_category_codes,
            self.explain_coding_rules
        ]
        
        # Let the model use tools to process the query
        result = self.model.act(
            self.chat,
            tools,
            on_message=self.chat.append
        )
        
        return result.content
    
    def run_interactive_session(self) -> None:
        """Run an interactive session where the user can ask questions about CPT codes."""
        print("\nENT CPT Code Assistant")
        print("=" * 30)
        print("Ask questions about ENT procedures and CPT codes.")
        print("Type 'quit' or 'exit' to end the session.\n")
        
        while True:
            query = input("\nQuestion: ")
            if query.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            response = self.process_query(query)
            print("\nResponse:")
            print(response)
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
