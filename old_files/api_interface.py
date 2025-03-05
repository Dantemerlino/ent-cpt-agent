from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
import logging
import os
from pydantic import BaseModel, Field
import json

# Import our agent components
# Note: These would be actual imports in a real implementation
# from agent_config import AgentConfig
# from cpt_database import CPTCodeDatabase
# from rules_engine import RulesEngine
# from conversation_manager import ConversationManager, Conversation
# from ent_cpt_agent import ENTCPTAgent

logger = logging.getLogger("ent_cpt_agent.api")

# ========== API DATA MODELS ==========
# These Pydantic models define the request/response schema for the API endpoints

class QueryRequest(BaseModel):
    """Request model for querying the agent."""
    query: str = Field(..., description="The query about ENT procedures or CPT codes")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

class CodeSearchRequest(BaseModel):
    """Request model for searching CPT codes."""
    search_term: str = Field(..., description="Term to search for in CPT code descriptions")

class CodeValidationRequest(BaseModel):
    """Request model for validating CPT codes."""
    code: str = Field(..., description="CPT code to validate")

class ProcedureAnalysisRequest(BaseModel):
    """Request model for analyzing a procedure description."""
    procedure_text: str = Field(..., description="Description of the ENT procedure")
    candidate_codes: Optional[List[str]] = Field(None, description="Optional list of candidate CPT codes")

class AgentResponse(BaseModel):
    """Generic response model for agent API."""
    status: str = Field(..., description="Status of the request (success/error)")
    message: Optional[str] = Field(None, description="Response message or error details")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

