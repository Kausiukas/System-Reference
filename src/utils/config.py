"""
Configuration Management for System-Reference

Handles environment variables, Streamlit secrets, and application configuration.
"""

import os
import streamlit as st
from typing import Dict, Any, Optional
import logging

def get_config() -> Dict[str, Any]:
    """
    Get configuration from environment variables or Streamlit secrets.
    
    Returns:
        Dict containing all configuration values
    """
    config = {}
    
    # Try to get from Streamlit secrets first (production)
    try:
        config['github_token'] = st.secrets['GITHUB_TOKEN']
        config['openai_api_key'] = st.secrets['OPENAI_API_KEY']
        config['chromadb_api_key'] = st.secrets['CHROMADB_API_KEY']
        config['postgres_url'] = st.secrets.get('POSTGRES_URL')
        config['redis_url'] = st.secrets.get('REDIS_URL')
        config['debug'] = st.secrets.get('DEBUG', False)
        config['log_level'] = st.secrets.get('LOG_LEVEL', 'INFO')
        config['max_workers'] = st.secrets.get('MAX_WORKERS', 10)
        
        logging.info("Configuration loaded from Streamlit secrets")
        
    except Exception as e:
        # Fallback to environment variables (development)
        config['github_token'] = os.getenv('GITHUB_TOKEN')
        config['openai_api_key'] = os.getenv('OPENAI_API_KEY')
        config['chromadb_api_key'] = os.getenv('CHROMADB_API_KEY')
        config['postgres_url'] = os.getenv('POSTGRES_URL')
        config['redis_url'] = os.getenv('REDIS_URL')
        config['debug'] = os.getenv('DEBUG', 'false').lower() == 'true'
        config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
        config['max_workers'] = int(os.getenv('MAX_WORKERS', '10'))
        
        logging.info("Configuration loaded from environment variables")
    
    # Set default values for optional configurations
    config.setdefault('embedding_model', 'all-MiniLM-L6-v2')
    config.setdefault('ai_model', 'gpt-4')
    config.setdefault('ai_temperature', 0.3)
    config.setdefault('ai_max_tokens', 2000)
    config.setdefault('processing_timeout', 1800)  # 30 minutes
    config.setdefault('cache_ttl', 3600)  # 1 hour
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if configuration is valid, False otherwise
    """
    required_keys = ['github_token', 'openai_api_key', 'chromadb_api_key']
    
    for key in required_keys:
        if not config.get(key):
            st.error(f"Missing required configuration: {key}")
            logging.error(f"Missing required configuration: {key}")
            return False
    
    # Validate GitHub token format
    if not config['github_token'].startswith('ghp_'):
        st.error("Invalid GitHub token format")
        logging.error("Invalid GitHub token format")
        return False
    
    # Validate OpenAI API key format
    if not config['openai_api_key'].startswith('sk-'):
        st.error("Invalid OpenAI API key format")
        logging.error("Invalid OpenAI API key format")
        return False
    
    logging.info("Configuration validation passed")
    return True

def get_database_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract database configuration from main config.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        Database configuration dictionary
    """
    return {
        'postgres_url': config.get('postgres_url'),
        'redis_url': config.get('redis_url'),
        'chromadb_api_key': config.get('chromadb_api_key')
    }

def get_ai_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract AI configuration from main config.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        AI configuration dictionary
    """
    return {
        'openai_api_key': config.get('openai_api_key'),
        'model': config.get('ai_model', 'gpt-4'),
        'temperature': config.get('ai_temperature', 0.3),
        'max_tokens': config.get('ai_max_tokens', 2000),
        'embedding_model': config.get('embedding_model', 'all-MiniLM-L6-v2')
    }

def get_github_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract GitHub configuration from main config.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        GitHub configuration dictionary
    """
    return {
        'token': config.get('github_token'),
        'timeout': config.get('processing_timeout', 1800)
    }

def is_production() -> bool:
    """
    Check if running in production environment.
    
    Returns:
        True if in production, False otherwise
    """
    # Check if running on Streamlit Cloud
    return 'STREAMLIT_SERVER_PORT' in os.environ

def get_cache_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract cache configuration from main config.
    
    Args:
        config: Main configuration dictionary
        
    Returns:
        Cache configuration dictionary
    """
    return {
        'ttl': config.get('cache_ttl', 3600),
        'max_size': config.get('cache_max_size', 1000),
        'enabled': config.get('cache_enabled', True)
    }

def log_config_summary(config: Dict[str, Any]):
    """
    Log configuration summary (without sensitive data).
    
    Args:
        config: Configuration dictionary
    """
    safe_config = {
        'debug': config.get('debug'),
        'log_level': config.get('log_level'),
        'max_workers': config.get('max_workers'),
        'ai_model': config.get('ai_model'),
        'embedding_model': config.get('embedding_model'),
        'processing_timeout': config.get('processing_timeout'),
        'cache_ttl': config.get('cache_ttl'),
        'production': is_production()
    }
    
    logging.info(f"Configuration summary: {safe_config}") 