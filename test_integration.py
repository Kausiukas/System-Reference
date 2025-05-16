import sys
import os
import importlib.util
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil

# Load db.py from DATA/utils
utils_db_path = os.path.abspath('../DATA/utils/db.py')
spec = importlib.util.spec_from_file_location('db', utils_db_path)
db = importlib.util.module_from_spec(spec)
sys.modules['db'] = db
spec.loader.exec_module(db)
get_vector_db = db.get_vector_db
search_documents = db.search_documents

from app import (
    VECTOR_DB_PATH,
    DATA_DIR,
    initialize_session_state,
    process_user_input,
    display_chat_history,
    display_visualization
)

class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Create test directories
        self.test_data_dir = Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create test documents
        self.test_documents = [
            "Artificial Intelligence (AI) is the simulation of human intelligence by machines.",
            "Machine Learning is a subset of AI that focuses on training algorithms.",
            "Deep Learning uses neural networks with multiple layers.",
            "Natural Language Processing helps computers understand human language.",
            "Computer Vision enables machines to interpret visual information."
        ]
        
        self.test_metadata = [
            {"source": "ai_intro.txt", "date": "2024-01-01"},
            {"source": "ml_basics.txt", "date": "2024-01-02"},
            {"source": "deep_learning.txt", "date": "2024-01-03"},
            {"source": "nlp_overview.txt", "date": "2024-01-04"},
            {"source": "computer_vision.txt", "date": "2024-01-05"}
        ]
        
        # Initialize vector database with test data
        self.vector_db = get_vector_db()
        self.vector_db.add_documents(self.test_documents, self.test_metadata)

    def tearDown(self):
        """Clean up test environment after each test."""
        if hasattr(self, 'vector_db'):
            self.vector_db = None
        
        if self.test_data_dir.exists():
            try:
                shutil.rmtree(self.test_data_dir)
            except PermissionError:
                for file in self.test_data_dir.glob("*"):
                    try:
                        file.unlink()
                    except PermissionError:
                        pass
                try:
                    self.test_data_dir.rmdir()
                except:
                    pass

    @patch('streamlit.session_state')
    def test_real_database_search(self, mock_session_state):
        """Test search functionality with real vector database."""
        # Create a list to store chat history
        chat_history = []
        
        # Mock session state
        mock_session_state.__getitem__.side_effect = lambda key: {
            "chat_history": chat_history,
            "vector_db": self.vector_db
        }[key]
        
        # Test search with real database
        process_user_input("What is AI?", max_results=3)
        
        # Verify chat history was updated
        self.assertEqual(len(chat_history), 2)
        self.assertEqual(chat_history[0][0], "user")
        self.assertEqual(chat_history[1][0], "assistant")
        
        # Verify response contains relevant information
        response = chat_history[1][1]
        self.assertIn("AI", response)
        self.assertIn("artificial intelligence", response.lower())

    @patch('streamlit.session_state')
    def test_document_retrieval(self, mock_session_state):
        """Test document retrieval from vector database."""
        # Create a list to store chat history
        chat_history = []
        
        # Mock session state
        mock_session_state.__getitem__.side_effect = lambda key: {
            "chat_history": chat_history,
            "vector_db": self.vector_db
        }[key]
        
        # Test document retrieval
        process_user_input("Tell me about machine learning", max_results=2)
        
        # Verify response contains relevant documents
        response = chat_history[1][1]
        self.assertIn("Machine Learning", response)
        self.assertIn("training algorithms", response.lower())

    @patch('streamlit.session_state')
    def test_multiple_queries(self, mock_session_state):
        """Test multiple queries in sequence."""
        # Create a list to store chat history
        chat_history = []
        
        # Mock session state
        mock_session_state.__getitem__.side_effect = lambda key: {
            "chat_history": chat_history,
            "vector_db": self.vector_db
        }[key]
        
        # Test multiple queries
        queries = [
            "What is deep learning?",
            "How does NLP work?",
            "Explain computer vision"
        ]
        
        for query in queries:
            process_user_input(query, max_results=2)
        
        # Verify chat history contains all interactions
        self.assertEqual(len(chat_history), len(queries) * 2)
        
        # Verify each response is relevant to its query
        for i in range(0, len(chat_history), 2):
            query = chat_history[i][1]
            response = chat_history[i + 1][1]
            # Check for relevant content based on the query
            if "deep learning" in query.lower():
                self.assertIn("neural networks", response.lower())
            elif "nlp" in query.lower():
                self.assertIn("natural language", response.lower())
            elif "computer vision" in query.lower():
                self.assertIn("visual", response.lower())

    @patch('streamlit.session_state')
    def test_no_results_handling(self, mock_session_state):
        """Test handling of queries with no results."""
        # Create a list to store chat history
        chat_history = []
        
        # Mock session state
        mock_session_state.__getitem__.side_effect = lambda key: {
            "chat_history": chat_history,
            "vector_db": self.vector_db
        }[key]
        
        # Test query with no results
        process_user_input("completely unrelated query about quantum physics and string theory", max_results=2)
        
        # Verify appropriate response for no results
        response = chat_history[1][1]
        self.assertIn("couldn't find", response.lower())

if __name__ == '__main__':
    unittest.main() 