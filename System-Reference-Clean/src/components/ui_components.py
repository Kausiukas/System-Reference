"""
Streamlit UI Components for System-Reference

Optimized UI components for real-time repository processing and AI assistance.
"""

import streamlit as st
import time
from typing import Dict, Any, Optional
from datetime import datetime

def render_header():
    """Render application header"""
    st.title("📚 System-Reference")
    st.subheader("Real-Time Repository Processing & AI Assistance")
    
    # Add some spacing
    st.markdown("---")

def render_sidebar(config: Dict[str, Any], metrics_tracker):
    """Render sidebar with configuration and metrics"""
    
    st.sidebar.title("⚙️ Configuration")
    
    # Configuration status
    st.sidebar.subheader("🔧 Services")
    
    # GitHub status
    github_status = "✅ Connected" if config.get('github_token') else "❌ Not Connected"
    st.sidebar.write(f"GitHub: {github_status}")
    
    # OpenAI status
    openai_status = "✅ Connected" if config.get('openai_api_key') else "❌ Not Connected"
    st.sidebar.write(f"OpenAI: {openai_status}")
    
    # ChromaDB status
    chromadb_status = "✅ Connected" if config.get('chromadb_api_key') else "❌ Not Connected"
    st.sidebar.write(f"ChromaDB: {chromadb_status}")
    
    # Processing controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
    if auto_refresh:
        st.sidebar.write("🔄 Auto-refresh enabled")
    
    # Show metrics toggle
    show_metrics = st.sidebar.checkbox("Show Metrics", value=False)
    st.session_state.show_metrics = show_metrics
    
    # Clear cache button
    if st.sidebar.button("🗑️ Clear Cache"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache cleared!")
    
    # Reset session button
    if st.sidebar.button("🔄 Reset Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Session reset!")
        st.rerun()
    
    # Metrics display
    if show_metrics:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Metrics")
        metrics_tracker.display_metrics()

def render_repository_input(repo_processor, ai_engine):
    """Render repository input and processing interface"""
    
    st.header("🔍 Repository Analysis")
    
    # Repository input
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/user/repository",
        help="Enter the GitHub repository URL to analyze"
    )
    
    # Input validation
    if repo_url and not repo_url.startswith("https://github.com/"):
        st.error("Please enter a valid GitHub repository URL")
        return
    
    # Processing buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Start Analysis", type="primary"):
            if repo_url:
                with st.spinner("Processing repository..."):
                    try:
                        results = process_repository(repo_url, repo_processor)
                        st.success("Repository analysis completed!")
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
            else:
                st.error("Please enter a repository URL")
    
    with col2:
        if st.button("📋 Quick Demo"):
            # Load demo repository
            demo_url = "https://github.com/Kausiukas/System-Reference"
            with st.spinner("Loading demo repository..."):
                try:
                    results = process_repository(demo_url, repo_processor)
                    st.success("Demo repository loaded!")
                except Exception as e:
                    st.error(f"Demo failed: {str(e)}")
    
    # Recent repositories
    if st.session_state.get('recent_repositories'):
        st.subheader("📚 Recent Repositories")
        for repo in st.session_state.recent_repositories[-5:]:
            if st.button(f"📁 {repo}", key=f"recent_{repo}"):
                with st.spinner(f"Loading {repo}..."):
                    try:
                        results = process_repository(repo, repo_processor)
                        st.success(f"Repository {repo} loaded!")
                    except Exception as e:
                        st.error(f"Failed to load {repo}: {str(e)}")

def render_processing_status():
    """Render real-time processing status"""
    
    if st.session_state.processing_status != 'idle':
        st.subheader("🔄 Processing Status")
        
        # Status indicator
        status = st.session_state.processing_status
        message = st.session_state.get('status_message', '')
        
        # Status badges
        if status == 'initializing':
            st.info(f"🔄 {message}")
        elif status == 'extracting_metadata':
            st.info(f"📋 {message}")
        elif status == 'analyzing_structure':
            st.info(f"📁 {message}")
        elif status == 'analyzing_code':
            st.info(f"💻 {message}")
        elif status == 'building_rag':
            st.info(f"🧠 {message}")
        elif status == 'ready':
            st.success(f"✅ {message}")
        elif status == 'error':
            st.error(f"❌ {message}")
        
        # Progress bar for active processing
        if status in ['initializing', 'extracting_metadata', 'analyzing_structure', 'analyzing_code', 'building_rag']:
            progress_bar = st.progress(0)
            
            # Simulate progress (in real implementation, this would be based on actual progress)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
                if st.session_state.processing_status == 'ready':
                    break

