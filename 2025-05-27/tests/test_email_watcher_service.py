import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import signal
from pathlib import Path
import sys
import platform

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.email_watcher_service import EmailWatcherService
from src.components.email_watcher import GmailWatcher, OutlookWatcher

class TestEmailWatcherService(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['GMAIL_ADDRESS'] = 'test@gmail.com'
        os.environ['GMAIL_APP_PASSWORD'] = 'test_password'
        os.environ['OUTLOOK_ADDRESS'] = 'test@outlook.com'
        os.environ['OUTLOOK_PASSWORD'] = 'test_password'
        
        # Create test directories
        os.makedirs(os.path.join(self.temp_dir, 'logs'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'data/temp_emails'), exist_ok=True)
        
        # Initialize service
        self.service = EmailWatcherService()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
        # Clean up environment variables
        del os.environ['GMAIL_ADDRESS']
        del os.environ['GMAIL_APP_PASSWORD']
        del os.environ['OUTLOOK_ADDRESS']
        del os.environ['OUTLOOK_PASSWORD']
        
    def test_initialization(self):
        """Test service initialization."""
        self.assertTrue(hasattr(self.service, 'watchers'))
        self.assertTrue(hasattr(self.service, 'running'))
        self.assertTrue(self.service.running)
        
    def test_add_gmail_watcher(self):
        """Test adding Gmail watcher."""
        self.service.add_gmail_watcher(
            email="test@gmail.com",
            app_password="test_password"
        )
        
        self.assertEqual(len(self.service.watchers), 1)
        self.assertIsInstance(self.service.watchers[0], GmailWatcher)
        
    def test_add_outlook_watcher(self):
        """Test adding Outlook watcher."""
        self.service.add_outlook_watcher(
            email="test@outlook.com",
            password="test_password"
        )
        
        self.assertEqual(len(self.service.watchers), 1)
        self.assertIsInstance(self.service.watchers[0], OutlookWatcher)
        
    @patch('src.components.nodes.build_graph')
    def test_process_files(self, mock_build_graph):
        """Test file processing."""
        # Create mock workflow
        mock_workflow = Mock()
        mock_workflow.invoke.return_value = Mock()
        mock_build_graph.return_value = mock_workflow
        
        # Create test files
        test_files = []
        for i in range(3):
            path = os.path.join(self.temp_dir, f"test_file_{i}.txt")
            with open(path, 'w') as f:
                f.write(f"Test content {i}")
            test_files.append(path)
            
        # Process files
        self.service.process_files(test_files)
        
        # Verify workflow was called for each file
        self.assertEqual(mock_workflow.invoke.call_count, 3)
        
        # Verify files were cleaned up
        for path in test_files:
            self.assertFalse(os.path.exists(path))
            
    def test_handle_shutdown(self):
        """Test shutdown handler."""
        # Add a mock watcher
        mock_watcher = Mock()
        self.service.watchers.append(mock_watcher)
        
        # Send shutdown signal
        self.service.handle_shutdown(signal.SIGTERM, None)
        
        # Verify service is stopped
        self.assertFalse(self.service.running)
        mock_watcher.stop.assert_called_once()
        
    @patch('src.components.email_watcher.EmailWatcher.start_watching')
    def test_run(self, mock_start_watching):
        """Test service run method."""
        # Add test watchers
        self.service.add_gmail_watcher(
            email="test@gmail.com",
            app_password="test_password"
        )
        self.service.add_outlook_watcher(
            email="test@outlook.com",
            password="test_password"
        )
        
        # Mock the running loop to exit immediately
        def stop_service():
            self.service.running = False
            
        mock_start_watching.side_effect = stop_service
        
        # Run service
        self.service.run()
        
        # Verify watchers were started
        self.assertEqual(mock_start_watching.call_count, 1)
        
    @unittest.skipIf(platform.system() == 'Windows', "Daemon tests not supported on Windows")
    @patch('daemon.DaemonContext')
    def test_run_as_daemon(self, mock_daemon):
        """Test running service as daemon (Unix-like systems only)."""
        from src.services.email_watcher_service import run_service
        
        # Run service as daemon
        run_service("test.pid", self.temp_dir)
        
        # Verify daemon context was created
        mock_daemon.assert_called_once()
        
class TestMainFunction(unittest.TestCase):
    @unittest.skipIf(platform.system() == 'Windows', "Daemon tests not supported on Windows")
    @patch('src.services.email_watcher_service.run_service')
    @patch('src.services.email_watcher_service.EmailWatcherService')
    def test_main_daemon(self, mock_service_class, mock_run_service):
        """Test main function in daemon mode (Unix-like systems only)."""
        from src.services.email_watcher_service import main
        import sys
        
        # Mock command line arguments
        sys.argv = ['email_watcher_service.py', '--daemon']
        
        # Run main
        main()
        
        # Verify daemon service was started
        mock_run_service.assert_called_once()
        mock_service_class.assert_not_called()
        
    @patch('src.services.email_watcher_service.run_service')
    @patch('src.services.email_watcher_service.EmailWatcherService')
    def test_main_normal(self, mock_service_class, mock_run_service):
        """Test main function in normal mode."""
        from src.services.email_watcher_service import main
        import sys
        
        # Mock command line arguments
        sys.argv = ['email_watcher_service.py']
        
        # Run main
        main()
        
        # Verify normal service was started
        mock_run_service.assert_called_once_with()

if __name__ == '__main__':
    unittest.main() 