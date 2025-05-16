import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from datetime import datetime, timedelta
import sys
import os
import importlib.util
import logging

def close_log_handlers():
    for handler in logging.getLogger().handlers:
        handler.flush()
        if hasattr(handler, "close"):
            handler.close()

# Load db.py from DATA/utils
utils_db_path = os.path.abspath('../DATA/utils/db.py')
spec = importlib.util.spec_from_file_location('db', utils_db_path)
db = importlib.util.module_from_spec(spec)
sys.modules['db'] = db
spec.loader.exec_module(db)
get_main_vector_db = db.get_main_vector_db
get_local_vector_db = db.get_local_vector_db

from app import (
    check_vectorstore_health,
    check_openai_health,
    update_health_status,
    initialize_session_state
)

class TestConnectionStatus(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Mock session state
        self.mock_session_state = {
            "main_vector_db": MagicMock(),
            "local_vector_db": MagicMock(),
            "main_db_path": "D:/DATA/vectorstore",
            "local_db_path": "D:/GUI/vectorstore",
            "last_health_check": datetime.now(),
            "main_vectorstore_status": (False, "Not checked"),
            "local_vectorstore_status": (False, "Not checked"),
            "openai_status": (False, "Not checked")
        }
        
        # Mock vector_db search methods
        self.mock_session_state["main_vector_db"].search.return_value = [{"text": "test document"}]
        self.mock_session_state["local_vector_db"].search.return_value = [{"text": "test document"}]
        
        # Patch streamlit.session_state
        self.session_state_patcher = patch('streamlit.session_state', self.mock_session_state)
        self.session_state_patcher.start()
        # Remove log file if exists
        close_log_handlers()
        if os.path.exists("app.log"):
            os.remove("app.log")

    def tearDown(self):
        """Clean up after each test."""
        self.session_state_patcher.stop()
        close_log_handlers()
        if os.path.exists("app.log"):
            os.remove("app.log")

    def test_vectorstore_health_check(self):
        """Test vectorstore health check functionality."""
        # Test successful connection for main database
        is_healthy, message = check_vectorstore_health(
            self.mock_session_state["main_vector_db"],
            self.mock_session_state["main_db_path"]
        )
        self.assertTrue(is_healthy)
        self.assertIn("Connected to", message)
        self.assertIn("D:/DATA/vectorstore", message)
        
        # Test failed connection for main database
        # Remove 'count' so fallback to 'search' is used
        if hasattr(self.mock_session_state["main_vector_db"], "count"):
            delattr(self.mock_session_state["main_vector_db"], "count")
        # Also remove 'info' so fallback to 'search' is used
        if hasattr(self.mock_session_state["main_vector_db"], "info"):
            delattr(self.mock_session_state["main_vector_db"], "info")
        self.mock_session_state["main_vector_db"].search.side_effect = Exception("Connection error")
        is_healthy, message = check_vectorstore_health(
            self.mock_session_state["main_vector_db"],
            self.mock_session_state["main_db_path"]
        )
        self.assertFalse(is_healthy)
        self.assertIn("Error", message)
        
        # Test successful connection for local database
        is_healthy, message = check_vectorstore_health(
            self.mock_session_state["local_vector_db"],
            self.mock_session_state["local_db_path"]
        )
        self.assertTrue(is_healthy)
        self.assertIn("Connected to", message)
        self.assertIn("D:/GUI/vectorstore", message)

    def test_openai_health_check(self):
        """Test OpenAI health check functionality."""
        # Test when OpenAI is not configured
        with patch('app.OPENAI_ENABLED', False):
            is_healthy, message = check_openai_health()
            self.assertFalse(is_healthy)
            self.assertEqual(message, "OpenAI not configured")
        
        # Test when OpenAI is configured but fails
        with patch('app.OPENAI_ENABLED', True), \
             patch('app.generate_answer', side_effect=Exception("API error")):
            is_healthy, message = check_openai_health()
            self.assertFalse(is_healthy)
            self.assertIn("Error", message)

    def test_health_status_update(self):
        """Test health status update functionality."""
        # Patch OPENAI_ENABLED to False to ensure consistent results
        with patch('app.OPENAI_ENABLED', False):
            # Test update when interval has passed
            self.mock_session_state["last_health_check"] = datetime.now() - timedelta(seconds=31)
            update_health_status()
            
            # Verify status was updated for both databases
            self.assertEqual(self.mock_session_state["main_vectorstore_status"][0], True)
            self.assertEqual(self.mock_session_state["local_vectorstore_status"][0], True)
            self.assertEqual(self.mock_session_state["openai_status"], (False, "OpenAI not configured"))
            
            # Test no update when interval hasn't passed
            self.mock_session_state["last_health_check"] = datetime.now()
            update_health_status()
            # Status should remain unchanged
            self.assertEqual(self.mock_session_state["main_vectorstore_status"][0], True)
            self.assertEqual(self.mock_session_state["local_vectorstore_status"][0], True)
            self.assertEqual(self.mock_session_state["openai_status"], (False, "OpenAI not configured"))

    def test_session_state_initialization(self):
        """Test session state initialization with connection status."""
        # Clear session state
        self.mock_session_state.clear()
        with patch('app.get_main_vector_db', return_value=(MagicMock(), "D:/DATA/vectorstore")), \
             patch('app.get_local_vector_db', return_value=(MagicMock(), "D:/GUI/vectorstore")):
            # Test initialization
            initialize_session_state()
            # Verify all required state variables were set
            self.assertIn("chat_history", self.mock_session_state)
            self.assertIn("main_vectorstore_status", self.mock_session_state)
            self.assertIn("local_vectorstore_status", self.mock_session_state)
            self.assertIn("openai_status", self.mock_session_state)
            self.assertEqual(self.mock_session_state["chat_history"], [])
            self.assertEqual(self.mock_session_state["main_vectorstore_status"], (False, "Not checked"))
            self.assertEqual(self.mock_session_state["local_vectorstore_status"], (False, "Not checked"))
            self.assertEqual(self.mock_session_state["openai_status"], (False, "Not checked"))

    def test_vectorstore_health_check_minimal_handshake(self):
        """Test vectorstore health check uses minimal handshake and logs appropriately."""
        # Only 'count' method should be called
        self.mock_session_state["main_vector_db"].count.return_value = 42
        is_healthy, message = check_vectorstore_health(
            self.mock_session_state["main_vector_db"],
            self.mock_session_state["main_db_path"]
        )
        self.assertTrue(is_healthy)
        self.assertIn("Connected to", message)
        self.mock_session_state["main_vector_db"].count.assert_called_once()
        # Check log file
        with open("app.log", "r") as f:
            log_content = f.read()
        self.assertIn("responded to count", log_content)

    def test_vectorstore_health_check_fallback_search(self):
        """Test vectorstore health check falls back to minimal search and logs."""
        # No 'count' or 'info', fallback to search
        del self.mock_session_state["main_vector_db"].count
        del self.mock_session_state["main_vector_db"].info
        self.mock_session_state["main_vector_db"].search.return_value = ["doc1"]
        is_healthy, message = check_vectorstore_health(
            self.mock_session_state["main_vector_db"],
            self.mock_session_state["main_db_path"]
        )
        self.assertTrue(is_healthy)
        self.mock_session_state["main_vector_db"].search.assert_called_once_with("test", k=1)
        with open("app.log", "r") as f:
            log_content = f.read()
        self.assertIn("responded to minimal search", log_content)

    def test_vectorstore_health_check_error_logging(self):
        """Test vectorstore health check logs errors."""
        self.mock_session_state["main_vector_db"].count.side_effect = Exception("fail")
        is_healthy, message = check_vectorstore_health(
            self.mock_session_state["main_vector_db"],
            self.mock_session_state["main_db_path"]
        )
        self.assertFalse(is_healthy)
        self.assertIn("Error at", message)
        with open("app.log", "r") as f:
            log_content = f.read()
        self.assertIn("health check failed", log_content)

    def test_logging_on_app_startup(self):
        """Test that app startup and main are logged."""
        # Import app again to trigger logging
        import importlib
        import app as app_module
        importlib.reload(app_module)
        with open("app.log", "r") as f:
            log_content = f.read()
        self.assertIn("App startup initiated", log_content)
        # Do not check for 'App main() started' since main() is not called on import

if __name__ == '__main__':
    unittest.main() 