class APIInterface:
    """
    API interface for the ENT CPT Code Agent.
    
    This class provides a REST API for interacting with the ENT CPT Code Agent,
    including endpoints for querying the agent, searching for codes, validating codes,
    analyzing procedures, and managing conversations.
    """
    
    def __init__(self, agent, config, host="localhost", port=8000):
        """
        Initialize the API interface.
        
        Args:
            agent: Instance of ENTCPTAgent
            config: Instance of AgentConfig
            host: Host to run the API server on
            port: Port to run the API server on
        """
        self.agent = agent
        self.config = config
        self.host = host
        self.port = port
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="ENT CPT Code Agent API",
            description="API for querying ENT CPT codes and analyzing medical procedures",
            version="1.0.0"
        )
        
        # Add CORS middleware to allow cross-origin requests
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this to specific origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register API routes
        self.register_routes()
    
    def register_routes(self):
        """
        Register API routes.
        
        This method sets up all the API endpoints and their handlers.
        """
        
        # ========== GENERAL ROUTES ==========
        
        @self.app.get("/", tags=["General"])
        async def root():
            """Root endpoint providing API information."""
            return {
                "name": "ENT CPT Code Agent API",
                "version": "1.0.0",
                "status": "running"
            }
        
        # ========== AGENT ROUTES ==========
        
        @self.app.post("/api/query", response_model=AgentResponse, tags=["Agent"])
        async def query_agent(request: QueryRequest):
            """
            Submit a query to the ENT CPT Code Agent.
            
            This endpoint processes natural language queries about ENT procedures
            and CPT codes, using the agent to determine the most appropriate response.
            """
            try:
                # Get or create session
                session_id = request.session_id
                conversation_manager = self.agent.conversation_manager
                
                if session_id and conversation_manager.get_conversation(session_id):
                    conversation = conversation_manager.get_conversation(session_id)
                else:
                    conversation = conversation_manager.create_conversation()
                    session_id = conversation.session_id
                
                # Add user message to conversation
                conversation.add_message("user", request.query)
                
                # Process the query
                response = self.agent.process_query(request.query, conversation)
                
                # Extract CPT codes from response
                codes = conversation_manager.extract_cpt_codes(response)
                
                # Add assistant message to conversation
                conversation.add_message("assistant", response, codes)
                
                # Save conversation
                conversation_manager.save_conversation(conversation)
                
                return {
                    "status": "success",
                    "message": response,
                    "data": {
                        "codes": codes
                    },
                    "session_id": session_id
                }
            
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ========== CPT CODE ROUTES ==========
        
        @self.app.post("/api/search", response_model=AgentResponse, tags=["CPT Codes"])
        async def search_codes(request: CodeSearchRequest):
            """
            Search for CPT codes by description or keywords.
            
            This endpoint searches the CPT code database for codes matching
            the provided search term in their description.
            """
            try:
                results = self.agent.cpt_db.search_codes(request.search_term)
                
                return {
                    "status": "success",
                    "data": {
                        "codes": results,
                        "count": len(results)
                    }
                }
            
            except Exception as e:
                logger.error(f"Error searching codes: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/validate", response_model=AgentResponse, tags=["CPT Codes"])
        async def validate_code(request: CodeValidationRequest):
            """
            Validate a CPT code.
            
            This endpoint checks if a CPT code exists and is valid according
            to the CPT code database.
            """
            try:
                result = self.agent.cpt_db.get_code_validation(request.code)
                
                return {
                    "status": "success" if result.get("valid", False) else "error",
                    "message": result.get("description") if result.get("valid", False) else result.get("error"),
                    "data": result
                }
            
            except Exception as e:
                logger.error(f"Error validating code: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/analyze", response_model=AgentResponse, tags=["Analysis"])
        async def analyze_procedure(request: ProcedureAnalysisRequest):
            """
            Analyze an ENT procedure description to determine appropriate CPT codes.
            
            This endpoint uses the rules engine to analyze a procedure description
            and suggest appropriate CPT codes based on coding guidelines.
            """
            try:
                # If candidate codes weren't provided, search for them
                candidate_codes = request.candidate_codes
                if not candidate_codes:
                    search_results = self.agent.cpt_db.search_codes(request.procedure_text)
                    candidate_codes = [result["code"] for result in search_results]
                
                # Analyze the procedure using the rules engine
                analysis = self.agent.rules_engine.analyze_procedure(
                    request.procedure_text, candidate_codes, self.agent.cpt_db)
                
                return {
                    "status": "success",
                    "data": analysis
                }
            
            except Exception as e:
                logger.error(f"Error analyzing procedure: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ========== CONVERSATION ROUTES ==========
        
        @self.app.get("/api/conversations", response_model=AgentResponse, tags=["Conversations"])
        async def list_conversations():
            """
            List all saved conversations.
            
            This endpoint returns a list of all saved conversations with their metadata.
            """
            try:
                conversations = self.agent.conversation_manager.list_conversations()
                
                return {
                    "status": "success",
                    "data": {
                        "conversations": conversations,
                        "count": len(conversations)
                    }
                }
            
            except Exception as e:
                logger.error(f"Error listing conversations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/conversations/{session_id}", response_model=AgentResponse, tags=["Conversations"])
        async def get_conversation(session_id: str):
            """
            Get a specific conversation by session ID.
            
            This endpoint returns the details of a specific conversation.
            """
            try:
                conversation = self.agent.conversation_manager.get_conversation(session_id)
                
                if not conversation:
                    raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
                
                return {
                    "status": "success",
                    "data": conversation.to_dict(),
                    "session_id": session_id
                }
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting conversation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/conversations/{session_id}", response_model=AgentResponse, tags=["Conversations"])
        async def delete_conversation(session_id: str):
            """
            Delete a specific conversation by session ID.
            
            This endpoint deletes a specific conversation and its associated data.
            """
            try:
                result = self.agent.conversation_manager.delete_conversation(session_id)
                
                if not result:
                    raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
                
                return {
                    "status": "success",
                    "message": f"Conversation {session_id} deleted successfully"
                }
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting conversation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def start(self):
        """
        Start the API server.
        
        This method starts the FastAPI application using uvicorn.
        """
        logger.info(f"Starting API server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)
    
    def get_app(self):
        """
        Get the FastAPI application instance.
        
        Returns:
            FastAPI application instance
        """
        return self.appBaseModel):
    """Generic response model for agent API."""
    status: str = Field(..., description="Status of the request (success/error)")
    message: Optional[str] = Field(None, description="Response message or error details")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

class APIInterface:
    """API interface for the ENT CPT Code Agent."""
    
    def __init__(self, agent, config, host="localhost", port=8000):
        """
        Initialize the API interface.
        
        Args:
            agent: Instance of ENTCPTAgent
            config: Instance of AgentConfig
            host: Host to run the API server on
            port: Port to run the API server on
        """
        self.agent = agent
        self.config = config
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="ENT CPT Code Agent API",
            description="API for querying ENT CPT codes and analyzing medical procedures",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this to specific origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self.register_routes()
    
    def register_routes(self):
        """Register API routes."""
        
        @self.app.get("/", tags=["General"])
        async def root():
            """Root endpoint providing API information."""
            return {
                "name": "ENT CPT Code Agent API",
                "version": "1.0.0",
                "status": "running"
            }
        
        @self.app.post("/api/query", response_model=AgentResponse, tags=["Agent"])
        async def query_agent(request: QueryRequest):
            """
            Submit a query to the ENT CPT Code Agent.
            
            This endpoint processes natural language queries about ENT procedures
            and CPT codes, using the agent to determine the most appropriate response.
            """
            try:
                # Get or create session
                session_id = request.session_id
                conversation_manager = self.agent.conversation_manager
                
                if session_id and conversation_manager.get_conversation(session_id):
                    conversation = conversation_manager.get_conversation(session_id)
                else:
                    conversation = conversation_manager.create_conversation()
                    session_id = conversation.session_id
                
                # Add user message to conversation
                conversation.add_message("user", request.query)
                
                # Process the query
                response = self.agent.process_query(request.query, conversation)
                
                # Extract CPT codes from response
                codes = conversation_manager.extract_cpt_codes(response)
                
                # Add assistant message to conversation
                conversation.add_message("assistant", response, codes)
                
                # Save conversation
                conversation_manager.save_conversation(conversation)
                
                return {
                    "status": "success",
                    "message": response,
                    "data": {
                        "codes": codes
                    },
                    "session_id": session_id
                }
            
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/search", response_model=AgentResponse, tags=["CPT Codes"])
        async def search_codes(request: CodeSearchRequest):
            """
            Search for CPT codes by description or keywords.
            
            This endpoint searches the CPT code database for codes matching
            the provided search term in their description.
            """
            try:
                results = self.agent.cpt_db.search_codes(request.search_term)
                
                return {
                    "status": "success",
                    "data": {
                        "codes": results,
                        "count": len(results)
                    }
                }
            
            except Exception as e:
                logger.error(f"Error searching codes: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/validate", response_model=AgentResponse, tags=["CPT Codes"])
        async def validate_code(request: CodeValidationRequest):
            """
            Validate a CPT code.
            
            This endpoint checks if a CPT code exists and is valid according
            to the CPT code database.
            """
            try:
                result = self.agent.cpt_db.get_code_validation(request.code)
                
                return {
                    "status": "success" if result.get("valid", False) else "error",
                    "message": result.get("description") if result.get("valid", False) else result.get("error"),
                    "data": result
                }
            
            except Exception as e:
                logger.error(f"Error validating code: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/analyze", response_model=AgentResponse, tags=["Analysis"])
        async def analyze_procedure(request: ProcedureAnalysisRequest):
            """
            Analyze an ENT procedure description to determine appropriate CPT codes.
            
            This endpoint uses the rules engine to analyze a procedure description
            and suggest appropriate CPT codes based on coding guidelines.
            """
            try:
                # If candidate codes weren't provided, search for them
                candidate_codes = request.candidate_codes
                if not candidate_codes:
                    search_results = self.agent.cpt_db.search_codes(request.procedure_text)
                    candidate_codes = [result["code"] for result in search_results]
                
                # Analyze the procedure using the rules engine
                analysis = self.agent.rules_engine.analyze_procedure(
                    request.procedure_text, candidate_codes, self.agent.cpt_db)
                
                return {
                    "status": "success",
                    "data": analysis
                }
            
            except Exception as e:
                logger.error(f"Error analyzing procedure: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/conversations", response_model=AgentResponse, tags=["Conversations"])
        async def list_conversations():
            """
            List all saved conversations.
            
            This endpoint returns a list of all saved conversations with their metadata.
            """
            try:
                conversations = self.agent.conversation_manager.list_conversations()
                
                return {
                    "status": "success",
                    "data": {
                        "conversations": conversations,
                        "count": len(conversations)
                    }
                }
            
            except Exception as e:
                logger.error(f"Error listing conversations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/conversations/{session_id}", response_model=AgentResponse, tags=["Conversations"])
        async def get_conversation(session_id: str):
            """
            Get a specific conversation by session ID.
            
            This endpoint returns the details of a specific conversation.
            """
            try:
                conversation = self.agent.conversation_manager.get_conversation(session_id)
                
                if not conversation:
                    raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
                
                return {
                    "status": "success",
                    "data": conversation.to_dict(),
                    "session_id": session_id
                }
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting conversation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/conversations/{session_id}", response_model=AgentResponse, tags=["Conversations"])
        async def delete_conversation(session_id: str):
            """
            Delete a specific conversation by session ID.
            
            This endpoint deletes a specific conversation and its associated data.
            """
            try:
                result = self.agent.conversation_manager.delete_conversation(session_id)
                
                if not result:
                    raise HTTPException(status_code=404, detail=f"Conversation {session_id} not found")
                
                return {
                    "status": "success",
                    "message": f"Conversation {session_id} deleted successfully"
                }
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting conversation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def start(self):
        """Start the API server."""
        logger.info(f"Starting API server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)
    
    def get_app(self):
        """Get the FastAPI application instance."""
        return self.app