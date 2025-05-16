import unittest
from embedding_cache import EmbeddingCache

class TestEmbeddingCache(unittest.TestCase):
    def setUp(self):
        self.cache = EmbeddingCache(max_size=2)

    def test_set_and_get(self):
        self.cache.set("text1", [0.1, 0.2])
        self.assertEqual(self.cache.get("text1"), [0.1, 0.2])

    def test_cache_miss(self):
        self.assertIsNone(self.cache.get("textX"))

    def test_lru_eviction(self):
        self.cache.set("text1", [0.1, 0.2])
        self.cache.set("text2", [0.3, 0.4])
        self.cache.get("text1")  # Access text1 to make it most recently used
        self.cache.set("text3", [0.5, 0.6])  # Should evict text2
        self.assertIsNone(self.cache.get("text2"))
        self.assertEqual(self.cache.get("text1"), [0.1, 0.2])
        self.assertEqual(self.cache.get("text3"), [0.5, 0.6])

    def test_clear(self):
        self.cache.set("text1", [0.1, 0.2])
        self.cache.clear()
        self.assertIsNone(self.cache.get("text1"))

if __name__ == "__main__":
    unittest.main() 