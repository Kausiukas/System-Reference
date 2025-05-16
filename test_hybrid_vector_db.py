import unittest
from unittest.mock import Mock, patch, MagicMock
from hybrid_vector_db import HybridVectorDB
from pathlib import Path
import shutil
import os

class TestHybridVectorDB(unittest.TestCase):
    def setUp(self):
        # Set up test directories
        self.test_cache_path = Path("test_cache")
        self.test_full_db_path = Path("test_full_db")
        
        # Clean up any existing test directories
        shutil.rmtree(self.test_cache_path, ignore_errors=True)
        shutil.rmtree(self.test_full_db_path, ignore_errors=True)
        
        # Create test directories
        self.test_cache_path.mkdir(parents=True, exist_ok=True)
        self.test_full_db_path.mkdir(parents=True, exist_ok=True)
        
        # Mock metrics tracker
        self.metrics_patcher = patch('hybrid_vector_db.get_metrics_tracker')
        self.mock_metrics = self.metrics_patcher.start()
        self.mock_metrics_instance = MagicMock()
        self.mock_metrics.return_value = self.mock_metrics_instance
        
        # Create test instance
        self.db = HybridVectorDB(
            cache_path=str(self.test_cache_path),
            full_db_path=str(self.test_full_db_path),
            cache_size=3  # Small cache size for testing
        )
    
    def tearDown(self):
        # Clean up test directories
        shutil.rmtree(self.test_cache_path, ignore_errors=True)
        shutil.rmtree(self.test_full_db_path, ignore_errors=True)
        self.metrics_patcher.stop()
    
    def test_initialization(self):
        """Test that the hybrid database initializes correctly."""
        self.assertIsNotNone(self.db.cache_db)
        self.assertIsNotNone(self.db.full_db)
        self.assertEqual(self.db.cache_size, 3)
        self.assertEqual(self.db.cache_hits, 0)
        self.assertEqual(self.db.cache_misses, 0)
    
    def test_add_documents(self):
        """Test adding documents to both tiers."""
        texts = ["test document 1", "test document 2"]
        metadata = [{"source": "test1"}, {"source": "test2"}]
        
        self.db.add_documents(texts, metadata)
        
        # Verify documents were added to both tiers
        cache_stats = self.db.cache_db.get_stats()
        full_stats = self.db.full_db.get_stats()
        
        self.assertEqual(cache_stats['total_documents'], 2)
        self.assertEqual(full_stats['total_documents'], 2)
    
    def test_cache_size_limit(self):
        """Test that cache size limit is respected."""
        # Add more documents than cache size
        texts = ["doc1", "doc2", "doc3", "doc4"]
        metadata = [{"id": i} for i in range(4)]
        
        self.db.add_documents(texts, metadata)
        
        # Verify cache size is not exceeded
        cache_stats = self.db.cache_db.get_stats()
        self.assertLessEqual(cache_stats['total_documents'], self.db.cache_size)
    
    def test_search_cache_hit(self):
        """Test search with cache hit."""
        # Mock both search methods to avoid actual file operations
        self.db.cache_db.search = Mock(return_value=[{
            'text': 'test query document',
            'metadata': {'id': 1},
            'score': 0.9  # High score to trigger cache hit
        }])
        self.db.full_db.search = Mock(return_value=[{
            'text': 'test query document',
            'metadata': {'id': 1},
            'score': 0.8
        }])
        
        # Perform search
        results = self.db.search("test query", cache_threshold=0.7)
        
        # Verify cache hit was recorded
        self.assertEqual(self.db.cache_hits, 1)
        self.assertEqual(self.db.cache_misses, 0)
        self.mock_metrics_instance.track_cache_hit.assert_called_once()
    
    def test_search_cache_miss(self):
        """Test search with cache miss."""
        # Add a document to both tiers
        self.db.add_documents(["test query document"], [{"id": 1}])
        
        # Mock cache search to return low score
        self.db.cache_db.search = Mock(return_value=[{
            'text': 'test query document',
            'metadata': {'id': 1},
            'score': 0.5  # Low score to trigger cache miss
        }])
        
        # Mock full search
        self.db.full_db.search = Mock(return_value=[{
            'text': 'test query document',
            'metadata': {'id': 1},
            'score': 0.8
        }])
        
        # Perform search
        results = self.db.search("test query", cache_threshold=0.7)
        
        # Verify cache miss was recorded
        self.assertEqual(self.db.cache_hits, 0)
        self.assertEqual(self.db.cache_misses, 1)
        self.mock_metrics_instance.track_cache_miss.assert_called_once()
    
    def test_get_stats(self):
        """Test getting database statistics."""
        # Add some documents
        self.db.add_documents(["doc1", "doc2"], [{"id": 1}, {"id": 2}])
        
        # Perform some searches
        self.db.cache_hits = 2
        self.db.cache_misses = 1
        
        # Get stats
        stats = self.db.get_stats()
        
        # Verify stats structure
        self.assertIn('cache', stats)
        self.assertIn('full_db', stats)
        self.assertIn('performance', stats)
        self.assertEqual(stats['performance']['cache_hits'], 2)
        self.assertEqual(stats['performance']['cache_misses'], 1)
        self.assertEqual(stats['performance']['hit_rate'], "66.7%")
    
    def test_rebuild_cache(self):
        """Test cache rebuilding."""
        # Add documents
        texts = ["doc1", "doc2", "doc3"]
        metadata = [{"id": i} for i in range(3)]
        self.db.add_documents(texts, metadata)
        
        # Rebuild cache with new documents
        new_texts = ["new1", "new2"]
        new_metadata = [{"id": "new1"}, {"id": "new2"}]
        self.db.rebuild_cache(new_texts, new_metadata)
        
        # Verify cache was rebuilt
        cache_stats = self.db.cache_db.get_stats()
        self.assertEqual(cache_stats['total_documents'], 2)

    def test_schedule_cache_rebuild(self):
        """Test scheduling cache rebuild."""
        with self.assertLogs(level='INFO') as log:
            self.db.schedule_cache_rebuild(interval_hours=12)
            self.assertIn("Cache rebuild scheduled every 12 hours", log.output[0])

    def test_check_cache_freshness(self):
        """Test cache freshness check."""
        with self.assertLogs(level='INFO') as log:
            result = self.db.check_cache_freshness()
            self.assertTrue(result)
            self.assertIn("Cache freshness check performed", log.output[0])

    def test_trigger_cache_update(self):
        """Test triggering cache update."""
        with self.assertLogs(level='INFO') as log:
            self.db.trigger_cache_update()
            self.assertIn("Cache update triggered", log.output[0])

if __name__ == '__main__':
    unittest.main() 