def render_analysis_results(results: Dict[str, Any]):
    """Render repository analysis results"""
    
    st.header("📊 Analysis Results")
    
    if not results:
        st.info("No analysis results available. Please process a repository first.")
        return
    
    # Repository information
    repo_info = results.get('repository', {})
    if repo_info:
        st.subheader("📁 Repository Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Repository", repo_info.get('name', 'Unknown'))
            st.metric("Size", f"{repo_info.get('size', 0):.1f} MB")
        
        with col2:
            st.metric("Files", repo_info.get('file_count', 0))
            st.metric("Language", repo_info.get('primary_language', 'Unknown'))
        
        with col3:
            st.metric("Last Commit", repo_info.get('last_commit', 'Unknown'))
            st.metric("Processing Time", f"{results.get('processing_time', 0):.1f}s")
    
    # Code analysis statistics
    code_analysis = results.get('code_analysis', {})
    if code_analysis:
        st.subheader("💻 Code Analysis")
        
        stats = code_analysis.get('statistics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Files", stats.get('total_files', 0))
        
        with col2:
            st.metric("Functions", stats.get('total_functions', 0))
        
        with col3:
            st.metric("Classes", stats.get('total_classes', 0))
        
        with col4:
            st.metric("Lines of Code", stats.get('total_lines', 0))
    
    # File structure
    structure = results.get('structure', {})
    if structure:
        st.subheader("📂 File Structure")
        
        files = structure.get('files', [])
        if files:
            # Show file types distribution
            file_types = {}
            for file in files:
                file_type = file.get('type', 'unknown')
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Create a simple chart
            st.write("File Types Distribution:")
            for file_type, count in file_types.items():
                st.write(f"  {file_type}: {count} files")
    
    # Metadata
    metadata = results.get('metadata', {})
    if metadata:
        st.subheader("📋 Repository Metadata")
        
        # README information
        readme = metadata.get('readme')
        if readme:
            st.write("**README Found:** ✅")
            st.write(f"Size: {readme.get('size', 0)} characters")
            
            # Show README sections
            sections = readme.get('sections', {})
            if sections:
                st.write("**README Sections:**")
                for section_name, content in sections.items():
                    with st.expander(f"📄 {section_name.title()}"):
                        st.write(content[:500] + "..." if len(content) > 500 else content)
        else:
            st.write("**README Found:** ❌")
        
        # Dependencies
        dependencies = metadata.get('dependencies', {})
        if dependencies:
            st.write("**Dependencies:**")
            for dep_type, deps in dependencies.items():
                with st.expander(f"📦 {dep_type.title()}"):
                    for dep in deps:
                        st.write(f"  - {dep}")

def render_chat_interface(ai_engine):
    """Render AI chat interface"""
    
    st.header("🤖 AI Assistant")
    
    if not st.session_state.get('analysis_results'):
        st.info("💡 Process a repository first to enable AI assistance!")
        return
    
    # Chat history
    if st.session_state.get('chat_history'):
        st.subheader("💬 Chat History")
        
        for i, chat in enumerate(st.session_state.chat_history[-5:]):
            with st.expander(f"Q: {chat['query'][:50]}..."):
                st.write(f"**Question:** {chat['query']}")
                st.write(f"**Answer:** {chat['response']}")
                st.caption(f"Time: {datetime.fromtimestamp(chat['timestamp']).strftime('%H:%M:%S')}")
    
    # Chat input
    st.subheader("💭 Ask a Question")
    
    # Predefined questions
    st.write("**Quick Questions:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("What does this project do?"):
            st.session_state.quick_question = "What does this project do?"
        
        if st.button("How do I install it?"):
            st.session_state.quick_question = "How do I install and run this project?"
        
        if st.button("Show me the main functions"):
            st.session_state.quick_question = "What are the main functions and classes in this project?"
    
    with col2:
        if st.button("What are the key features?"):
            st.session_state.quick_question = "What are the key features of this project?"
        
        if st.button("How is the code organized?"):
            st.session_state.quick_question = "How is the code organized and structured?"
        
        if st.button("Show me the dependencies"):
            st.session_state.quick_question = "What are the main dependencies and requirements?"
    
    # Custom question input
    user_question = st.text_input(
        "Or ask your own question:",
        value=st.session_state.get('quick_question', ''),
        placeholder="Ask anything about the repository..."
    )
    
    # Clear quick question after use
    if 'quick_question' in st.session_state:
        del st.session_state.quick_question
    
    # Submit button
    if st.button("🚀 Ask AI", type="primary") and user_question:
        with st.spinner("AI is thinking..."):
            try:
                response = chat_with_ai(user_question, ai_engine)
                
                # Display response
                st.subheader("🤖 AI Response")
                st.write(response)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'query': user_question,
                    'response': response,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                st.error(f"Failed to get AI response: {str(e)}")

def render_error_boundary(func):
    """Error boundary decorator for UI components"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"UI Error in {func.__name__}: {str(e)}")
            st.info("Please refresh the page and try again.")
            return None
    return wrapper

# Apply error boundary to all UI functions
render_header = render_error_boundary(render_header)
render_sidebar = render_error_boundary(render_sidebar)
render_repository_input = render_error_boundary(render_repository_input)
render_processing_status = render_error_boundary(render_processing_status)
render_analysis_results = render_error_boundary(render_analysis_results)
render_chat_interface = render_error_boundary(render_chat_interface) 