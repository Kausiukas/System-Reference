"""
Caching Utilities for System-Reference

Optimized caching strategies for Streamlit Cloud deployment.
"""

import streamlit as st
import time
import hashlib
import json
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union
import logging

def cache_function(ttl: int = 3600, max_entries: int = 1000):
    """
    Cache function results with TTL and max entries limit.
    
    Args:
        ttl: Time to live in seconds
        max_entries: Maximum number of cached entries
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @st.cache_data(ttl=ttl, max_entries=max_entries)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def cache_resource():
    """
    Cache expensive resources in memory.
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @st.cache_resource
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a unique cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Unique cache key string
    """
    # Convert arguments to string representation
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    # Generate hash
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_with_key_generator(key_func: Callable):
    """
    Cache function with custom key generator.
    
    Args:
        key_func: Function to generate cache keys
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @st.cache_data
        def wrapper(*args, **kwargs):
            # Generate custom key
            cache_key = key_func(*args, **kwargs)
            
            # Use the key as part of the cache identifier
            return func(*args, **kwargs)
        return wrapper
    return decorator

def cache_github_data(ttl: int = 1800):
    """
    Cache GitHub API data with shorter TTL.
    
    Args:
        ttl: Time to live in seconds (default 30 minutes)
        
    Returns:
        Decorator function
    """
    return cache_function(ttl=ttl, max_entries=500)

def cache_ai_responses(ttl: int = 3600):
    """
    Cache AI responses with longer TTL.
    
    Args:
        ttl: Time to live in seconds (default 1 hour)
        
    Returns:
        Decorator function
    """
    return cache_function(ttl=ttl, max_entries=200)

def cache_analysis_results(ttl: int = 7200):
    """
    Cache repository analysis results with long TTL.
    
    Args:
        ttl: Time to live in seconds (default 2 hours)
        
    Returns:
        Decorator function
    """
    return cache_function(ttl=ttl, max_entries=100)

class CacheManager:
    """Manages caching operations and statistics."""
    
    def __init__(self):
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def track_cache_hit(self, cache_name: str):
        """Track a cache hit."""
        self.cache_stats['hits'] += 1
        logging.debug(f"Cache hit: {cache_name}")
    
    def track_cache_miss(self, cache_name: str):
        """Track a cache miss."""
        self.cache_stats['misses'] += 1
        logging.debug(f"Cache miss: {cache_name}")
    
    def track_cache_set(self, cache_name: str):
        """Track a cache set operation."""
        self.cache_stats['sets'] += 1
        logging.debug(f"Cache set: {cache_name}")
    
    def track_cache_delete(self, cache_name: str):
        """Track a cache delete operation."""
        self.cache_stats['deletes'] += 1
        logging.debug(f"Cache delete: {cache_name}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self.cache_stats.copy()
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        if total_requests == 0:
            return 0.0
        return self.cache_stats['hits'] / total_requests
    
    def clear_cache_stats(self):
        """Clear cache statistics."""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

# Global cache manager instance
cache_manager = CacheManager()

def smart_cache(ttl: int = 3600, max_entries: int = 1000, cache_name: str = None):
    """
    Smart caching with statistics tracking.
    
    Args:
        ttl: Time to live in seconds
        max_entries: Maximum number of cached entries
        cache_name: Name for cache tracking
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @st.cache_data(ttl=ttl, max_entries=max_entries)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(*args, **kwargs)
            cache_id = cache_name or f"{func.__name__}_{cache_key}"
            
            # Track cache operation
            cache_manager.track_cache_set(cache_id)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def cache_with_fallback(fallback_func: Callable, ttl: int = 3600):
    """
    Cache with fallback function if cache fails.
    
    Args:
        fallback_func: Function to call if cache fails
        ttl: Time to live in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @st.cache_data(ttl=ttl)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.warning(f"Cache failed for {func.__name__}: {e}")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator

def clear_all_caches():
    """Clear all Streamlit caches."""
    st.cache_data.clear()
    st.cache_resource.clear()
    cache_manager.clear_cache_stats()
    logging.info("All caches cleared")

def get_cache_info() -> Dict[str, Any]:
    """
    Get information about current cache state.
    
    Returns:
        Dictionary with cache information
    """
    return {
        'stats': cache_manager.get_cache_stats(),
        'hit_rate': cache_manager.get_hit_rate(),
        'cache_cleared': False  # This would need to be tracked separately
    }

# Predefined cache decorators for common use cases
@cache_github_data(ttl=1800)
def cache_github_repository_info(repo_url: str) -> Dict[str, Any]:
    """Cache GitHub repository information."""
    # This is a placeholder - actual implementation would be in the GitHub API module
    pass

@cache_ai_responses(ttl=3600)
def cache_ai_response(query: str, context: str) -> str:
    """Cache AI responses."""
    # This is a placeholder - actual implementation would be in the AI module
    pass

@cache_analysis_results(ttl=7200)
def cache_repository_analysis(repo_url: str) -> Dict[str, Any]:
    """Cache repository analysis results."""
    # This is a placeholder - actual implementation would be in the processor module
    pass

@cache_resource()
def cache_ai_model():
    """Cache AI model in memory."""
    # This is a placeholder - actual implementation would be in the AI module
    pass

@cache_resource()
def cache_embedding_model():
    """Cache embedding model in memory."""
    # This is a placeholder - actual implementation would be in the AI module
    pass 