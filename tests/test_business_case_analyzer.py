import unittest
import os
from pathlib import Path
from business_case_agent import BusinessCaseAgent

class TestBusinessCaseAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.agent = BusinessCaseAgent()
        self.test_doc_path = Path("test_documents/lithuania_economic_issue.txt")
        
    def test_document_loading(self):
        """Test if the document can be loaded correctly."""
        content = self.agent.load_document(str(self.test_doc_path))
        self.assertIsNotNone(content)
        self.assertIsInstance(content, str)
        self.assertTrue(len(content) > 0)
        
    def test_language_detection(self):
        """Test if the language detection works correctly for Lithuanian text."""
        content = self.agent.load_document(str(self.test_doc_path))
        self.assertEqual(self.agent.last_loaded_language, 'lt')
        
    def test_analysis_steps(self):
        """Test if all analysis steps are performed correctly."""
        results = self.agent.build_case(str(self.test_doc_path))
        
        # Check if all required analysis steps are present
        required_steps = [
            'summarize_document',
            'identify_parties',
            'describe_situation',
            'describe_problem',
            'recommend_solution'
        ]
        
        analysis = results['analysis']
        if 'english' in analysis:
            analysis = analysis['english']
        for step in required_steps:
            self.assertIn(step, analysis)
            
    def test_checklist_generation(self):
        """Test if checklist is generated with correct structure."""
        results = self.agent.build_case(str(self.test_doc_path))
        checklist = results['checklist']
        
        # Check if checklist items have required structure
        for item in checklist:
            self.assertIn('main_task', item)
            self.assertIn('priority', item)
            self.assertIn('dependencies', item)
            self.assertIn('subtasks', item)
            
            # Check if main_task has description
            self.assertIsNotNone(item['main_task'].description)
            
            # Check if subtasks are properly structured
            for subtask in item['subtasks']:
                self.assertIsNotNone(subtask.description)
                self.assertIsNotNone(subtask.priority)
                
    def test_translation_capability(self):
        """Test if the analyzer can handle translation to English."""
        results = self.agent.build_case(
            str(self.test_doc_path),
            input_language='lt',
            output_language='en'
        )
        
        # Check if both original and translated content are present
        self.assertIn('analysis', results)
        self.assertIn('english', results['analysis'])
        self.assertIn('translated', results['analysis'])
        
    def test_priority_evaluation(self):
        """Test if priorities are correctly evaluated for tasks."""
        results = self.agent.build_case(str(self.test_doc_path))
        checklist = results['checklist']
        
        for item in checklist:
            self.assertIn(item['priority'].lower(), ['high', 'medium', 'low'])
            
    def test_performance_metrics(self):
        """Test if performance metrics are being tracked."""
        results = self.agent.build_case(str(self.test_doc_path))
        report = self.agent.get_performance_report()
        
        self.assertIn('analysis_performance', report)
        self.assertIn('resource_usage', report)
        self.assertIn('quality_metrics', report)
        
    def test_error_handling(self):
        """Test if the analyzer handles errors gracefully."""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            self.agent.build_case("non_existent_file.txt")
            
        # Test with empty file
        empty_file = Path("test_documents/empty.txt")
        empty_file.touch()
        try:
            with self.assertRaises(Exception):
                self.agent.build_case(str(empty_file))
        finally:
            empty_file.unlink()
            
    def test_context_enrichment(self):
        """Test if context enrichment works correctly."""
        content = self.agent.load_document(str(self.test_doc_path))
        context = self.agent.enrich_with_vectorstore("energy transition Lithuania")
        
        self.assertIsNotNone(context)
        self.assertIsInstance(context, str)
        self.assertTrue(len(context) > 0)

if __name__ == '__main__':
    unittest.main() 