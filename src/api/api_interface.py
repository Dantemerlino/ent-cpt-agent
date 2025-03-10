"""
Enhanced API interface for the ENT CPT Code Agent.

This module implements a FastAPI interface for the agent with improved:
- OpenAI API compatibility
- Streaming support 
- LM Studio-specific endpoints
- Structured response formats
- Enhanced error handling
"""

import logging
import os
import sys
import json
import time
from typing import List, Dict, Any, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Query, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our agent components
from src.config.agent_config import AgentConfig
from src.conversation.conversation_manager import ConversationManager
from src.agent.ent_cpt_agent import ENTCPTAgent

# Configure logging
logger = logging.getLogger("ent_cpt_agent.api")

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    """Request model for querying the agent."""
    query: str = Field(..., description="The query about ENT procedures or CPT codes")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    stream: bool = Field(False, description="Whether to stream the response")

class CodeSearchRequest(BaseModel):
    """Request model for searching CPT codes."""
    search_term: str = Field(..., description="Term to search for in CPT code descriptions")
    limit: int = Field(10, description="Maximum number of results to return")

class CodeValidationRequest(BaseModel):
    """Request model for validating CPT codes."""
    code: str = Field(..., description="CPT code to validate")

class ProcedureAnalysisRequest(BaseModel):
    """Request model for analyzing a procedure description."""
    procedure_text: str = Field(..., description="Description of the ENT procedure")
    candidate_codes: Optional[List[str]] = Field(None, description="Optional list of candidate CPT codes")

class CodeComparisonRequest(BaseModel):
    """Request model for comparing CPT codes."""
    code1: str = Field(..., description="First CPT code to compare")
    code2: str = Field(..., description="Second CPT code to compare")

class ExplanationRequest(BaseModel):
    """Request model for getting a code explanation."""
    code: str = Field(..., description="CPT code to explain")

class AgentResponse(BaseModel):
    """Generic response model for agent API."""
    status: str = Field(..., description="Status of the request (success/error)")
    message: Optional[str] = Field(None, description="Response message or error details")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

# OpenAI API compatibility models
class ChatMessage(BaseModel):
    """Chat message for OpenAI compatibility."""
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    """OpenAI compatible chat completion request."""
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None

class EmbeddingRequest(BaseModel):
    """OpenAI compatible embedding request."""
    model: str
    input: Union[str, List[str]]

class CompletionRequest(BaseModel):
    """OpenAI compatible completion request."""
    model: str
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None

