'''
File name and location = ent-cpt-agent/src/agent/cpt_database.py
'''

import pandas as pd
import logging
from typing import List, Dict, Any
import os

logger = logging.getLogger("ent_cpt_agent.cpt_database")

class CPTCodeDatabase:
    """
    Handles loading, processing, and querying of CPT codes for ENT procedures.
    
    The CPTCodeDatabase class is responsible for:
    - Loading CPT code data from an Excel file
    - Providing search functionality for codes
    - Retrieving code details and validating codes
    - Organizing codes by category
    - Identifying key indicator codes
    - Managing standard charge information
    
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

        self.code_subspecialty = {}

        # Set of codes that are key indicators
        self.key_indicators = set()
        # Dictionary of code to standard charge mappings
        self.standard_charges = {}
        self.load_data()

    def load_data(self) -> None:
        """
        Load CPT code data from Excel file and process it.
        
        This method reads the Excel file and populates the internal
        data structures for efficient code lookup and search.
        """
        logger.info(f"Loading CPT code data from {self.file_path}")
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
                code_column_names = ['CPT_code']
                code = None
                
                # Try to find the code in any of the possible column names
                for col_name in code_column_names:
                    if col_name in row and not pd.isna(row[col_name]):
                        # Convert to string (handles numeric CPT codes)
                        code = str(row[col_name]).strip()
                        break
                
                if code and not pd.isna(code):
                    # Store description - try to find description column
                    desc_column_names = ['description']
                    description = ""
                    for desc_col in desc_column_names:
                        if desc_col in row and not pd.isna(row[desc_col]):
                            description = row[desc_col]
                            break
                    
                    self.code_descriptions[code] = description
                    row_count += 1
                    
                    # Store category
                    category_cols = ['category']
                    category = ""
                    for cat_col in category_cols:
                        if cat_col in row and not pd.isna(row[cat_col]):
                            category = row[cat_col]
                            break
                            
                    if category:
                        if category not in self.code_categories:
                            self.code_categories[category] = []
                        self.code_categories[category].append(code)

                    # Store subspecialty
                    subspecialty_cols = ['subspecialty']
                    subspecialty = ""
                    for subsp_col in subspecialty_cols:
                        if subsp_col in row and not pd.isna(row[subsp_col]):
                            subspecialty = row[subsp_col]
                            break
                            
                    if subspecialty:
                        if subspecialty not in self.code_subspecialty:
                            self.code_subspecialty[subspecialty] = []
                        self.code_subspecialty[subspecialty].append(code)

                    # NEW: Check for key indicator status
                    key_indicator_cols = ['key_indicator']
                    for ki_col in key_indicator_cols:
                        if ki_col in row and not pd.isna(row[ki_col]):
                            # Check if it's a boolean True, 'Yes', 'Y', 1, etc.
                            ki_value = row[ki_col]
                            if isinstance(ki_value, bool) and ki_value:
                                self.key_indicators.add(code)
                            elif isinstance(ki_value, (int, float)) and ki_value == 1:
                                self.key_indicators.add(code)
                            elif isinstance(ki_value, str) and ki_value.lower() in ['yes', 'y', 'true', 't', '1']:
                                self.key_indicators.add(code)
                            break
                    
                    # NEW: Check for standard charge
                    charge_cols = ['standard_charge']
                    for charge_col in charge_cols:
                        if charge_col in row and not pd.isna(row[charge_col]):
                            charge_value = row[charge_col]
                            # Handle various formats (remove currency symbols, commas, etc.)
                            if isinstance(charge_value, str):
                                try:
                                    charge_value = float(charge_value)
                                except ValueError:
                                    logger.warning(
                                        f"Could not convert charge value '{row[charge_col]}' to float for code {code}"
                                    )
                                    continue
                            if isinstance(charge_value, (int, float)):
                                self.standard_charges[code] = float(charge_value)
                            break
            
            logger.info(
                f"Loaded {row_count} CPT codes, "
                f"{len(self.key_indicators)} key indicators, "
                f"{len(self.standard_charges)} with standard charges"
            )
        except Exception as e:
            logger.error(f"Error loading CPT codes: {e}")
            raise

        # Now that we've loaded our data, either return the entire dictionary or simply finish
        # We'll just return self.code_descriptions for convenience
        return self.code_descriptions

    def search_codes(self, query: str, limit: int = 10) -> list:
        """
        Searches for CPT codes that match the given query in the description fields.

        :param query: The text query to search for.
        :param limit: The maximum number of results to return.
        :return: A list of dictionaries representing matching CPT codes.
        """
        if not hasattr(self, 'df'):
            raise AttributeError("CPTCodeDatabase does not have a 'df' attribute. Ensure data is loaded properly.")

        try:
            # Filter rows where any relevant column contains the query
            matching_rows = self.df[
                self.df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)
            ].head(limit)

            return matching_rows.to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error searching codes: {e}")
            # Return an empty list if search fails
            return []


    def is_key_indicator(self, code: str) -> bool:
        """
        Check if a CPT code is a key indicator.
        
        Args:
            code: The CPT code to check
            
        Returns:
            True if the code is a key indicator, False otherwise
        """
        return code in self.key_indicators

    def get_standard_charge(self, code: str) -> float:
        """
        Get the standard charge for a CPT code.
        
        Args:
            code: The CPT code to get the charge for
            
        Returns:
            The standard charge amount, or 0.0 if not available
        """
        return self.standard_charges.get(code, 0.0)
        
    def get_code_validation(self, code: str) -> Dict[str, Any]:
        """
        Validate if a CPT code exists and is valid.
        
        Args:
            code: The CPT code to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            if code in self.code_descriptions:
                return {
                    "valid": True,
                    "code": code,
                    "description": self.code_descriptions.get(code, "")
                }
            else:
                return {
                    "valid": False,
                    "code": code,
                    "error": f"Invalid CPT code: {code}"
                }
        except Exception as e:
            logger.error(f"Error validating code {code}: {e}")
            return {
                "valid": False,
                "code": code,
                "error": str(e)
            }
    
    def get_code_details(self, code: str) -> Dict[str, Any]:
        """
        Get detailed information about a CPT code.
        
        Args:
            code: The CPT code to get details for
            
        Returns:
            Dictionary with code details
        """
        try:
            if code not in self.code_descriptions:
                return {"error": f"CPT code {code} not found"}
                
            # Get the category for this code
            category = ""
            for cat, codes in self.code_categories.items():
                if code in codes:
                    category = cat
                    break
            
            # Get the subspecialty for this code
            subspecialty = ""
            for subspec, codes in self.code_subspecialty.items():
                if code in codes:
                    subspecialty = subspec
                    break
                    
            return {
                "code": code,
                "description": self.code_descriptions.get(code, ""),
                "category": category,
                "subspecialty": subspecialty,
                "key_indicator": self.is_key_indicator(code),
                "standard_charge": self.get_standard_charge(code)
            }
            
        except Exception as e:
            logger.error(f"Error getting details for code {code}: {e}")
            return {"error": str(e)}