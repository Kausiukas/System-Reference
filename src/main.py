#!/usr/bin/env python3
"""
System-Reference: Main Streamlit Application

Real-Time Repository Processing System optimized for Streamlit Cloud deployment.
Provides intelligent codebase analysis and AI-powered assistance.
"""

import streamlit as st
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import time

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

# Import application components
from utils.config import get_config, validate_config
from utils.session import init_session_state, update_processing_status
from utils.cache import cache_function, cache_resource
from utils.error_handling import handle_errors
from utils.metrics import MetricsTracker
from components.repository_processor import RepositoryProcessor
from components.ai_engine import AIEngine
from components.ui_components import (
    render_header,
    render_sidebar,
    render_repository_input,
    render_processing_status,
    render_chat_interface,
    render_analysis_results
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize metrics tracker
metrics_tracker = MetricsTracker()

def main():
    """Main application function"""
    
    # Configure page
    st.set_page_config(
        page_title="System-Reference",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Get configuration
    config = get_config()
    
    # Validate configuration
    if not validate_config(config):
        st.error("Configuration validation failed. Please check your environment variables.")
        st.stop()
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar(config, metrics_tracker)
    
    # Main application logic
    try:
        # Initialize components
        repo_processor = get_repository_processor(config)
        ai_engine = get_ai_engine(config)
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Repository input and processing
            render_repository_input(repo_processor, ai_engine)
            
            # Processing status
            render_processing_status()
            
            # Analysis results
            if st.session_state.get('analysis_results'):
                render_analysis_results(st.session_state.analysis_results)
        
        with col2:
            # Chat interface
            render_chat_interface(ai_engine)
        
        # Display metrics
        if st.session_state.get('show_metrics', False):
            metrics_tracker.display_metrics()
    
    except Exception as e:
        logging.error(f"Application error: {e}")
        st.error(f"An unexpected error occurred: {str(e)}")
        st.info("Please refresh the page and try again.")

@cache_resource
def get_repository_processor(config: Dict[str, Any]) -> RepositoryProcessor:
    """Get cached repository processor instance"""
    return RepositoryProcessor(config)

@cache_resource
def get_ai_engine(config: Dict[str, Any]) -> AIEngine:
    """Get cached AI engine instance"""
    return AIEngine(config)

@handle_errors
def process_repository(repo_url: str, repo_processor: RepositoryProcessor) -> Dict[str, Any]:
    """Process a repository with real-time updates"""
    
    # Update status
    update_processing_status('initializing', 'Initializing repository processing...')
    
    # Start timing
    start_time = time.time()
    
    try:
        # Stage 1: Repository initialization
        update_processing_status('initializing', 'Cloning repository...')
        repo_info = repo_processor.initialize_repository(repo_url)
        metrics_tracker.track_timing('repository_initialization', start_time)
        
        # Stage 2: Metadata extraction
        update_processing_status('extracting_metadata', 'Extracting metadata...')
        metadata = repo_processor.extract_metadata(repo_info)
        metrics_tracker.track_timing('metadata_extraction', start_time)
        
        # Stage 3: File structure analysis
        update_processing_status('analyzing_structure', 'Analyzing file structure...')
        structure = repo_processor.analyze_file_structure(repo_info)
        metrics_tracker.track_timing('structure_analysis', start_time)
        
        # Stage 4: Code analysis
        update_processing_status('analyzing_code', 'Analyzing code...')
        code_analysis = repo_processor.analyze_code(repo_info)
        metrics_tracker.track_timing('code_analysis', start_time)
        
        # Stage 5: RAG index building
        update_processing_status('building_rag', 'Building AI knowledge base...')
        rag_index = repo_processor.build_rag_index(metadata, structure, code_analysis)
        metrics_tracker.track_timing('rag_index_building', start_time)
        
        # Complete processing
        update_processing_status('ready', 'AI Assistant ready!')
        
        # Store results
        results = {
            'repository': repo_info,
            'metadata': metadata,
            'structure': structure,
            'code_analysis': code_analysis,
            'rag_index': rag_index,
            'processing_time': time.time() - start_time
        }
        
        st.session_state.analysis_results = results
        st.session_state.current_repository = repo_url
        
        # Track metrics
        metrics_tracker.track_metric('total_processing_time', results['processing_time'])
        metrics_tracker.track_metric('files_processed', len(code_analysis.get('files', [])))
        metrics_tracker.track_metric('functions_found', code_analysis.get('statistics', {}).get('total_functions', 0))
        
        return results
        
    except Exception as e:
        update_processing_status('error', f'Processing failed: {str(e)}')
        raise e

@handle_errors
def chat_with_ai(query: str, ai_engine: AIEngine) -> str:
    """Chat with AI assistant"""
    
    if not st.session_state.get('analysis_results'):
        return "Please process a repository first before asking questions."
    
    # Track chat metrics
    metrics_tracker.track_metric('chat_queries', 1, 'chat')
    
    # Get response from AI
    response = ai_engine.get_response(query, st.session_state.analysis_results)
    
    # Add to chat history
    st.session_state.chat_history.append({
        'query': query,
        'response': response,
        'timestamp': time.time()
    })
    
    return response

if __name__ == "__main__":
    main() 