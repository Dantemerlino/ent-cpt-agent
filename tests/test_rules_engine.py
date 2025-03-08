import os
import sys
import unittest
from unittest.mock import Mock, MagicMock
import logging

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the classes to test
from src.agent.rules_engine import RulesEngine, CodeRule

# Disable logging output during tests
logging.disable(logging.CRITICAL)

class TestRulesEngine(unittest.TestCase):
    """
    Unit tests for the RulesEngine class.
    
    These tests validate the rule application logic and code recommendations.
    """
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a RulesEngine instance
        self.rules_engine = RulesEngine()
        
        # Create a mock CPT database
        self.mock_cpt_db = MagicMock()
        
        # Set up mock code details responses
        self.mock_cpt_db.get_code_details.side_effect = self._mock_get_code_details
    
    def _mock_get_code_details(self, code):
        """Mock implementation of get_code_details."""
        # Define some test code details
        code_details = {
            '31231': {
                'code': '31231',
                'description': 'Nasal endoscopy, diagnostic',
                'related_codes': ['31233', '31235']
            },
            '31233': {
                'code': '31233',
                'description': 'Nasal endoscopy with biopsy',
                'related_codes': ['31231']
            },
            '69436': {
                'code': '69436',
                'description': 'Tympanostomy with tubes, bilateral',
                'related_codes': ['69433']
            },
            '30520': {
                'code': '30520',
                'description': 'Septoplasty',
                'related_codes': ['30930']
            }
        }
        
        if code in code_details:
            return code_details[code]
        else:
            return {"error": f"CPT code {code} not found"}
    
    def test_initialize_rules(self):
        """Test that default rules are properly initialized."""
        # Check that rules were loaded
        self.assertGreater(len(self.rules_engine.rules), 0)
        
        # Check that rules are sorted by priority
        priorities = [rule.priority for rule in self.rules_engine.rules]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        
        # Check that specific rules exist
        rule_ids = [rule.rule_id for rule in self.rules_engine.rules]
        self.assertIn("R001", rule_ids)  # Bundled procedures
        self.assertIn("R002", rule_ids)  # Bilateral procedures
    
    def test_add_rule(self):
        """Test adding a custom rule."""
        # Initial rule count
        initial_count = len(self.rules_engine.rules)
        
        # Add a new rule
        new_rule = CodeRule(
            rule_id="TEST001",
            description="Test rule",
            conditions=[{"type": "test"}],
            priority=100
        )
        self.rules_engine.add_rule(new_rule)
        
        # Check rule was added
        self.assertEqual(len(self.rules_engine.rules), initial_count + 1)
        
        # Check rule is first (highest priority)
        self.assertEqual(self.rules_engine.rules[0].rule_id, "TEST001")
    
    def test_evaluate_bundled_codes(self):
        """Test evaluation of bundled codes."""
        # Test case: two potentially bundled codes
        candidate_codes = ['31231']
        procedure_text = "Diagnostic nasal endoscopy"
        
        recommended, excluded, explanations = self.rules_engine.evaluate_bundled_codes(
            procedure_text, candidate_codes, self.mock_cpt_db
        )
        
        # No bundled codes in this case - just a single code
        self.assertEqual(len(recommended), 1)
        self.assertEqual(len(excluded), 0)
        self.assertEqual(len(explanations), 0)
    
    def test_evaluate_bilateral_procedures(self):
        """Test evaluation of bilateral procedures."""
        # Test case: bilateral procedure
        candidate_codes = ['30520']
        procedure_text = "Bilateral septoplasty"
        
        modified_codes, explanations = self.rules_engine.evaluate_bilateral_procedures(
            procedure_text, candidate_codes, self.mock_cpt_db
        )
        
        # Should add modifier 50 to the code
        self.assertEqual(len(modified_codes), 1)
        self.assertEqual(modified_codes[0], "30520-50")
        self.assertEqual(len(explanations), 1)
        
        # Test case: non-bilateral procedure
        candidate_codes = ['30520']
        procedure_text = "Septoplasty"
        
        modified_codes, explanations = self.rules_engine.evaluate_bilateral_procedures(
            procedure_text, candidate_codes, self.mock_cpt_db
        )
        
        # Should not modify the code
        self.assertEqual(len(modified_codes), 1)
        self.assertEqual(modified_codes[0], "30520")
        self.assertEqual(len(explanations), 0)
    
    def test_analyze_procedure(self):
        """Test the main analyze_procedure method."""
        # Test case: bilateral procedure with potential bundling
        procedure_text = "Bilateral nasal endoscopy with biopsy"
        candidate_codes = ['31231', '31233']
        
        result = self.rules_engine.analyze_procedure(
            procedure_text, candidate_codes, self.mock_cpt_db
        )
        
        # Check overall result structure
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["procedure_text"], procedure_text)
        self.assertIn("recommended_codes", result)
        self.assertIn("excluded_codes", result)
        self.assertIn("explanations", result)
        
        # Check that at least one recommended code has modifier 50
        has_bilateral_code = any("-50" in code for code in result["recommended_codes"])
        self.assertTrue(has_bilateral_code)
    
    def test_analyze_procedure_no_candidates(self):
        """Test analyze_procedure with no candidate codes."""
        procedure_text = "Some procedure description"
        candidate_codes = []
        
        result = self.rules_engine.analyze_procedure(
            procedure_text, candidate_codes, self.mock_cpt_db
        )
        
        # Should return an error
        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)
        self.assertEqual(result["recommended_codes"], [])
    
    def test_get_coding_tips(self):
        """Test retrieving coding tips for a code."""
        # Test case: endoscopic procedure
        tips = self.rules_engine.get_coding_tips(
            '31231', 'Nasal endoscopy, diagnostic, endoscopic procedure'
        )
        
        # Should return a list of tips
        self.assertIsInstance(tips, list)
        self.assertGreater(len(tips), 0)
        
        # Should include endoscopy-specific tips
        has_endoscopy_tip = any("endoscopic" in tip.lower() for tip in tips)
        self.assertTrue(has_endoscopy_tip)
        
        # All procedures should have general tips
        has_general_tips = any("medical necessity" in tip.lower() for tip in tips)
        self.assertTrue(has_general_tips)


if __name__ == '__main__':
    unittest.main()