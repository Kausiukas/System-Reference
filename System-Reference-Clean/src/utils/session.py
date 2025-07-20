"""
Session State Management for System-Reference

Manages Streamlit session state for real-time updates and data persistence.
"""

import streamlit as st
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

def init_session_state():
    """Initialize session state variables with default values."""
    
    # Processing status
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = 'idle'
    
    if 'status_message' not in st.session_state:
        st.session_state.status_message = ''
    
    if 'processing_start_time' not in st.session_state:
        st.session_state.processing_start_time = None
    
    # Repository data
    if 'current_repository' not in st.session_state:
        st.session_state.current_repository = None
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    if 'recent_repositories' not in st.session_state:
        st.session_state.recent_repositories = []
    
    # Chat and AI
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'ai_model_loaded' not in st.session_state:
        st.session_state.ai_model_loaded = False
    
    # UI state
    if 'show_metrics' not in st.session_state:
        st.session_state.show_metrics = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # Error handling
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None
    
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0

def update_processing_status(status: str, message: str = ""):
    """
    Update processing status and message.
    
    Args:
        status: Processing status ('idle', 'initializing', 'extracting_metadata', 
                'analyzing_structure', 'analyzing_code', 'building_rag', 'ready', 'error')
        message: Status message
    """
    st.session_state.processing_status = status
    st.session_state.status_message = message
    
    # Update processing start time for new processing
    if status in ['initializing', 'extracting_metadata']:
        st.session_state.processing_start_time = time.time()
    
    # Log status change
    if hasattr(st, 'logger'):
        st.logger.info(f"Processing status: {status} - {message}")

def get_processing_status() -> Dict[str, Any]:
    """
    Get current processing status and information.
    
    Returns:
        Dictionary with processing status information
    """
    status_info = {
        'status': st.session_state.processing_status,
        'message': st.session_state.status_message,
        'start_time': st.session_state.processing_start_time,
        'duration': None
    }
    
    # Calculate duration if processing
    if (st.session_state.processing_start_time and 
        st.session_state.processing_status not in ['idle', 'ready', 'error']):
        status_info['duration'] = time.time() - st.session_state.processing_start_time
    
    return status_info

def add_recent_repository(repo_url: str):
    """
    Add repository to recent repositories list.
    
    Args:
        repo_url: Repository URL to add
    """
    if repo_url not in st.session_state.recent_repositories:
        st.session_state.recent_repositories.append(repo_url)
        
        # Keep only last 10 repositories
        if len(st.session_state.recent_repositories) > 10:
            st.session_state.recent_repositories = st.session_state.recent_repositories[-10:]

def get_recent_repositories() -> List[str]:
    """
    Get list of recent repositories.
    
    Returns:
        List of recent repository URLs
    """
    return st.session_state.recent_repositories

def add_chat_message(query: str, response: str):
    """
    Add a chat message to history.
    
    Args:
        query: User query
        response: AI response
    """
    chat_entry = {
        'query': query,
        'response': response,
        'timestamp': time.time(),
        'datetime': datetime.now().isoformat()
    }
    
    st.session_state.chat_history.append(chat_entry)
    
    # Keep only last 50 messages
    if len(st.session_state.chat_history) > 50:
        st.session_state.chat_history = st.session_state.chat_history[-50:]

def get_chat_history() -> List[Dict[str, Any]]:
    """
    Get chat history.
    
    Returns:
        List of chat messages
    """
    return st.session_state.chat_history

def clear_chat_history():
    """Clear chat history."""
    st.session_state.chat_history = []

def set_analysis_results(results: Dict[str, Any]):
    """
    Set analysis results in session state.
    
    Args:
        results: Analysis results dictionary
    """
    st.session_state.analysis_results = results
    st.session_state.current_repository = results.get('repository', {}).get('url')

def get_analysis_results() -> Optional[Dict[str, Any]]:
    """
    Get current analysis results.
    
    Returns:
        Analysis results dictionary or None
    """
    return st.session_state.analysis_results

def has_analysis_results() -> bool:
    """
    Check if analysis results are available.
    
    Returns:
        True if analysis results exist, False otherwise
    """
    return bool(st.session_state.analysis_results)

def set_error(error: str):
    """
    Set error information in session state.
    
    Args:
        error: Error message
    """
    st.session_state.last_error = error
    st.session_state.error_count += 1
    st.session_state.processing_status = 'error'
    st.session_state.status_message = f"Error: {error}"

def get_error_info() -> Dict[str, Any]:
    """
    Get error information.
    
    Returns:
        Dictionary with error information
    """
    return {
        'last_error': st.session_state.last_error,
        'error_count': st.session_state.error_count,
        'has_error': bool(st.session_state.last_error)
    }

def clear_error():
    """Clear error information."""
    st.session_state.last_error = None

def set_ai_model_loaded(loaded: bool = True):
    """
    Set AI model loaded status.
    
    Args:
        loaded: Whether AI model is loaded
    """
    st.session_state.ai_model_loaded = loaded

def is_ai_model_loaded() -> bool:
    """
    Check if AI model is loaded.
    
    Returns:
        True if AI model is loaded, False otherwise
    """
    return st.session_state.ai_model_loaded

def set_current_page(page: str):
    """
    Set current page.
    
    Args:
        page: Page name
    """
    st.session_state.current_page = page

def get_current_page() -> str:
    """
    Get current page.
    
    Returns:
        Current page name
    """
    return st.session_state.current_page

def get_session_summary() -> Dict[str, Any]:
    """
    Get session state summary (for debugging).
    
    Returns:
        Dictionary with session state summary
    """
    return {
        'processing_status': st.session_state.processing_status,
        'current_repository': st.session_state.current_repository,
        'has_analysis_results': has_analysis_results(),
        'chat_history_length': len(st.session_state.chat_history),
        'recent_repositories_count': len(st.session_state.recent_repositories),
        'ai_model_loaded': st.session_state.ai_model_loaded,
        'error_count': st.session_state.error_count,
        'current_page': st.session_state.current_page
    }

def reset_session():
    """Reset all session state variables."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Re-initialize
    init_session_state()

def export_session_data() -> Dict[str, Any]:
    """
    Export session data for debugging or backup.
    
    Returns:
        Dictionary with session data
    """
    return {
        'processing_status': st.session_state.processing_status,
        'status_message': st.session_state.status_message,
        'current_repository': st.session_state.current_repository,
        'recent_repositories': st.session_state.recent_repositories,
        'chat_history': st.session_state.chat_history,
        'error_count': st.session_state.error_count,
        'current_page': st.session_state.current_page,
        'export_timestamp': datetime.now().isoformat()
    } 