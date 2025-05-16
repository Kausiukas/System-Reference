import unittest
from faiss_query_cache import QueryResultCache
import time

class TestQueryResultCache(unittest.TestCase):
    def setUp(self):
        self.cache = QueryResultCache()
        self.query = ("vector1",)
        self.result = [1, 2, 3]

    def test_set_and_get(self):
        self.cache.set(self.query, self.result)
        self.assertEqual(self.cache.get(self.query), self.result)

    def test_cache_miss(self):
        self.assertIsNone(self.cache.get(("vector2",)))

    def test_invalidate(self):
        self.cache.set(self.query, self.result)
        self.cache.invalidate(self.query)
        self.assertIsNone(self.cache.get(self.query))

    def test_clear(self):
        self.cache.set(self.query, self.result)
        self.cache.clear()
        self.assertIsNone(self.cache.get(self.query))

    def test_ttl_expiration(self):
        cache = QueryResultCache(ttl_seconds=1)
        cache.set(self.query, self.result)
        self.assertEqual(cache.get(self.query), self.result)
        time.sleep(1.1)
        self.assertIsNone(cache.get(self.query))

if __name__ == "__main__":
    unittest.main() 