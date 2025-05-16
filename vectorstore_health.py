import psutil
import logging
from typing import Dict, Any, Optional
from chromadb import Client, Collection
from chromadb.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='vectorstore_health.log'
)
logger = logging.getLogger(__name__)

class VectorStoreHealth:
    def __init__(self, client: Client, memory_threshold_mb: int = 8000):
        """
        Initialize the health checker for vector store.
        
        Args:
            client: ChromaDB client instance
            memory_threshold_mb: Memory threshold in MB (default: 8000MB = 8GB)
        """
        self.client = client
        self.memory_threshold = memory_threshold_mb * 1024 * 1024  # Convert to bytes
        self._last_memory_check = 0
        self._last_stats = None

    def get_memory_usage(self) -> int:
        """Get current memory usage of the process in bytes."""
        process = psutil.Process()
        return process.memory_info().rss

    def check_memory_threshold(self) -> bool:
        """Check if current memory usage is below threshold."""
        current_memory = self.get_memory_usage()
        is_below_threshold = current_memory < self.memory_threshold
        
        if not is_below_threshold:
            logger.warning(
                f"Memory usage ({current_memory / (1024*1024):.2f} MB) "
                f"exceeds threshold ({self.memory_threshold / (1024*1024):.2f} MB)"
            )
        
        return is_below_threshold

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get lightweight statistics for a collection without loading all documents.
        
        Args:
            collection_name: Name of the collection to check
            
        Returns:
            Dictionary containing collection statistics
        """
        try:
            collection = self.client.get_collection(collection_name)
            stats = collection.get_stats()
            count = collection.count()
            
            return {
                'name': collection_name,
                'document_count': count,
                'dimension': stats.get('dimension', 0),
                'memory_usage': self.get_memory_usage(),
                'status': 'healthy'
            }
        except Exception as e:
            logger.error(f"Error getting stats for collection {collection_name}: {str(e)}")
            return {
                'name': collection_name,
                'status': 'error',
                'error': str(e)
            }

    def check_collection_health(self, collection_name: str) -> Dict[str, Any]:
        """
        Perform a comprehensive health check on a collection.
        
        Args:
            collection_name: Name of the collection to check
            
        Returns:
            Dictionary containing health check results
        """
        try:
            # Get basic stats
            stats = self.get_collection_stats(collection_name)
            
            # Check memory usage
            memory_ok = self.check_memory_threshold()
            
            # Try to get a single document to verify access
            collection = self.client.get_collection(collection_name)
            sample = collection.peek(limit=1)
            
            return {
                **stats,
                'memory_ok': memory_ok,
                'sample_accessible': bool(sample),
                'timestamp': psutil.Process().create_time()
            }
        except Exception as e:
            logger.error(f"Health check failed for collection {collection_name}: {str(e)}")
            return {
                'name': collection_name,
                'status': 'error',
                'error': str(e),
                'memory_ok': self.check_memory_threshold()
            }

    def get_all_collections_health(self) -> Dict[str, Any]:
        """
        Check health of all collections in the vector store.
        
        Returns:
            Dictionary containing health status of all collections
        """
        try:
            collections = self.client.list_collections()
            results = {
                'total_collections': len(collections),
                'collections': {},
                'memory_usage': self.get_memory_usage(),
                'memory_ok': self.check_memory_threshold(),
                'timestamp': psutil.Process().create_time()
            }
            
            for collection in collections:
                results['collections'][collection.name] = self.check_collection_health(collection.name)
            
            return results
        except Exception as e:
            logger.error(f"Error checking all collections: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'memory_ok': self.check_memory_threshold()
            }

def create_health_checker(persist_directory: str, memory_threshold_mb: int = 8000) -> VectorStoreHealth:
    """
    Create a VectorStoreHealth instance with the specified configuration.
    
    Args:
        persist_directory: Directory where ChromaDB data is persisted
        memory_threshold_mb: Memory threshold in MB
        
    Returns:
        VectorStoreHealth instance
    """
    settings = Settings(
        chroma_segment_cache_policy="LRU",
        chroma_memory_limit_bytes=memory_threshold_mb * 1024 * 1024
    )
    
    client = Client(persist_directory=persist_directory, settings=settings)
    return VectorStoreHealth(client, memory_threshold_mb) 