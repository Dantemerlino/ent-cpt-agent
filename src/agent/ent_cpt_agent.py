"""
Streamlined ENT CPT Agent implementation with direct database lookup.
"""

import logging
import json
import re
import os
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
        
        # Fix database path - ensure we're using absolute path when needed
        cpt_db_path = self.config.get("cpt_database", "file_path")
        
        # If the path is relative and not found, try constructing an absolute path
        if not os.path.isabs(cpt_db_path) and not os.path.exists(cpt_db_path):
            # Try from project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            self.cpt_db_path = os.path.join(project_root, cpt_db_path) 
            if not os.path.exists(self.cpt_db_path):
                # If still not found, try the alternative file in the root directory
                self.cpt_db_path = os.path.join(project_root, 'CPT codes for ENT.xlsx')
                if not os.path.exists(self.cpt_db_path):
                    logger.warning(f"Could not find CPT database file at {self.cpt_db_path}")
                    logger.warning("Falling back to direct path")
                    self.cpt_db_path = 'CPT codes for ENT.xlsx'
        else:
            self.cpt_db_path = cpt_db_path
            
        logger.info(f"Using CPT database path: {self.cpt_db_path}")
        
        # Set model to True for compatibility
        self.model = True
        
        # Initialize OpenAI client for LM Studio
        server_config = self.config.get("server")
        base_url = server_config.get("lm_studio_base_url", "http://localhost:1234/v1")
        api_key = server_config.get("lm_studio_api_key", "lm-studio")
        
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        logger.info(f"Connected to LM Studio at {base_url}")
        
        # Initialize components
        self.cpt_db = CPTCodeDatabase(self.cpt_db_path)
        self.rules_engine = RulesEngine()
        self.conversation_manager = conversation_manager
        
        # Enhance CPT database with better search capabilities
        self._enhance_cpt_database()
        
        logger.info("ENTCPTAgent initialized successfully")
    
    def initialize_model(self) -> None:
        """Compatibility method for model initialization."""
        self.model = True
        logger.info("Model compatibility layer initialized")
    
    def _enhance_cpt_database(self) -> None:
        """Add enhanced search capabilities to the CPT database."""
        # Create keyword index for faster and more accurate searches
        self.cpt_db.keyword_index = {}
        
        # Map of common procedure terms to standardized keywords
        self.cpt_db.procedure_term_map = {
            # Parotid procedures
            "parotid": ["parotid", "parotidectomy", "salivary"],
            "parotidectomy": ["parotid", "parotidectomy", "salivary"],
            "salivary": ["parotid", "submandibular", "salivary", "gland"],
            
            # Ear procedures
            "ear": ["ear", "aural", "tympanic", "mastoid", "cochlear"],
            "tympano": ["ear", "tympanic", "tympanoplasty"],
            "mastoid": ["ear", "mastoid", "mastoidectomy"],
            "myringotomy": ["ear", "myringotomy", "tympanic"],
            
            # Nose procedures
            "nose": ["nose", "nasal", "rhinoplasty", "septum", "turbinate"],
            "nasal": ["nose", "nasal", "rhinoplasty", "septum"],
            "sinus": ["sinus", "endoscopic", "maxillary", "frontal", "ethmoid"],
            "septum": ["nose", "septum", "septoplasty"],
            
            # Throat procedures
            "throat": ["throat", "pharynx", "tonsil", "adenoid", "larynx"],
            "tonsil": ["tonsil", "tonsillectomy", "adenoid"],
            "adenoid": ["adenoid", "adenoidectomy", "tonsil"],
            "larynx": ["larynx", "laryngoscopy", "laryngeal"],
            
            # Common procedure types
            "biopsy": ["biopsy", "excision", "removal"],
            "excision": ["excision", "removal", "resection"],
            "endoscopic": ["endoscopic", "endoscopy", "scope"],
            "partial": ["partial", "incomplete", "subtotal"],
            "total": ["total", "complete", "entire"]
        }
        
        # Build the keyword index
        for code, description in self.cpt_db.code_descriptions.items():
            description_lower = description.lower()
            
            # Add each word in the description as a key
            for word in description_lower.split():
                if len(word) > 3:  # Only index words longer than 3 characters
                    if word not in self.cpt_db.keyword_index:
                        self.cpt_db.keyword_index[word] = []
                    self.cpt_db.keyword_index[word].append(code)
            
            # Add expanded keywords for common terms
            for term, related_keywords in self.cpt_db.procedure_term_map.items():
                if term in description_lower:
                    for keyword in related_keywords:
                        if keyword not in self.cpt_db.keyword_index:
                            self.cpt_db.keyword_index[keyword] = []
                        if code not in self.cpt_db.keyword_index[keyword]:
                            self.cpt_db.keyword_index[keyword].append(code)
    
    def _search_codes(self, query: str) -> List[Dict[str, Any]]:
        """
        Enhanced search for CPT codes with better keyword matching.
        
        Args:
            query: Search terms for finding relevant CPT codes
            
        Returns:
            List of matching CPT codes with descriptions
        """
        query_lower = query.lower()
        results = []
        matched_codes = set()
        
        # First try exact matching as in original search
        for code, description in self.cpt_db.code_descriptions.items():
            if query_lower in description.lower() or query_lower in code:
                results.append({
                    "code": code,
                    "description": description,
                    "related_codes": self.cpt_db.related_codes.get(code, []),
                    "match_quality": "exact",
                    "score": 100  # Give exact matches a high score
                })
                matched_codes.add(code)
        
        # If exact matching yielded results, return them
        if results:
            return results
        
        # No exact matches, try keyword matching
        query_terms = query_lower.split()
        
        # Expand query terms using our term map
        expanded_terms = set()
        for term in query_terms:
            expanded_terms.add(term)
            if hasattr(self.cpt_db, 'procedure_term_map') and term in self.cpt_db.procedure_term_map:
                expanded_terms.update(self.cpt_db.procedure_term_map[term])
        
        # Search using expanded terms
        code_scores = {}  # Track match scores for each code
        
        for term in expanded_terms:
            if hasattr(self.cpt_db, 'keyword_index') and term in self.cpt_db.keyword_index:
                for code in self.cpt_db.keyword_index[term]:
                    if code not in matched_codes:  # Skip already matched codes
                        if code not in code_scores:
                            code_scores[code] = 0
                        code_scores[code] += 1
        
        # Add scored matches to results
        for code, score in code_scores.items():
            if score > 0:
                results.append({
                    "code": code,
                    "description": self.cpt_db.code_descriptions.get(code, ""),
                    "related_codes": self.cpt_db.related_codes.get(code, []),
                    "match_quality": "keyword",
                    "score": score
                })
                matched_codes.add(code)
        
        # Sort results by score (highest first)
        results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
        
        return results
    
    def _get_procedure_explanation(self, query: str) -> str:
        """
        Get a general explanation about a procedure without asking for specific codes.
        
        Args:
            query: The user's question or procedure description
            
        Returns:
            General explanation about the procedure
        """
        try:
            # Create a message that asks for explanation only, not codes
            messages = [
                {
                    "role": "system", 
                    "content": "You are a medical expert who explains ENT procedures. Your task is to provide brief, accurate explanations of ENT procedures, diagnostic methods, or treatments. DO NOT mention or recommend any specific CPT codes."
                },
                {
                    "role": "user", 
                    "content": f"Please briefly explain this ENT query in 2-3 sentences: '{query}'. Focus only on what the procedure or condition involves, not on coding."
                }
            ]
            
            # Get explanation from model
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,  # Lower temperature for more factual response
                max_tokens=150    # Limit token count for brief response
            )
            
            explanation = response.choices[0].message.content.strip()
            
            # Remove any mention of CPT codes that might have slipped through
            explanation = re.sub(r'\b\d{5}\b', '[code]', explanation)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error getting procedure explanation: {e}")
            return "This query relates to ENT (Ear, Nose, Throat) procedures. I'll provide relevant codes from our verified database."
    
    def process_query(self, query: str, conversation=None) -> str:
        """
        Process a query with direct database lookup for guaranteed accuracy.
        
        Args:
            query: The user's question or procedure description
            conversation: Optional Conversation object
            
        Returns:
            Response with verified CPT codes directly from the database
        """
        logger.info(f"Processing query: {query}")
        query_lower = query.lower()
        
        # Step 1: Find relevant CPT codes from the database
        relevant_codes = self._search_codes(query)
        
        # If no codes found, try additional keyword extraction
        if not relevant_codes:
            keywords = []
            
            # Check for specific ENT procedures or terms in the query
            all_ent_keywords = [
                # Ear procedures
                "tympano", "myringotomy", "mastoid", "mastoidectomy", "tympanoplasty", 
                "ossicular", "stapedectomy", "cochlear", "labyrinth", "vestibular", "temporal",
                
                # Nose procedures
                "rhinoplasty", "septoplasty", "septum", "turbinate", "nasal", "turbinectomy",
                "polypectomy", "rhinectomy", "epistaxis",
                
                # Sinus procedures
                "sinus", "sinusotomy", "sinusectomy", "maxillary", "frontal", "ethmoid", "sphenoid",
                "antrostomy", "endoscopic", "fess", "antral",
                
                # Throat/pharynx
                "pharynx", "pharyngeal", "uvula", "uvulectomy", "palate", "palatoplasty",
                "oropharynx", "nasopharynx", "hypopharynx",
                
                # Tonsil and adenoid
                "tonsil", "tonsillectomy", "adenoid", "adenoidectomy", "adenotonsillectomy",
                
                # Larynx
                "larynx", "laryngoscopy", "laryngoplasty", "laryngectomy", "cordectomy",
                "arytenoid", "vocal", "cord", "tracheostomy", "tracheotomy",
                
                # Salivary glands
                "parotid", "parotidectomy", "submandibular", "sublingual", "salivary", "sialolithotomy",
                "sialoadenectomy", "sialography", "sialendoscopy",
                
                # Facial nerve
                "facial", "nerve", "nervectomy", "decompression", "neurolysis", "neuroplasty",
                
                # Thyroid and parathyroid
                "thyroid", "thyroidectomy", "parathyroid", "parathyroidectomy", "lobectomy",
                
                # Common procedure types
                "biopsy", "excision", "incision", "drainage", "removal", "aspiration", "resection",
                "reconstruction", "repair", "partial", "total", "ligation", "cauterization",
                "exploration", "debridement", "dilation"
            ]
            
            for keyword in all_ent_keywords:
                if keyword in query_lower:
                    keywords.append(keyword)
            
            # Search for each extracted keyword
            for keyword in keywords:
                keyword_results = self._search_codes(keyword)
                relevant_codes.extend(keyword_results)
        
        # Step 2: Get a general explanation from the LLM
        explanation = self._get_procedure_explanation(query)
        
        # Step 3: Format the response
        response = f"**{query}**\n\n"
        response += f"{explanation}\n\n"
        
        # Add the CPT codes section
        if relevant_codes:
            response += "**Verified CPT Codes from Database:**\n"
            
            # Remove duplicates while preserving order
            seen_codes = set()
            unique_codes = []
            for code_info in relevant_codes:
                code = code_info["code"]
                if code not in seen_codes:
                    seen_codes.add(code)
                    unique_codes.append(code_info)
            
            # Sort by match quality and score
            unique_codes.sort(key=lambda x: (
                0 if x.get('match_quality') == 'exact' else 1,
                -x.get('score', 0)
            ))
            
            # Display sorted codes (limit to top 10)
            for i, code_info in enumerate(unique_codes[:10], 1):
                code = code_info["code"]
                description = code_info["description"]
                related_codes = code_info.get("related_codes", [])
                
                response += f"{i}. **{code}**: {description}\n"
                
                # Add related codes if any
                if related_codes:
                    related_desc = []
                    for rel_code in related_codes[:3]:  # Limit to 3 related codes
                        rel_description = self.cpt_db.code_descriptions.get(rel_code, "")
                        if rel_description:
                            related_desc.append(f"{rel_code} ({rel_description})")
                        else:
                            related_desc.append(rel_code)
                    
                    if related_desc:
                        response += f"   Related codes: {', '.join(related_desc)}\n"
        else:
            response += "**No specific CPT codes found in our database for this query.**\n"
            response += "Please try rephrasing with more specific ENT procedure terminology.\n"
        
        # Add coding guidance
        response += "\n**Coding Guidance:**\n"
        response += "- Select the code that most accurately describes the specific procedure performed\n"
        response += "- Check if any modifiers apply (e.g., -50 for bilateral procedures)\n"
        response += "- Ensure documentation in the medical record supports the selected code\n"
        
        # Add note about verification
        response += "\n*All CPT codes provided are directly verified from our CPT code database.*"
        
        # Add to conversation history if provided
        if conversation and hasattr(conversation, 'add_message'):
            conversation.add_message("assistant", response)
        
        return response
    
    def extract_cpt_codes(self, text: str) -> List[str]:
        """Extract CPT codes from text."""
        if not isinstance(text, str):
            text = str(text)
            
        pattern = r'\b\d{5}(?:-\d{1,2})?\b'
        matches = re.findall(pattern, text)
        return matches