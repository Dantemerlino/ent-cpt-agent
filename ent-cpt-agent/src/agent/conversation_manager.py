import json
import os
import datetime
import uuid
import re  # Added missing import for regex pattern matching
from typing import List, Dict, Any, Optional
import logging
import lmstudio as lms

logger = logging.getLogger("ent_cpt_agent.conversation")

class Conversation:
    """
    Represents a conversation session with the ENT CPT Code Agent.
    
    This class handles individual conversations between the user and agent,
    including message history, metadata, and serialization/deserialization.
    """
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize a new conversation.
        
        Args:
            session_id: Optional session ID (generates a new one if not provided)
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = datetime.datetime.now()
        self.messages = []
        self.metadata = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "total_messages": 0,
            "total_codes_identified": 0
        }
    
    def add_message(self, role: str, content: str, codes: List[str] = None) -> None:
        """
        Add a message to the conversation.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            codes: List of CPT codes mentioned in the message (optional)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if codes:
            message["codes"] = codes
            self.metadata["total_codes_identified"] += len(codes)
        
        self.messages.append(message)
        self.metadata["total_messages"] = len(self.messages)
    
    def to_lmstudio_chat(self, system_prompt: str) -> lms.Chat:
        """
        Convert the conversation to an LM Studio Chat object.
        
        This method transforms our internal conversation representation
        to the format expected by LM Studio's API.
        
        Args:
            system_prompt: System prompt to use for the chat
            
        Returns:
            LM Studio Chat object representing this conversation
        """
        chat = lms.Chat(system_prompt)
        
        for message in self.messages:
            if message["role"] == "user":
                chat.add_user_message(message["content"])
            elif message["role"] == "assistant":
                chat.add_assistant_message(message["content"])
            # System messages are handled by the initial system prompt
        
        return chat
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conversation to a dictionary.
        
        Returns:
            Dictionary representation of the conversation
        """
        return {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "messages": self.messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        Create a conversation from a dictionary.
        
        This factory method reconstructs a Conversation object
        from a previously serialized dictionary representation.
        
        Args:
            data: Dictionary representation of a conversation
            
        Returns:
            Conversation object
        """
        conversation = cls(session_id=data.get("session_id"))
        conversation.metadata = data.get("metadata", {})
        conversation.messages = data.get("messages", [])
        
        # Parse start_time from metadata if available
        start_time_str = conversation.metadata.get("start_time")
        if start_time_str:
            try:
                conversation.start_time = datetime.datetime.fromisoformat(start_time_str)
            except (ValueError, TypeError):
                logger.warning(f"Could not parse start_time: {start_time_str}")
        
        return conversation


class ConversationManager:
    """
    Manages multiple conversations, including loading/saving to disk.
    
    This class handles the lifecycle of conversations, including:
    - Creating new conversations
    - Loading existing conversations from disk
    - Saving conversations to disk
    - Listing available conversations
    - Extracting CPT codes from conversation text
    """
    def __init__(self, conversation_dir: str = "conversations"):
        """
        Initialize the conversation manager.
        
        Args:
            conversation_dir: Directory to store conversation files
        """
        self.conversation_dir = conversation_dir
        self.current_conversation = None
        self.conversations = {}
        
        # Create conversation directory if it doesn't exist
        os.makedirs(self.conversation_dir, exist_ok=True)
        
        # Load existing conversations
        self.load_conversations()
    
    def load_conversations(self) -> None:
        """
        Load all saved conversations from the conversation directory.
        
        This method scans the conversation directory for JSON files,
        loads them, and reconstructs Conversation objects.
        """
        if not os.path.exists(self.conversation_dir):
            logger.warning(f"Conversation directory not found: {self.conversation_dir}")
            return
        
        try:
            for filename in os.listdir(self.conversation_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.conversation_dir, filename)
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                conversation = Conversation.from_dict(data)
                self.conversations[conversation.session_id] = conversation
                
            logger.info(f"Loaded {len(self.conversations)} conversations")
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
    
    def save_conversation(self, conversation: Conversation) -> None:
        """
        Save a conversation to disk.
        
        Args:
            conversation: Conversation to save
        """
        if not conversation:
            logger.error("Cannot save empty conversation")
            return
        
        file_path = os.path.join(self.conversation_dir, f"{conversation.session_id}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(conversation.to_dict(), f, indent=2)
            
            logger.info(f"Saved conversation {conversation.session_id}")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def create_conversation(self) -> Conversation:
        """
        Create a new conversation.
        
        Returns:
            Newly created conversation
        """
        conversation = Conversation()
        self.conversations[conversation.session_id] = conversation
        self.current_conversation = conversation
        return conversation
    
    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """
        Get a conversation by session ID.
        
        Args:
            session_id: Session ID of the conversation to retrieve
            
        Returns:
            Conversation object or None if not found
        """
        return self.conversations.get(session_id)
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        Get a list of all conversations with their metadata.
        
        Returns:
            List of conversation metadata dictionaries
        """
        result = []
        for session_id, conversation in self.conversations.items():
            result.append({
                "session_id": session_id,
                "start_time": conversation.metadata.get("start_time"),
                "total_messages": conversation.metadata.get("total_messages", 0),
                "total_codes_identified": conversation.metadata.get("total_codes_identified", 0)
            })
        
        # Sort by start time (newest first)
        result.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        return result
    
    def delete_conversation(self, session_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            session_id: Session ID of the conversation to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if session_id not in self.conversations:
            logger.warning(f"Conversation not found: {session_id}")
            return False
        
        # Remove from memory
        del self.conversations[session_id]
        
        # Remove from disk
        file_path = os.path.join(self.conversation_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted conversation file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting conversation file: {e}")
                return False
        
        # Reset current conversation if it was deleted
        if self.current_conversation and self.current_conversation.session_id == session_id:
            self.current_conversation = None
        
        return True
    
    def extract_cpt_codes(self, text: str) -> List[str]:
        """
        Extract CPT codes from text using regex pattern matching.
        
        This method identifies potential CPT codes in text by looking
        for 5-digit numbers that may be followed by modifiers.
        
        Args:
            text: Text to extract CPT codes from
            
        Returns:
            List of extracted CPT codes
        """
        # CPT codes are typically 5 digits or 5 digits followed by F or T or a two-digit modifier
        pattern = r'\b\d{5}(?:[FT]|\d{2})?\b'
        matches = re.findall(pattern, text)
        return matches