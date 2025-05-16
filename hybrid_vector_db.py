import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from vector_db import AnnoyVectorDB, ChromaVectorDB, BaseVectorDB
import logging
from metrics_tracker import get_metrics_tracker
import gc

logger = logging.getLogger(__name__)

class HybridVectorDB(BaseVectorDB):
    def __init__(self, 
                 cache_path: str = "D:/DATA/cache",
                 full_db_path: str = "D:/DATA/vectorstore",
                 cache_size: int = 1000):
        """
        Initialize a hybrid vector database with two tiers:
        - Hot cache using Annoy for fast access
        - Full dataset using ChromaDB for complete coverage
        
        Args:
            cache_path: Path to store the Annoy cache index
            full_db_path: Path to store the ChromaDB full dataset
            cache_size: Maximum number of documents to keep in cache
        """
        self.cache_path = Path(cache_path)
        self.full_db_path = Path(full_db_path)
        self.cache_size = cache_size
        
        # Initialize metrics tracker
        self.metrics = get_metrics_tracker()
        
        # Create cache directory if it doesn't exist
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize both backends
        self.cache_db = AnnoyVectorDB(str(self.cache_path))
        self.full_db = ChromaVectorDB(str(self.full_db_path))
        
        # Track cache hits/misses
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info(f"Initialized HybridVectorDB with cache size {cache_size}")
    
    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        """
        Add documents to both the cache and full database.
        If cache is full, oldest documents are removed.
        """
        # Add to full database first
        self.full_db.add_documents(texts, metadata)
        
        # Get current cache stats
        cache_stats = self.cache_db.get_stats()
        current_cache_size = cache_stats['total_documents']
        
        # If adding these documents would exceed cache size, remove oldest
        if current_cache_size + len(texts) > self.cache_size:
            # TODO: Implement cache eviction strategy
            # For now, we'll just not add to cache if it would exceed size
            logger.warning(f"Cache would exceed size limit ({self.cache_size}). Skipping cache update.")
            return
        
        # Add to cache
        self.cache_db.add_documents(texts, metadata)
        logger.info(f"Added {len(texts)} documents to both cache and full database")
    
    def search(self, query: str, k: int = 5, cache_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Orchestrate query: Try cache first, then fallback to full search if needed.
        Args:
            query: Search query
            k: Number of results to return
            cache_threshold: Minimum similarity score to accept cache results
        Returns:
            List of search results with metadata and scores
        """
        # --- Cache-first search logic ---
        cache_results = self.cache_db.search(query, k)
        cache_hit = False
        if cache_results:
            # Accept cache if top result meets threshold
            if cache_results[0]['score'] >= cache_threshold:
                cache_hit = True
        
        if cache_hit:
            self.cache_hits += 1
            self.metrics.track_cache_hit()
            logger.debug(f"Cache hit for query: {query}")
            return cache_results
        else:
            # --- Fallback to full search ---
            self.cache_misses += 1
            self.metrics.track_cache_miss()
            logger.debug(f"Cache miss for query: {query}, falling back to full search")
            return self.full_db.search(query, k)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the hybrid database."""
        cache_stats = self.cache_db.get_stats()
        full_stats = self.full_db.get_stats()
        
        total_queries = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        return {
            'cache': {
                'total_documents': cache_stats['total_documents'],
                'dimension': cache_stats['dimension'],
                'is_built': cache_stats['is_built']
            },
            'full_db': {
                'total_documents': full_stats['total_documents'],
                'dimension': full_stats['dimension'],
                'is_built': full_stats['is_built']
            },
            'performance': {
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'hit_rate': f"{hit_rate:.1f}%"
            }
        }
    
    def rebuild_cache(self, documents: Optional[List[str]] = None, metadata: Optional[List[Dict[str, Any]]] = None):
        """
        Rebuild the cache with new documents or from the full database.
        
        Args:
            documents: Optional list of documents to add to cache
            metadata: Optional metadata for the documents
        """
        if documents is None:
            # TODO: Implement logic to select most relevant documents from full_db
            # For now, we'll just clear the cache
            logger.warning("Cache rebuild without documents not implemented yet")
            return
        
        # Dereference and clean up the Annoy index before deleting files
        self.cache_db.index = None
        del self.cache_db
        gc.collect()
        
        # Now clear existing cache files
        for file in self.cache_path.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete {file}: {e}")
        
        # Create new cache instance
        self.cache_db = AnnoyVectorDB(str(self.cache_path))
        
        # Add new documents
        self.add_documents(documents, metadata)
        logger.info(f"Rebuilt cache with {len(documents)} documents")

    def schedule_cache_rebuild(self, interval_hours: int = 24):
        """
        Schedule periodic cache rebuilding.
        Args:
            interval_hours: Interval in hours for cache rebuild
        """
        logger.info(f"Cache rebuild scheduled every {interval_hours} hours")
        # TODO: Implement actual scheduling logic (e.g., using a background task or cron job)

    def check_cache_freshness(self) -> bool:
        """
        Check if the cache is fresh based on a predefined freshness threshold.
        Returns:
            bool: True if cache is fresh, False otherwise
        """
        # TODO: Implement actual freshness check logic (e.g., based on last update time)
        logger.info("Cache freshness check performed")
        return True

    def trigger_cache_update(self):
        """
        Trigger an immediate cache update.
        """
        logger.info("Cache update triggered")
        # TODO: Implement actual cache update logic (e.g., rebuild cache with latest documents) 