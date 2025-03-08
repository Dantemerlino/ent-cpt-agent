import pandas as pd
import logging
from typing import List, Dict, Any

logger = logging.getLogger("ent_cpt_agent.cpt_database")

class CPTCodeDatabase:
    """
    Handles loading, processing, and querying of CPT codes for ENT procedures.
    
    The CPTCodeDatabase class is responsible for:
    - Loading CPT code data from an Excel file
    - Providing search functionality for codes
    - Retrieving code details and validating codes
    - Organizing codes by category
    
    This serves as the data layer for the ENT CPT Code Agent.
    """
    def __init__(self, file_path: str):
        """
        Initialize the CPT code database from the provided Excel file.
        
        Args:
            file_path: Path to the Excel file containing CPT codes
        """
        self.file_path = file_path
        self.df = None
        # Dictionary of code to description mappings
        self.code_descriptions = {}
        # Dictionary of category to list of codes mappings
        self.code_categories = {}
        # Dictionary of code to related codes mappings
        self.related_codes = {}
        self.load_data()
    
    def load_data(self) -> None:
        """
        Load CPT code data from Excel file and process it.
        
        This method reads the Excel file and populates the internal
        data structures for efficient code lookup and search.
        """
        logger.info(f"Loading CPT codes from {self.file_path}")
        try:
            # Load the Excel file into a pandas DataFrame
            self.df = pd.read_excel(self.file_path)
            
            # Log DataFrame info for debugging
            logger.info(f"Excel file loaded: {len(self.df)} rows, {len(self.df.columns)} columns")
            logger.info(f"Column names: {self.df.columns.tolist()}")
            
            # Check first few rows
            if len(self.df) > 0:
                logger.info(f"First row sample: {self.df.iloc[0].to_dict()}")
            
            # Process the dataframe to create lookup dictionaries
            row_count = 0
            for _, row in self.df.iterrows():
                # Try different column name variations
                code_column_names = ['CPT Code', 'CPT_Code', 'CPTCode', 'Code', 'cpt_code', 'cpt code', 'CPT']
                code = None
                
                # Try to find the code in any of the possible column names
                for col_name in code_column_names:
                    if col_name in row and not pd.isna(row[col_name]):
                        # Convert to string (handles numeric CPT codes)
                        code = str(row[col_name]).strip()
                        break
                
                if code and not pd.isna(code):
                    # Store description - try to find description column
                    desc_column_names = ['Description', 'Desc', 'description', 'desc', 'Detailed description']
                    description = ""
                    for desc_col in desc_column_names:
                        if desc_col in row and not pd.isna(row[desc_col]):
                            description = row[desc_col]
                            break
                    
                    self.code_descriptions[code] = description
                    row_count += 1
                    
                    # Store category
                    category_cols = ['Category', 'category', 'Type', 'type', 'Area', 'area']
                    category = ""
                    for cat_col in category_cols:
                        if cat_col in row and not pd.isna(row[cat_col]):
                            category = row[cat_col]
                            break
                            
                    if category:
                        if category not in self.code_categories:
                            self.code_categories[category] = []
                        self.code_categories[category].append(code)
                    
                    # Store related codes
                    related_cols = ['Related Codes', 'Related_Codes', 'Related', 'related_codes', 'related']
                    related = ""
                    for rel_col in related_cols:
                        if rel_col in row and not pd.isna(row[rel_col]):
                            related = row[rel_col]
                            break
                            
                    if related:
                        related_codes = [r.strip() for r in str(related).split(',')]
                        self.related_codes[code] = related_codes
            
            logger.info(f"Loaded {row_count} CPT codes")
        except Exception as e:
            logger.error(f"Error loading CPT codes: {e}")
            raise
    
    def search_codes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for CPT codes based on a text query.
        
        This method searches for codes whose descriptions or code numbers
        contain the search query.
        
        Args:
            query: Search terms for finding relevant CPT codes
            
        Returns:
            List of matching CPT codes with descriptions
        """
        query = query.lower()
        results = []
        
        # Search in both code numbers and descriptions
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
        
        This method retrieves all available information about a
        specific CPT code, including its description and related codes.
        
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
        
        This method retrieves all codes that are classified under
        a particular category (e.g., "Ear", "Nose", "Throat").
        
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
        
        This method checks if a given CPT code exists in the database
        and returns its validation status.
        
        Args:
            code: The CPT code to validate
            
        Returns:
            Dictionary with validation results
        """
        if code in self.code_descriptions:
            return {"valid": True, "description": self.code_descriptions[code]}
        else:
            return {"valid": False, "error": f"Invalid CPT code: {code}"}