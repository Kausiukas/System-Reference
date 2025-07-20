# Streamlit Cloud Deployment Guide

## 🎯 **Overview**

This guide provides step-by-step instructions for deploying the System-Reference application to Streamlit Cloud, including configuration, optimization, and monitoring setup.

## 🚀 **Prerequisites**

### **Required Accounts**
- **GitHub Account**: For repository hosting and version control
- **Streamlit Cloud Account**: For application deployment
- **OpenAI Account**: For AI/ML capabilities
- **ChromaDB Cloud Account**: For vector database storage
- **PostgreSQL Cloud Account**: For data storage (optional)
- **Redis Cloud Account**: For caching (optional)

### **Required Tokens & Keys**
```bash
# GitHub Personal Access Token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# OpenAI API Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# ChromaDB API Key
CHROMADB_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# PostgreSQL Connection String (optional)
POSTGRES_URL=postgresql://user:pass@host:port/db

# Redis Connection String (optional)
REDIS_URL=redis://user:pass@host:port
```

## 📋 **Deployment Steps**

### **Step 1: Repository Setup**

1. **Fork the Repository**
   ```bash
   # Fork the System-Reference repository to your GitHub account
   # Visit: https://github.com/Kausiukas/System-Reference
   # Click "Fork" button
   ```

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/System-Reference.git
   cd System-Reference
   ```

3. **Verify Repository Structure**
   ```bash
   # Ensure the following files exist:
   ls -la
   # Should include:
   # - src/main.py (main application)
   # - requirements.txt (dependencies)
   # - .streamlit/config.toml (Streamlit configuration)
   # - README.md (documentation)
   ```

### **Step 2: Streamlit Cloud Configuration**

1. **Create Streamlit Configuration**
   ```toml
   # .streamlit/config.toml
   [theme]
   primaryColor = "#FF6B6B"
   backgroundColor = "#FFFFFF"
   secondaryBackgroundColor = "#F0F2F6"
   textColor = "#262730"
   font = "sans serif"

   [server]
   maxUploadSize = 200
   enableCORS = false
   enableXsrfProtection = true
   headless = true

   [browser]
   gatherUsageStats = false
   serverAddress = "localhost"
   serverPort = 8501

   [client]
   showErrorDetails = false
   ```

2. **Update Requirements**
   ```txt
   # requirements.txt
   streamlit>=1.28.0
   openai>=1.0.0
   chromadb>=0.4.0
   sentence-transformers>=2.2.0
   langchain>=0.1.0
   psycopg2-binary>=2.9.0
   redis>=4.5.0
   requests>=2.31.0
   PyGithub>=1.59.0
   python-dotenv>=1.0.0
   ```

### **Step 3: Connect to Streamlit Cloud**

1. **Access Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Sign in with your GitHub account

2. **Deploy New App**
   - Click "New app"
   - Select your forked repository
   - Set the main file path: `src/main.py`
   - Click "Deploy"

3. **Configure Environment Variables**
   ```bash
   # In Streamlit Cloud dashboard:
   # Go to App Settings > Secrets
   # Add the following secrets:
   
   GITHUB_TOKEN = "your_github_token"
   OPENAI_API_KEY = "your_openai_key"
   CHROMADB_API_KEY = "your_chromadb_key"
   POSTGRES_URL = "your_postgres_url"
   REDIS_URL = "your_redis_url"
   ```

### **Step 4: Application Configuration**

1. **Main Application Entry Point**
   ```python
   # src/main.py
   import streamlit as st
   import os
   from dotenv import load_dotenv
   
   # Load environment variables
   load_dotenv()
   
   # Configure page
   st.set_page_config(
       page_title="System-Reference",
       page_icon="📚",
       layout="wide",
       initial_sidebar_state="expanded"
   )
   
   # Main application
   def main():
       st.title("System-Reference: Repository Processing")
       st.subheader("Real-Time Code Analysis & AI Assistance")
       
       # Your application logic here
       pass
   
   if __name__ == "__main__":
       main()
   ```

2. **Environment Variable Handling**
   ```python
   # src/utils/config.py
   import os
   import streamlit as st
   
   def get_config():
       """Get configuration from environment variables or Streamlit secrets"""
       config = {}
       
       # Try to get from Streamlit secrets first
       try:
           config['github_token'] = st.secrets['GITHUB_TOKEN']
           config['openai_api_key'] = st.secrets['OPENAI_API_KEY']
           config['chromadb_api_key'] = st.secrets['CHROMADB_API_KEY']
           config['postgres_url'] = st.secrets.get('POSTGRES_URL')
           config['redis_url'] = st.secrets.get('REDIS_URL')
       except:
           # Fallback to environment variables
           config['github_token'] = os.getenv('GITHUB_TOKEN')
           config['openai_api_key'] = os.getenv('OPENAI_API_KEY')
           config['chromadb_api_key'] = os.getenv('CHROMADB_API_KEY')
           config['postgres_url'] = os.getenv('POSTGRES_URL')
           config['redis_url'] = os.getenv('REDIS_URL')
       
       return config
   ```

## ⚙️ **Performance Optimization**

### **Caching Strategy**

```python
# src/utils/cache.py
import streamlit as st
import time
from functools import wraps

