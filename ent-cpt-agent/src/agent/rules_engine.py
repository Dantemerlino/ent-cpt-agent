from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger("ent_cpt_agent.rules_engine")

@dataclass
class CodeRule:
    """Represents a rule for CPT code selection."""
    rule_id: str
    description: str
    conditions: List[Dict[str, Any]]
    priority: int = 0
    
    def __str__(self) -> str:
        return f"Rule {self.rule_id}: {self.description} (Priority: {self.priority})"


class RulesEngine:
    """
    Implements a rules engine for CPT code selection based on medical coding guidelines.
    """
    def __init__(self):
        """Initialize the rules engine with ENT-specific CPT coding rules."""
        self.rules = []
        self.initialize_rules()
    
    def initialize_rules(self) -> None:
        """Load default rules for ENT CPT coding."""
        # Rule: Bundled procedures
        self.rules.append(CodeRule(
            rule_id="R001",
            description="Check for bundled procedures",
            conditions=[
                {"type": "bundled_codes", "codes": []}
            ],
            priority=10
        ))
        
        # Rule: Bilateral procedures
        self.rules.append(CodeRule(
            rule_id="R002",
            description="Check for bilateral procedures (use modifier 50)",
            conditions=[
                {"type": "procedure_bilateral", "keywords": ["bilateral", "both sides", "both ears"]}
            ],
            priority=8
        ))
        
        # Rule: Follow-up visits
        self.rules.append(CodeRule(
            rule_id="R003",
            description="Check for post-operative visits (usually included in surgical package)",
            conditions=[
                {"type": "post_op", "keywords": ["follow-up", "post-op", "postoperative"]}
            ],
            priority=9
        ))
        
        # Rule: Check for multiple procedures
        self.rules.append(CodeRule(
            rule_id="R004",
            description="Check for multiple procedures (additional procedures may require modifier 51)",
            conditions=[
                {"type": "multiple_procedures", "patterns": [
                    r"\bmultiple\s+procedures\b",
                    r"\bseveral\s+procedures\b"
                ]}
            ],
            priority=7
        ))
        
        # Rule: Check for medical necessity
        self.rules.append(CodeRule(
            rule_id="R005",
            description="Verify medical necessity documentation",
            conditions=[
                {"type": "medical_necessity", "required": True}
            ],
            priority=6
        ))
        
        logger.info(f"Initialized {len(self.rules)} CPT coding rules")
    
    def add_rule(self, rule: CodeRule) -> None:
        """
        Add a new rule to the engine.
        
        Args:
            rule: The rule to add
        """
        self.rules.append(rule)
        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Added rule: {rule}")
    
    def evaluate_bundled_codes(self, procedure_text: str, candidate_codes: List[str], 
                               code_db) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
        """
        Check for bundled procedure codes.
        
        Args:
            procedure_text: Description of the procedure
            candidate_codes: List of potential CPT codes
            code_db: Database of CPT codes
            
        Returns:
            Tuple of (recommended_codes, excluded_codes, explanations)
        """
        recommended = []
        excluded = []
        explanations = []
        
        # Check each candidate code
        for code in candidate_codes:
            details = code_db.get_code_details(code)
            
            # Skip if code not found
            if "error" in details:
                continue
            
            # Check related codes for potential bundling
            related_codes = details.get("related_codes", [])
            bundled_with = []
            
            for related in related_codes:
                if related in candidate_codes:
                    bundled_with.append(related)
            
            if bundled_with:
                # This code might be bundled with others
                # In a real implementation, we would check a bundling database
                explanations.append({
                    "rule_id": "R001",
                    "code": code,
                    "message": f"Code {code} may be bundled with {', '.join(bundled_with)}. "
                               f"Check coding guidelines to determine which code to use."
                })
                
                # For demonstration, we'll add the main code and exclude related codes
                # (This logic should be updated based on actual bundling rules)
                if code not in excluded:
                    recommended.append(code)
                    excluded.extend(bundled_with)
            elif code not in excluded:
                recommended.append(code)
        
        return recommended, excluded, explanations
    
    def evaluate_bilateral_procedures(self, procedure_text: str, candidate_codes: List[str],
                                     code_db) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Check for bilateral procedures that require modifier 50.
        
        Args:
            procedure_text: Description of the procedure
            candidate_codes: List of potential CPT codes
            code_db: Database of CPT codes
            
        Returns:
            Tuple of (modified_codes, explanations)
        """
        modified_codes = []
        explanations = []
        
        # Check if the procedure description indicates a bilateral procedure
        bilateral_keywords = ["bilateral", "both sides", "both ears", "right and left"]
        is_bilateral = any(keyword in procedure_text.lower() for keyword in bilateral_keywords)
        
        if is_bilateral:
            for code in candidate_codes:
                # In a real implementation, we would check if the code is eligible for modifier 50
                modified_codes.append(f"{code}-50")
                explanations.append({
                    "rule_id": "R002",
                    "code": code,
                    "message": f"Added modifier 50 to code {code} for bilateral procedure."
                })
        else:
            modified_codes = candidate_codes
        
        return modified_codes, explanations
    
    def analyze_procedure(self, procedure_text: str, candidate_codes: List[str], 
                         code_db) -> Dict[str, Any]:
        """
        Analyze a procedure description and apply coding rules to suggest the
        most appropriate CPT codes.
        
        Args:
            procedure_text: Description of the procedure
            candidate_codes: List of potential CPT codes
            code_db: Database of CPT codes
            
        Returns:
            Dictionary with analysis results and recommendations
        """
        logger.info(f"Analyzing procedure: {procedure_text}")
        logger.info(f"Candidate codes: {candidate_codes}")
        
        if not candidate_codes:
            return {
                "status": "error",
                "message": "No candidate codes provided for analysis",
                "recommended_codes": []
            }
        
        recommended_codes = candidate_codes.copy()
        excluded_codes = []
        explanations = []
        modifiers = {}
        
        # Apply each rule in priority order
        for rule in self.rules:
            logger.info(f"Applying rule: {rule}")
            
            try:
                if rule.rule_id == "R001":  # Bundled procedures
                    rec, exc, exp = self.evaluate_bundled_codes(
                        procedure_text, recommended_codes, code_db)
                    recommended_codes = rec
                    excluded_codes.extend(exc)
                    explanations.extend(exp)
                
                elif rule.rule_id == "R002":  # Bilateral procedures
                    rec, exp = self.evaluate_bilateral_procedures(
                        procedure_text, recommended_codes, code_db)
                    recommended_codes = rec
                    explanations.extend(exp)
                
                # Additional rule implementations would go here
                
            except Exception as e:
                logger.error(f"Error applying rule {rule.rule_id}: {e}")
        
        # Prepare the result
        result = {
            "status": "success",
            "procedure_text": procedure_text,
            "recommended_codes": recommended_codes,
            "excluded_codes": excluded_codes,
            "explanations": explanations
        }
        
        logger.info(f"Analysis complete. Recommended codes: {recommended_codes}")
        return result
    
    def get_rule_explanations(self) -> Dict[str, str]:
        """
        Get explanations for all rules.
        
        Returns:
            Dictionary mapping rule IDs to descriptions
        """
        return {rule.rule_id: rule.description for rule in self.rules}
    
    def get_coding_tips(self, code: str, procedure_text: str) -> List[str]:
        """
        Get coding tips for a specific CPT code based on the procedure description.
        
        Args:
            code: CPT code to get tips for
            procedure_text: Description of the procedure
            
        Returns:
            List of coding tips
        """
        tips = []
        
        # General tips
        tips.append("Ensure the documentation supports medical necessity.")
        tips.append("Check that the procedure description matches the code definition exactly.")
        
        # Specific tips based on procedure text
        if "consultation" in procedure_text.lower():
            tips.append("Initial consultations may require different codes than follow-up visits.")
        
        if "biopsy" in procedure_text.lower():
            tips.append("Verify if the biopsy was for diagnostic or therapeutic purposes.")
        
        if "endoscopic" in procedure_text.lower():
            tips.append("Endoscopic procedures often have specific bundling rules.")
        
        return tips