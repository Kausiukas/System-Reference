import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from datetime import datetime
import imaplib
import email
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.components.email_watcher import EmailWatcher, GmailWatcher, OutlookWatcher

class TestEmailWatcherImpl(EmailWatcher):
    """Concrete implementation of EmailWatcher for testing."""
    def connect(self) -> bool:
        """Test implementation of connect."""
        return True
        
    def disconnect(self):
        """Test implementation of disconnect."""
        pass
        
    def save_attachment(self, part, email_id: str, part_num: int) -> str:
        """Test implementation of save_attachment."""
        filename = part.get_filename()
        if filename:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(part.get_payload(decode=True))
            return file_path
        return None
        
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Test implementation of cleanup_temp_files."""
        for file_path in Path(self.temp_dir).glob('*'):
            if file_path.is_file():
                file_path.unlink()

class TestEmailWatcher(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.watcher = TestEmailWatcherImpl(
            imap_server="test.server.com",
            email_address="test@example.com",
            password="test_password",
            temp_dir=self.temp_dir
        )
        
    def tearDown(self):
        """Clean up test environment."""
        for file in Path(self.temp_dir).glob('*'):
            file.unlink()
        Path(self.temp_dir).rmdir()
        
    def test_connect(self):
        """Test connection."""
        self.assertTrue(self.watcher.connect())
        
    def test_check_new_emails(self):
        """Test checking new emails."""
        # Mock IMAP connection
        mock_imap = MagicMock()
        mock_imap.search.return_value = (None, [b'1'])
        mock_imap.fetch.return_value = (None, [(b'1', b'test email')])
        
        self.watcher.imap = mock_imap
        self.watcher.check_new_emails()
        
        mock_imap.select.assert_called_once_with('INBOX')
        mock_imap.search.assert_called_once_with(None, 'UNSEEN')
        
    def test_save_attachment(self):
        """Test saving attachments."""
        # Create test email part
        part = MagicMock()
        part.get_content_maintype.return_value = 'application'
        part.get_filename.return_value = 'test.txt'
        part.get_payload.return_value = b'test content'
        
        # Save attachment
        saved_path = self.watcher.save_attachment(part, '1', 1)
        
        # Verify file was saved
        self.assertTrue(Path(saved_path).exists())
        with open(saved_path, 'r') as f:
            self.assertEqual(f.read(), 'test content')
            
    def test_cleanup_temp_files(self):
        """Test cleaning up temporary files."""
        # Create test files
        test_files = []
        for i in range(3):
            path = Path(self.temp_dir) / f"test_{i}.txt"
            path.write_text("test content")
            test_files.append(path)
            
        # Clean up files
        self.watcher.cleanup_temp_files(max_age_hours=0)
        
        # Verify files were deleted
        for path in test_files:
            self.assertFalse(path.exists())

class TestGmailWatcher(unittest.TestCase):
    def test_initialization(self):
        """Test Gmail watcher initialization."""
        watcher = GmailWatcher(
            email_address="test@gmail.com",
            app_password="test_password"
        )
        self.assertEqual(watcher.imap_server, "imap.gmail.com")
        self.assertEqual(watcher.email_address, "test@gmail.com")

class TestOutlookWatcher(unittest.TestCase):
    def test_initialization(self):
        """Test Outlook watcher initialization."""
        watcher = OutlookWatcher(
            email_address="test@outlook.com",
            password="test_password"
        )
        self.assertEqual(watcher.imap_server, "outlook.office365.com")
        self.assertEqual(watcher.email_address, "test@outlook.com")

if __name__ == '__main__':
    unittest.main() 