def cache_function(ttl=3600):
    """Cache function results with TTL"""
    def decorator(func):
        @st.cache_data(ttl=ttl)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def cache_resource():
    """Cache expensive resources"""
    def decorator(func):
        @st.cache_resource
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage examples
@cache_function(ttl=1800)  # Cache for 30 minutes
def get_repository_info(repo_url: str):
    """Get repository information from GitHub API"""
    # Implementation here
    pass

@cache_resource()
def get_ai_model():
    """Load and cache AI model"""
    # Implementation here
    pass
```

### **Session State Management**

```python
# src/utils/session.py
import streamlit as st
from typing import Any, Dict

def init_session_state():
    """Initialize session state variables"""
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = 'idle'
    
    if 'current_repository' not in st.session_state:
        st.session_state.current_repository = None
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def update_processing_status(status: str, message: str = ""):
    """Update processing status"""
    st.session_state.processing_status = status
    if message:
        st.session_state.status_message = message

def get_processing_status() -> Dict[str, Any]:
    """Get current processing status"""
    return {
        'status': st.session_state.processing_status,
        'message': st.session_state.get('status_message', '')
    }
```

### **Error Handling**

```python
# src/utils/error_handling.py
import streamlit as st
import logging
from typing import Callable, Any

def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors gracefully"""
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            st.error(f"An error occurred: {str(e)}")
            st.info("Please try again or contact support if the issue persists.")
            return None
    return wrapper

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration"""
    required_keys = ['github_token', 'openai_api_key', 'chromadb_api_key']
    
    for key in required_keys:
        if not config.get(key):
            st.error(f"Missing required configuration: {key}")
            return False
    
    return True
```

## 📊 **Monitoring & Analytics**

### **Custom Metrics Tracking**

```python
# src/utils/metrics.py
import streamlit as st
import time
from typing import Dict, Any

class MetricsTracker:
    def __init__(self):
        if 'metrics' not in st.session_state:
            st.session_state.metrics = {}
    
    def track_metric(self, name: str, value: float, category: str = 'general'):
        """Track a custom metric"""
        if category not in st.session_state.metrics:
            st.session_state.metrics[category] = {}
        
        st.session_state.metrics[category][name] = value
    
    def track_timing(self, name: str, start_time: float):
        """Track timing for an operation"""
        duration = time.time() - start_time
        self.track_metric(f"{name}_duration", duration, 'timing')
    
    def get_metrics(self, category: str = None) -> Dict[str, Any]:
        """Get tracked metrics"""
        if category:
            return st.session_state.metrics.get(category, {})
        return st.session_state.metrics
    
    def display_metrics(self):
        """Display metrics in the sidebar"""
        if st.session_state.metrics:
            st.sidebar.subheader("📊 Metrics")
            
            for category, metrics in st.session_state.metrics.items():
                st.sidebar.write(f"**{category.title()}:**")
                for name, value in metrics.items():
                    if isinstance(value, float):
                        st.sidebar.write(f"  {name}: {value:.2f}")
                    else:
                        st.sidebar.write(f"  {name}: {value}")
```

### **Performance Monitoring**

```python
# src/utils/performance.py
import streamlit as st
import time
import psutil
import os

def get_system_info():
    """Get system information"""
    return {
        'memory_usage': psutil.virtual_memory().percent,
        'cpu_usage': psutil.cpu_percent(),
        'disk_usage': psutil.disk_usage('/').percent
    }

