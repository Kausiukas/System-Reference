import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from test_email_watcher import TestEmailWatcher, TestGmailWatcher, TestOutlookWatcher
from test_email_watcher_service import TestEmailWatcherService, TestMainFunction

def run_tests():
    """Run all test cases."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEmailWatcher))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGmailWatcher))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestOutlookWatcher))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEmailWatcherService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMainFunction))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 