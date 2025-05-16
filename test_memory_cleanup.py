import unittest
from unittest.mock import MagicMock, patch
import memory_cleanup

class DummyCache:
    def __init__(self):
        self.cleared = False
    def clear(self):
        self.cleared = True

class TestMemoryCleanup(unittest.TestCase):
    @patch('memory_cleanup.psutil.Process')
    def test_cleanup_clears_caches_above_threshold(self, mock_process):
        # Simulate high memory usage
        mock_process.return_value.memory_info.return_value.rss = 200 * 1024 * 1024  # 200 MB
        cache = DummyCache()
        memory_cleanup.memory_cleanup(threshold_mb=100, caches=[cache])
        self.assertTrue(cache.cleared)

    @patch('memory_cleanup.psutil.Process')
    def test_cleanup_does_not_clear_caches_below_threshold(self, mock_process):
        # Simulate low memory usage
        mock_process.return_value.memory_info.return_value.rss = 50 * 1024 * 1024  # 50 MB
        cache = DummyCache()
        memory_cleanup.memory_cleanup(threshold_mb=100, caches=[cache])
        self.assertFalse(cache.cleared)

if __name__ == "__main__":
    unittest.main() 