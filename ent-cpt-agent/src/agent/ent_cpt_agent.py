"""
Main module for the ENT CPT Agent.
Contains the ENTCPTAgent class for processing ENT procedure queries.
"""

import os
import logging
import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI

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
        self.model_temperature = float(self.config.get("model", "temperature"))
        self.model_max_tokens = int(self.config.get("model", "max_tokens"))
        self.cpt_db_path = self.config.get("cpt_database", "file_path")
        
        # Initialize components
        self.cpt_db = CPTCodeDatabase(self.cpt_db_path)
        self.rules_engine = RulesEngine()
        self.conversation_manager = conversation_manager
        
        # Create system prompt
        self.system_prompt = self._create_system_prompt()
        
        # Define tools for OpenAI API
        self.tools = self._define_tools()
        
        # Initialize model-related objects
        self.model = None  # Will be set by initialize_model
        
        # Initialize OpenAI client for LM Studio
        server_config = self.config.get("server")
        base_url = server_config.get("lm_studio_base_url", "http://localhost:1234/v1")
        api_key = server_config.get("lm_studio_api_key", "lm-studio")
        
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        logger.info(f"Connected to LM Studio at {base_url}")
        
        # Initialize model (compatibility)
        self.initialize_model()
        
        logger.info("ENTCPTAgent initialized successfully")
    def initialize_model(self) -> None:
        """
        Compatibility method for model initialization.
        We're using the OpenAI API now, so this just sets a dummy model.
        """
        logger.info(f"Using OpenAI API for {self.model_name}")
        # Set a dummy model object to indicate initialization
        self.model = True
        logger.info("OpenAI API connection established")

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent."""
        return """
        You are an expert ENT (Ear, Nose, Throat) medical coding assistant specialized in CPT codes. 
        Your goal is to help medical professionals find the correct CPT codes for ENT procedures.
        
        You have access to tools that can search for CPT codes, validate codes, and analyze procedures.
        Use these tools to provide accurate coding assistance.
        
        When recommending CPT codes:
        - Always verify that the procedure description matches the code exactly
        - Check for any modifiers that may be needed (e.g., bilateral procedures)
        - Explain why you're recommending specific codes
        - Consider bundling rules and related codes
        - Format CPT codes clearly using the format: XXXXX (description)
        
        Always provide educational explanations of your reasoning process so
        medical professionals can learn the correct coding principles.
        """
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define the tools that the model can use."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_cpt_codes",
                    "description": "Search for CPT codes based on a procedure description or keywords",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The procedure description or keywords to search for"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_cpt_code",
                    "description": "Validate if a CPT code exists and is correct",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The CPT code to validate"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_category_codes",
                    "description": "Get all CPT codes for a specific ENT category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "The ENT category to get codes for"
                            }
                        },
                        "required": ["category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "explain_coding_rules",
                    "description": "Explain the rules for using a specific CPT code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The CPT code to explain rules for"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_procedure",
                    "description": "Analyze a procedure description to determine appropriate CPT codes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "procedure_text": {
                                "type": "string",
                                "description": "Description of the ENT procedure"
                            }
                        },
                        "required": ["procedure_text"]
                    }
                }
            }
        ]
    
    def search_cpt_codes(self, query: str) -> str:
        """Search for CPT codes based on a procedure description."""
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
        """Validate if a CPT code exists and is correct."""
        result = self.cpt_db.get_code_validation(code)
        if result["valid"]:
            return f"CPT code {code} is valid: {result['description']}"
        else:
            return result["error"]
    
    def get_category_codes(self, category: str) -> str:
        """Get all CPT codes for a specific ENT category."""
        results = self.cpt_db.get_codes_by_category(category)
        if not results:
            return f"No CPT codes found for category '{category}'"
        
        response = f"CPT codes for category '{category}':\n\n"
        for idx, result in enumerate(results, 1):
            response += f"{idx}. Code {result['code']}: {result['description']}\n"
        
        return response
    
    def explain_coding_rules(self, code: str) -> str:
        """Explain the rules for using a specific CPT code."""
        result = self.cpt_db.get_code_details(code)
        if "error" in result:
            return result["error"]
        
        response = f"Coding guidelines for CPT {code}:\n\n"
        response += f"Description: {result['description']}\n\n"
        
        tips = self.rules_engine.get_coding_tips(code, result['description'])
        
        response += "Coding guidelines:\n"
        for idx, tip in enumerate(tips, 1):
            response += f"{idx}. {tip}\n"
        
        if result['related_codes']:
            response += f"\nRelated codes to consider: {', '.join(result['related_codes'])}\n"
            response += "\nAlways check if one of these related codes may be more appropriate based on specific procedure details."
        
        return response
    
    def analyze_procedure(self, procedure_text: str) -> str:
        """Analyze a procedure description to determine appropriate CPT codes."""
        search_results = self.cpt_db.search_codes(procedure_text)
        candidate_codes = [result["code"] for result in search_results]
        
        if not candidate_codes:
            return f"No potential CPT codes found for this procedure description. Please provide more details about the procedure."
        
        analysis = self.rules_engine.analyze_procedure(
            procedure_text, candidate_codes, self.cpt_db)
        
        if analysis["status"] != "success":
            return f"Error analyzing procedure: {analysis.get('message', 'Unknown error')}"
        
        response = f"Analysis of procedure: {procedure_text}\n\n"
        
        response += "Recommended CPT codes:\n"
        for code in analysis["recommended_codes"]:
            code_info = self.cpt_db.get_code_details(code.split('-')[0])
            description = code_info.get("description", "Unknown") if "error" not in code_info else "Unknown"
            response += f"- {code}: {description}\n"
        
        if analysis["explanations"]:
            response += "\nRecommendation details:\n"
            for explanation in analysis["explanations"]:
                if "message" in explanation:
                    response += f"- {explanation['message']}\n"
        
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
        
        # Prepare messages for the OpenAI API
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history if available
        if conversation and hasattr(conversation, 'messages'):
            for msg in conversation.messages:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        try:
            # Make the initial API call
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.tools,
                temperature=self.model_temperature,
                max_tokens=self.model_max_tokens
            )
            
            # Check if the model wants to use tools
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                # Process all tool calls
                tool_calls = response.choices[0].message.tool_calls
                
                # Add assistant message with tool calls to conversation
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in tool_calls
                    ]
                })
                
                # Process each tool call
                for tool_call in tool_calls:
                    # Parse arguments
                    args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    tool_result = ""
                    if tool_call.function.name == "search_cpt_codes":
                        tool_result = self.search_cpt_codes(args["query"])
                    elif tool_call.function.name == "validate_cpt_code":
                        tool_result = self.validate_cpt_code(args["code"])
                    elif tool_call.function.name == "get_category_codes":
                        tool_result = self.get_category_codes(args["category"])
                    elif tool_call.function.name == "explain_coding_rules":
                        tool_result = self.explain_coding_rules(args["code"])
                    elif tool_call.function.name == "analyze_procedure":
                        tool_result = self.analyze_procedure(args["procedure_text"])
                    else:
                        tool_result = f"Unknown tool: {tool_call.function.name}"
                    
                    # Add tool response to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Generate final response after tool calls
                final_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.model_temperature,
                    max_tokens=self.model_max_tokens
                )
                
                # Get the final text response
                final_content = final_response.choices[0].message.content
                
                # Add to conversation history if provided
                if conversation and hasattr(conversation, 'add_message'):
                    conversation.add_message("assistant", final_content)
                
                return final_content
            else:
                # No tool calls, just return the direct response
                content = response.choices[0].message.content
                
                # Add to conversation history if provided
                if conversation and hasattr(conversation, 'add_message'):
                    conversation.add_message("assistant", content)
                
                return content
        
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return f"I encountered an error while processing your query: {str(e)}"
    
    def extract_cpt_codes(self, text: str) -> List[str]:
        """Extract CPT codes from text."""
        if not isinstance(text, str):
            text = str(text)
            
        pattern = r'\b\d{5}(?:-\d{1,2})?\b'
        matches = re.findall(pattern, text)
        return matches