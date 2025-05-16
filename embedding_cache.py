from collections import OrderedDict
from typing import Any
from logging_utils import get_logger
from metrics_tracker import get_metrics_tracker

# Configure logging
logger = get_logger(__name__)

class EmbeddingCache:
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Any:
        metrics = get_metrics_tracker()
        if key in self.cache:
            self.cache.move_to_end(key)
            logger.info(f"Embedding cache hit for key: {key}")
            metrics.track_cache_event(cache_name='embedding_cache', hit=True)
            return self.cache[key]
        logger.info(f"Embedding cache miss for key: {key}")
        metrics.track_cache_event(cache_name='embedding_cache', hit=False)
        return None

    def set(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            evicted = self.cache.popitem(last=False)
            logger.info(f"Evicted embedding cache entry: {evicted[0]}")
        logger.info(f"Cached embedding for key: {key}")

    def clear(self):
        self.cache.clear()
        logger.info("Cleared all cached embeddings.")

# Example usage
if __name__ == "__main__":
    cache = EmbeddingCache(max_size=2)
    cache.set("text1", [0.1, 0.2])
    cache.set("text2", [0.3, 0.4])
    print(cache.get("text1"))
    cache.set("text3", [0.5, 0.6])  # Should evict "text2"
    print(cache.get("text2")) 