from typing import Any, Tuple
import time
from collections import OrderedDict
from logging_utils import get_logger
from metrics_tracker import get_metrics_tracker
try:
    import psutil
except ImportError:
    psutil = None

# Configure logging
logger = get_logger(__name__)

class QueryResultCache:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = None):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def get(self, query: Tuple) -> Any:
        metrics = get_metrics_tracker()
        entry = self.cache.get(query)
        if entry:
            value, timestamp = entry
            if self.ttl_seconds is not None and (time.time() - timestamp > self.ttl_seconds):
                del self.cache[query]
                logger.info(f"Cache expired for query: {query}")
                metrics.track_cache_event(cache_name='llm_query_cache', hit=False)
                return None
            self.cache.move_to_end(query)
            logger.info(f"Cache hit for query: {query}")
            metrics.track_cache_event(cache_name='llm_query_cache', hit=True)
            return value
        logger.info(f"Cache miss for query: {query}")
        metrics.track_cache_event(cache_name='llm_query_cache', hit=False)
        return None

    def set(self, query: Tuple, result: Any):
        if query in self.cache:
            self.cache.move_to_end(query)
        self.cache[query] = (result, time.time())
        if len(self.cache) > self.max_size:
            evicted = self.cache.popitem(last=False)
            logger.info(f"Evicted query cache entry: {evicted[0]}")
        logger.info(f"Cached result for query: {query}")
        self._log_cache_stats()

    def invalidate(self, query: Tuple):
        if query in self.cache:
            del self.cache[query]
            logger.info(f"Invalidated cache for query: {query}")
        self._log_cache_stats()

    def clear(self):
        self.cache.clear()
        logger.info("Cleared all cached query results.")
        self._log_cache_stats()

    def _log_cache_stats(self):
        size = len(self.cache)
        mem = None
        if psutil:
            process = psutil.Process()
            mem = process.memory_info().rss / (1024 * 1024)  # MB
            logger.info(f"QueryResultCache size: {size}, process memory usage: {mem:.2f} MB")
        else:
            logger.info(f"QueryResultCache size: {size}")

# Example usage
if __name__ == "__main__":
    cache = QueryResultCache(max_size=2, ttl_seconds=2)
    q = ("vector1",)
    cache.set(q, [1, 2, 3])
    print(cache.get(q))
    time.sleep(3)
    print(cache.get(q))
    cache.invalidate(q)
    print(cache.get(q)) 