def monitor_performance(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        duration = end_time - start_time
        memory_delta = end_memory - start_memory
        
        # Track metrics
        if 'metrics' in st.session_state:
            st.session_state.metrics.setdefault('performance', {})
            st.session_state.metrics['performance'][f"{func.__name__}_duration"] = duration
            st.session_state.metrics['performance'][f"{func.__name__}_memory_delta"] = memory_delta
        
        return result
    return wrapper
```

## 🔒 **Security Configuration**

### **Input Validation**

```python
# src/utils/validation.py
import re
from typing import Optional

def validate_github_url(url: str) -> bool:
    """Validate GitHub repository URL"""
    pattern = r'^https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+/?$'
    return bool(re.match(pattern, url))

def validate_api_key(api_key: str, service: str) -> bool:
    """Validate API key format"""
    if service == 'openai':
        return api_key.startswith('sk-') and len(api_key) > 20
    elif service == 'github':
        return api_key.startswith('ghp_') and len(api_key) > 20
    elif service == 'chromadb':
        return len(api_key) > 30
    return False

def sanitize_input(input_str: str) -> str:
    """Sanitize user input"""
    # Remove potentially dangerous characters
    return re.sub(r'[<>"\']', '', input_str)
```

### **Rate Limiting**

```python
# src/utils/rate_limiting.py
import time
import streamlit as st
from typing import Dict, Any

class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_make_request(self) -> bool:
        """Check if a request can be made"""
        current_time = time.time()
        
        # Remove old requests
        self.requests = [req_time for req_time in self.requests 
                        if current_time - req_time < self.time_window]
        
        # Check if we can make a new request
        if len(self.requests) < self.max_requests:
            self.requests.append(current_time)
            return True
        
        return False
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        while not self.can_make_request():
            time.sleep(1)
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Deployment Failures**
```bash
# Check deployment logs
# In Streamlit Cloud dashboard, go to your app and check the logs

# Common solutions:
# 1. Verify requirements.txt is up to date
# 2. Check environment variables are set correctly
# 3. Ensure main.py exists and is properly formatted
# 4. Verify all dependencies are compatible
```

#### **Performance Issues**
```python
# Monitor memory usage
import psutil
import streamlit as st

def check_memory_usage():
    """Check current memory usage"""
    memory = psutil.virtual_memory()
    st.write(f"Memory usage: {memory.percent}%")
    
    if memory.percent > 80:
        st.warning("High memory usage detected!")
        st.cache_data.clear()  # Clear cache
```

#### **API Rate Limits**
```python
# Handle API rate limits gracefully
def handle_rate_limit(func):
    """Decorator to handle rate limits"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "rate limit" in str(e).lower():
                st.warning("API rate limit reached. Please wait a moment and try again.")
                time.sleep(60)  # Wait 1 minute
                return func(*args, **kwargs)  # Retry
            else:
                raise e
    return wrapper
```

### **Debug Mode**

```python
# Enable debug mode for development
import streamlit as st

if st.secrets.get('DEBUG', False):
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.set_option('deprecation.showfileUploaderEncoding', False)
    
    # Show debug information
    st.sidebar.subheader("🐛 Debug Info")
    st.sidebar.write(f"Session State Keys: {list(st.session_state.keys())}")
    st.sidebar.write(f"System Info: {get_system_info()}")
```

## 📈 **Scaling Considerations**

### **Streamlit Cloud Limits**
- **Memory**: 1GB per app instance
- **CPU**: Shared resources
- **File Upload**: 200MB max
- **Concurrent Users**: Auto-scaling based on demand

### **Optimization Strategies**
1. **Efficient Caching**: Use `@st.cache_data` and `@st.cache_resource`
2. **External Processing**: Offload heavy tasks to external services
3. **Lazy Loading**: Load data only when needed
4. **Connection Pooling**: Reuse database connections
5. **Batch Processing**: Process multiple items together

### **Monitoring Scaling**
```python
# Monitor app scaling
def check_app_health():
    """Check app health and scaling status"""
    system_info = get_system_info()
    
    if system_info['memory_usage'] > 80:
        st.warning("High memory usage - consider optimization")
    
    if system_info['cpu_usage'] > 80:
        st.warning("High CPU usage - consider caching")
    
    return system_info
```

This comprehensive deployment guide ensures successful deployment and optimal performance of the System-Reference application on Streamlit Cloud. 