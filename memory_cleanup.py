import gc
import psutil
import os
from datetime import datetime
from logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

def memory_cleanup():
    """Perform memory cleanup operations."""
    try:
        # Get memory usage before cleanup
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # Force garbage collection
        gc.collect()
        
        # Get memory usage after cleanup
        mem_after = process.memory_info().rss / 1024 / 1024
        
        # Log results
        logger.info(f"Memory cleanup completed - Before: {mem_before:.2f}MB, After: {mem_after:.2f}MB, Saved: {mem_before - mem_after:.2f}MB")
        
        return True
    except Exception as e:
        logger.error(f"Error during memory cleanup: {str(e)}")
        return False

if __name__ == "__main__":
    memory_cleanup() 