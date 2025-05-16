import unittest
from unittest.mock import Mock, patch
import psutil
from vectorstore_health import VectorStoreHealth, create_health_checker

class TestVectorStoreHealth(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.health_checker = VectorStoreHealth(self.mock_client, memory_threshold_mb=100)
        
        # Mock collection
        self.mock_collection = Mock()
        self.mock_collection.get_stats.return_value = {'dimension': 384}
        self.mock_collection.count.return_value = 100
        self.mock_collection.peek.return_value = {'documents': ['sample doc']}
        
        # Mock client methods
        self.mock_client.get_collection.return_value = self.mock_collection
        self.mock_client.list_collections.return_value = [
            Mock(name='test_collection')
        ]

    @patch('psutil.Process')
    def test_memory_usage(self, mock_process):
        """Test memory usage monitoring."""
        # Mock memory usage
        mock_process.return_value.memory_info.return_value.rss = 50 * 1024 * 1024  # 50MB
        
        # Test memory usage check
        memory_usage = self.health_checker.get_memory_usage()
        self.assertEqual(memory_usage, 50 * 1024 * 1024)
        
        # Test threshold check
        is_below_threshold = self.health_checker.check_memory_threshold()
        self.assertTrue(is_below_threshold)

    def test_collection_stats(self):
        """Test collection statistics retrieval."""
        stats = self.health_checker.get_collection_stats('test_collection')
        
        self.assertEqual(stats['name'], 'test_collection')
        self.assertEqual(stats['document_count'], 100)
        self.assertEqual(stats['dimension'], 384)
        self.assertEqual(stats['status'], 'healthy')

    def test_collection_health(self):
        """Test comprehensive collection health check."""
        health = self.health_checker.check_collection_health('test_collection')
        
        self.assertEqual(health['name'], 'test_collection')
        self.assertTrue(health['memory_ok'])
        self.assertTrue(health['sample_accessible'])
        self.assertIn('timestamp', health)

    def test_all_collections_health(self):
        """Test health check for all collections."""
        health = self.health_checker.get_all_collections_health()
        
        self.assertEqual(health['total_collections'], 1)
        self.assertIn('test_collection', health['collections'])
        self.assertIn('memory_usage', health)
        self.assertIn('memory_ok', health)
        self.assertIn('timestamp', health)

    def test_error_handling(self):
        """Test error handling in health checks."""
        # Simulate error in collection access
        self.mock_client.get_collection.side_effect = Exception("Test error")
        
        health = self.health_checker.check_collection_health('test_collection')
        self.assertEqual(health['status'], 'error')
        self.assertIn('error', health)

    def test_health_checker_creation(self):
        """Test creation of health checker with custom settings."""
        with patch('chromadb.Client') as mock_client:
            health_checker = create_health_checker(
                persist_directory='/test/path',
                memory_threshold_mb=2000
            )
            
            # Verify client was created with correct settings
            mock_client.assert_called_once()
            args, kwargs = mock_client.call_args
            self.assertEqual(kwargs['persist_directory'], '/test/path')
            self.assertEqual(
                kwargs['settings'].chroma_memory_limit_bytes,
                2000 * 1024 * 1024
            )

if __name__ == '__main__':
    unittest.main() 