import sys
import os
import importlib.util
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
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

class TestApp(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Create test directories
        self.test_data_dir = Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create test chat history
        self.test_history = [
            ("user", "What is AI?"),
            ("assistant", "AI is artificial intelligence.")
        ]
        
        # Save test history
        with open(self.test_data_dir / "chat_history.json", 'w') as f:
            json.dump(self.test_history, f)

        self.vector_db = get_vector_db()

    def tearDown(self):
        """Clean up test environment after each test."""
        if self.test_data_dir.exists():
            try:
                shutil.rmtree(self.test_data_dir)
            except PermissionError:
                # If files are still in use, try to remove them individually
                for file in self.test_data_dir.glob("*"):
                    try:
                        file.unlink()
                    except PermissionError:
                        pass
                try:
                    self.test_data_dir.rmdir()
                except:
                    pass
        self.vector_db = None

    @patch('streamlit.session_state')
    def test_initialize_session_state(self, mock_session_state):
        """Test session state initialization."""
        # Mock session state
        mock_session_state.__getitem__.side_effect = KeyError()
        
        # Test initialization
        initialize_session_state()
        
        # Verify session state was accessed with dictionary-style access
        mock_session_state.__setitem__.assert_any_call('chat_history', [])
        # Check that vector_db is set to an instance of AutoVectorDB
        args_list = [call[0][1] for call in mock_session_state.__setitem__.call_args_list if call[0][0] == 'vector_db']
        self.assertTrue(any(isinstance(arg, AutoVectorDB) for arg in args_list))

    def test_process_user_input(self):
        """Test user input processing."""
        # Create a list to store chat history
        chat_history = []
        
        # Mock session state
        mock_session_state = MagicMock()
        mock_session_state.__getitem__.side_effect = lambda key: {
            "chat_history": chat_history,
            "vector_db": self.vector_db
        }[key]
        
        # Test input processing
        with patch('streamlit.session_state', mock_session_state):
            process_user_input("Test query", max_results=5)
            
            # Verify chat history was updated
            self.assertEqual(len(chat_history), 2)
            self.assertEqual(chat_history[0][0], "user")
            self.assertEqual(chat_history[1][0], "assistant")

    def test_file_upload(self):
        """Test file upload functionality."""
        # Create a test file
        test_file_path = self.test_data_dir / "test.txt"
        with open(test_file_path, 'w') as f:
            f.write("This is a test document.")
        
        # Test file reading
        with open(test_file_path, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "This is a test document.")

    def test_chat_history_format(self):
        """Test chat history format."""
        # Test message format
        for role, message in self.test_history:
            self.assertIn(role, ["user", "assistant"])
            self.assertIsInstance(message, str)

    def test_vector_db_path(self):
        """Test vector database path configuration."""
        self.assertTrue(isinstance(VECTOR_DB_PATH, str))
        self.assertTrue(isinstance(DATA_DIR, Path))

    @patch('streamlit.file_uploader')
    def test_file_uploader(self, mock_file_uploader):
        """Test file uploader functionality."""
        # Mock file uploader
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"This is a test document."
        mock_file_uploader.return_value = mock_file
        
        # Test file uploader
        uploaded_file = mock_file_uploader("Upload a text file", type=['txt'])
        self.assertIsNotNone(uploaded_file)
        self.assertEqual(uploaded_file.getvalue(), b"This is a test document.")

if __name__ == '__main__':
    unittest.main() 