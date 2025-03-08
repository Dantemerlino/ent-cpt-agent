"""
Configuration manager for the ENT CPT Code Agent.
"""

import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("ent_cpt_agent.config")

class AgentConfig:
    """
    Configuration manager for the ENT CPT Code Agent.
    Handles loading, saving, and accessing configuration settings.
    """
    
    DEFAULT_CONFIG = {
        "model": {
            "name": "qwen2.5-14b-instruct",
            "temperature": 0,
            "max_tokens": 1024,
            "context_length": 8192
        },
        "cpt_database": {
            "file_path": "CPT codes for ENT.xlsx",
            "sheet_name": "Sheet1"
        },
        "agent": {
            "log_level": "INFO",
            "save_conversations": True,
            "conversation_dir": "conversations"
        },
        "server": {
            "host": "localhost",
            "port": 8000,
            "enable_api": False,
            "lm_studio_base_url": "http://localhost:1234/v1",
            "lm_studio_api_key": "lm-studio"
        }
    }
    
    def __init__(self, config_path: Optional[str] = "config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file (default: "config.json")
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file if it exists."""
        if not self.config_path or not os.path.exists(self.config_path):
            logger.info(f"Config file not found at {self.config_path}, using defaults")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
                
            # Update the default config with loaded values
            self._update_nested_dict(self.config, loaded_config)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    def _update_nested_dict(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a general explanation about a procedure without asking for specific codes.
        
        Args:
            d: Target dictionary to update
            u: Source dictionary with new values
            
        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def save_config(self) -> None:
        """Save the current configuration to file."""
        if not self.config_path:
            logger.warning("No config path specified, cannot save configuration")
            return
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
    
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section (e.g., "model", "agent")
            key: Specific key within the section (optional)
            
        Returns:
            Configuration value or section dictionary
        """
        if section not in self.config:
            return None
        
        if key is None:
            return self.config[section]
        
        return self.config[section].get(key)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            section: Configuration section (e.g., "model", "agent")
            key: Specific key within the section
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def create_default_config(self) -> None:
        """Create a default configuration file if it doesn't exist."""
        if not self.config_path:
            logger.warning("No config path specified, cannot create default configuration")
            return
        
        if os.path.exists(self.config_path):
            logger.info(f"Config file already exists at {self.config_path}")
            return
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2)
            
            logger.info(f"Created default configuration at {self.config_path}")
        except Exception as e:
            logger.error(f"Error creating default config file: {e}")


def setup_logging(config: AgentConfig) -> None:
    """
    Set up logging based on configuration.
    
    Args:
        config: Agent configuration object
    """
    log_level_name = config.get("agent", "log_level")
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ent_cpt_agent.log")
        ]
    )