class APIInterface:
    """Enhanced API interface for the ENT CPT Code Agent."""
    
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
            version="2.0.0"
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
        """Register API routes for both standard API and OpenAI compatibility."""
        
        # ----------------- Standard API Routes -----------------
        @self.app.get("/", tags=["General"])
        async def root():
            """Root endpoint providing API information."""
            return {
                "name": "ENT CPT Code Agent API",
                "version": "2.0.0",
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
                
                # Handle streaming if requested
                if request.stream:
                    return StreamingResponse(
                        self._stream_response(request.query, conversation),
                        media_type="text/event-stream"
                    )
                
                # Process the query
                response = self.agent.process_query(request.query, conversation)
                
                # Extract CPT codes from response
                codes = conversation_manager.extract_cpt_codes(response)
                
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
                result = self.agent.search_cpt_codes(request.search_term, request.limit)
                
                return {
                    "status": "success",
                    "data": result.get("data", {"codes": [], "total_results": 0})
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
                result = self.agent.validate_cpt_code(request.code)
                
                return {
                    "status": result.get("status", "error"),
                    "message": result.get("description", result.get("message", "")),
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
                result = self.agent.analyze_procedure(
                    request.procedure_text, 
                    request.candidate_codes
                )
                
                return {
                    "status": result.get("status", "error"),
                    "data": result.get("data", {})
                }
            
            except Exception as e:
                logger.error(f"Error analyzing procedure: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/explain", response_model=AgentResponse, tags=["CPT Codes"])
        async def explain_code(request: ExplanationRequest):
            """
            Get a detailed explanation of a CPT code.
            
            This endpoint provides detailed information about a specific CPT code,
            including its description, usage guidelines, and related codes.
            """
            try:
                result = self.agent.get_explanation(request.code)
                
                return {
                    "status": result.get("status", "error"),
                    "message": result.get("explanation", result.get("message", "")),
                    "data": result
                }
            
            except Exception as e:
                logger.error(f"Error explaining code: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/compare", response_model=AgentResponse, tags=["CPT Codes"])
        async def compare_codes(request: CodeComparisonRequest):
            """
            Compare two CPT codes and explain their differences.
            
            This endpoint analyzes two CPT codes and explains the key differences
            between them, including when each should be used.
            """
            try:
                result = self.agent.compare_codes(request.code1, request.code2)
                
                return {
                    "status": result.get("status", "error"),
                    "message": result.get("comparison", result.get("message", "")),
                    "data": result
                }
            
            except Exception as e:
                logger.error(f"Error comparing codes: {e}")
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
        
        @self.app.get("/api/health", response_model=AgentResponse, tags=["System"])
        async def health_check():
            """
            Health check endpoint to verify the API is working.
            
            This endpoint provides system status information including agent
            initialization status, database connectivity, and loaded models.
            """
            try:
                health_data = self.agent.health_check()
                
                return {
                    "status": "success",
                    "message": f"Service is {health_data.get('status', 'unknown')}",
                    "data": health_data
                }
            
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                return {
                    "status": "error",
                    "message": f"Service health check failed: {str(e)}",
                    "data": {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                }
        
        @self.app.get("/api/rules", response_model=AgentResponse, tags=["System"])
        async def list_rules():
            """
            List all rules used by the rules engine.
            
            This endpoint provides information about the coding rules used by the system.
            """
            try:
                return {
                    "status": "success",
                    "data": {
                        "rules": self.agent.rules_engine.rules,
                        "count": len(self.agent.rules_engine.rules)
                    }
                }
            
            except Exception as e:
                logger.error(f"Error listing rules: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ----------------- OpenAI API Compatibility Routes -----------------
        
        @self.app.get("/v1/models", tags=["OpenAI Compatibility"])
        async def list_models():
            """
            List available models (OpenAI compatibility).
            
            This endpoint mimics the OpenAI /v1/models endpoint, providing information
            about the available models in the system.
            """
            try:
                # For compatibility, we return the configured model
                return {
                    "object": "list",
                    "data": [
                        {
                            "id": self.agent.model_name,
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "ent-cpt-agent"
                        }
                    ]
                }
            
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/v1/chat/completions", tags=["OpenAI Compatibility"])
        async def chat_completions(request: ChatCompletionRequest):
            """
            Generate a chat completion (OpenAI compatibility).
            
            This endpoint mimics the OpenAI /v1/chat/completions endpoint, allowing
            the agent to be used with OpenAI-compatible clients.
            """
            try:
                # Extract messages
                messages = request.messages
                
                # Check for system message
                system_message = None
                user_messages = []
                
                for msg in messages:
                    if msg.role == "system":
                        system_message = msg.content
                    elif msg.role == "user":
                        user_messages.append(msg.content)
                
                # Use the last user message as the query
                if not user_messages:
                    raise HTTPException(status_code=400, detail="No user message provided")
                
                query = user_messages[-1]
                
                # Create or get conversation
                conversation = self.agent.conversation_manager.create_conversation()
                
                # Add system message if provided
                if system_message:
                    conversation.add_message("system", system_message)
                
                # Add previous user messages
                for msg in user_messages[:-1]:
                    conversation.add_message("user", msg)
                
                # Add final user message
                conversation.add_message("user", query)
                
                # Handle streaming if requested
                if request.stream:
                    return StreamingResponse(
                        self._stream_openai_response(query, conversation),
                        media_type="text/event-stream"
                    )
                
                # Process the query
                response = self.agent.process_query(query, conversation)
                
                # Extract CPT codes
                codes = self.agent.conversation_manager.extract_cpt_codes(response)
                
                # Format response for OpenAI compatibility
                return {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": self.agent.model_name,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,  # Placeholder value
                        "completion_tokens": 0,  # Placeholder value
                        "total_tokens": 0  # Placeholder value
                    }
                }
            
            except Exception as e:
                logger.error(f"Error in chat completions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/v1/completions", tags=["OpenAI Compatibility"])
        async def completions(request: CompletionRequest):
            """
            Generate a text completion (OpenAI compatibility).
            
            This endpoint mimics the OpenAI /v1/completions endpoint, providing
            text completions based on the provided prompt.
            """
            try:
                # Use the agent to process the prompt
                response = self.agent.process_query(request.prompt)
                
                # Format response for OpenAI compatibility
                return {
                    "id": f"cmpl-{uuid.uuid4().hex[:12]}",
                    "object": "text_completion",
                    "created": int(time.time()),
                    "model": self.agent.model_name,
                    "choices": [
                        {
                            "text": response,
                            "index": 0,
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,  # Placeholder value
                        "completion_tokens": 0,  # Placeholder value
                        "total_tokens": 0  # Placeholder value
                    }
                }
            
            except Exception as e:
                logger.error(f"Error in completions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ----------------- Debug Routes -----------------
        
        @self.app.get("/debug", tags=["Debug"])
        async def debug_info():
            """Debug endpoint to get information about the application state."""
            return {
                "agent_initialized": self.agent is not None,
                "model_name": self.agent.model_name if self.agent else None,
                "cpt_db_path": self.agent.cpt_db_path if self.agent else None,
                "cpt_codes_loaded": len(self.agent.cpt_db.code_descriptions) if self.agent and self.agent.cpt_db else 0,
                "conversation_dir": self.agent.conversation_manager.conversation_dir if self.agent and self.agent.conversation_manager else None,
                "environment_variables": {k: v for k, v in os.environ.items() if k.startswith(("CONFIG", "WEB", "DEBUG"))}
            }
    
    async def _stream_response(self, query: str, conversation):
        """
        Stream response to the client.
        
        Args:
            query: The user query
            conversation: The conversation object
        
        Yields:
            Chunks of the response as they become available
        """
        try:
            # Process the query
            response = self.agent.process_query(query, conversation)
            
            # Split the response into smaller chunks (simulating streaming)
            chunks = [response[i:i+20] for i in range(0, len(response), 20)]
            
            # Yield chunks with a small delay to simulate streaming
            for chunk in chunks:
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                await asyncio.sleep(0.05)
            
            # Yield end of stream marker
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    async def _stream_openai_response(self, query: str, conversation):
        """
        Stream response in OpenAI format.
        
        Args:
            query: The user query
            conversation: The conversation object
        
        Yields:
            Chunks of the response in OpenAI format
        """
        try:
            # Process the query
            response = self.agent.process_query(query, conversation)
            
            # Split the response into smaller chunks (simulating streaming)
            chunks = [response[i:i+20] for i in range(0, len(response), 20)]
            
            # Stream ID
            stream_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            
            # Yield chunks with a small delay to simulate streaming
            for i, chunk in enumerate(chunks):
                data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": self.agent.model_name,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": chunk
                            },
                            "finish_reason": None if i < len(chunks) - 1 else "stop"
                        }
                    ]
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(0.05)
            
            # Yield end of stream marker
            yield "data: [DONE]\n\n"
        
        except Exception as e:
            logger.error(f"Error streaming OpenAI response: {e}")
            data = {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            yield f"data: {json.dumps(data)}\n\n"
    
    def start(self):
        """Start the API server."""
        logger.info(f"Starting API server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)
    
    def get_app(self):
        """Get the FastAPI application instance."""
        return self.app