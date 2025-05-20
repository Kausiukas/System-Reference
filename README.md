# Multi-Agent AI Assistant System (Current State)

This project is a robust, extensible multi-agent AI assistant platform with:
- **Multi-agent support:** Switch between CodexAgent (chain-of-thought, local/cloud hybrid) and LLMAssistant (classic logic) from the UI.
- **Checklist management:** Interactive checklist tab with support for multiple checklists, progress tracking, and evaluation dashboard.
- **Metrics dashboard:** Real-time dashboard with per-metric status indicators, data freshness checks, and error handling for all logging sources.
- **Logging infrastructure:** Modular logging for system, app, LLM, profiling, memory, and aggregated logs. Includes documentation and troubleshooting guides.
- **Automated health checks:** Integrated health checks in the app and a standalone/background watchdog script to monitor and auto-restart logging processes.
- **Local knowledge base:** Sidebar UI for semantic search, file context, and reindexing of project files.
- **Extensive documentation:** Up-to-date docs for logging, metrics, health checks, and maintenance.

The system is designed for reliability, maintainability, and easy monitoring, with a focus on hybrid local/cloud LLM processing, robust error handling, and user-friendly dashboards.

---

# Memory-Optimized Vector Database System

A comprehensive system for memory optimization and performance monitoring in AI-powered vector databases.

## Features

- Memory optimization through FAISS PQ compression
- Real-time performance monitoring and metrics tracking
- Automated maintenance and self-healing capabilities
- Comprehensive testing and validation
- Interactive dashboard for system management

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/TuringCollegeSubmissions/avalci-AE.3.5.git
cd avalci-AE.3.5
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the monitoring dashboard:
```bash
streamlit run metrics_dashboard.py
```

2. Run system validation:
```bash
python system_validation.py
```

3. Run tests:
```bash
pytest
```

## Documentation

- [Project Overview](PROJECT_OVERVIEW.md)
- [Handover Report](HANDOVER_REPORT.md)
- [Maintenance Guide](MAINTENANCE_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Profiling Guide](PROFILING_GUIDE.md)

## Project Structure

```
.
├── app.py                    # Main application
├── metrics_dashboard.py      # Streamlit dashboard
├── vector_db.py             # Vector database implementation
├── model_loader.py          # Memory-efficient model loading
├── metrics_tracker.py       # System metrics tracking
├── auto_recovery.py         # Self-healing mechanisms
├── scheduled_maintenance.py # Automated maintenance
└── tests/                   # Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FAISS library for vector similarity search
- Streamlit for the dashboard interface
- LangChain for agent implementation

# AI Assistant GUI

A powerful, multi-agent AI assistant platform with local knowledge base integration, interactive checklists, and real-time metrics monitoring.

## Features

### Core Capabilities
- **Multi-Agent Support**: Switch between different AI agents:
  - CodexAgent: Chain-of-thought reasoning with local/cloud hybrid processing
  - LLMAssistant: Classic logic-based assistance
- **Local Knowledge Base**: 
  - Semantic search across project files
  - Automatic file indexing and reindexing
  - Context-aware document retrieval
  - Support for multiple file types (Python, Markdown, Text, JSON)
- **Interactive Checklists**:
  - Multiple checklist management
  - Progress tracking
  - Evaluation dashboard
  - Task prioritization

### Monitoring & Management
- **Real-time Metrics Dashboard**:
  - Per-metric status indicators
  - Data freshness monitoring
  - Error tracking
  - Performance analytics
- **Comprehensive Logging**:
  - System logs
  - Application logs
  - LLM interaction logs
  - Profiling data
  - Memory usage tracking
- **Health Monitoring**:
  - Automated health checks
  - Process monitoring
  - Auto-recovery capabilities
  - System status dashboard

## Installation

### Prerequisites
- Python 3.8+
- Git
- OpenAI API key

### Option 1: Using `uv` (Recommended)
```bash
# Install uv if you haven't already
pip install uv

# Clone the repository
git clone https://github.com/yourusername/ai-assistant-gui.git
cd ai-assistant-gui

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Option 2: Using `poetry`
```bash
# Install poetry if you haven't already
pip install poetry

# Clone and setup
git clone https://github.com/yourusername/ai-assistant-gui.git
cd ai-assistant-gui
poetry install
```

### Option 3: Using `pip`
```bash
git clone https://github.com/yourusername/ai-assistant-gui.git
cd ai-assistant-gui
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Setup
1. Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your-openai-key-here
VECTOR_DB_PATH=path/to/vectorstore
LOCAL_VECTOR_DB_PATH=path/to/local/vectorstore
DATA_DIR=data
HISTORY_FILE=data/chat_history.json
```

## Usage

### Launching the Application
```bash
streamlit run app.py
```

### Navigating the Interface
1. **Main Chat Interface**:
   - Select your preferred AI agent from the sidebar
   - Type your query in the chat input
   - View responses and follow-up suggestions

2. **Knowledge Base**:
   - Access the local knowledge base from the sidebar
   - Search across indexed files
   - View file context and metadata
   - Trigger reindexing when needed

3. **Checklist Management**:
   - Create and manage multiple checklists
   - Track progress on tasks
   - View completion statistics
   - Export checklist data

4. **Metrics Dashboard**:
   - Monitor system performance
   - Track memory usage
   - View error rates and logs
   - Check data freshness

### Sample Queries
1. **Code Analysis**:
   ```
   "Analyze the performance of the vector database implementation"
   "Find all references to the logging system in the codebase"
   ```

2. **Documentation**:
   ```
   "Generate documentation for the checklist management system"
   "Summarize the main features of the knowledge base"
   ```

3. **Task Management**:
   ```
   "Create a checklist for implementing the new feature"
   "Track progress on the current sprint tasks"
   ```

## System Prompt Customization

The system supports customization of AI agent behavior through prompt templates:

1. **Agent Selection**:
   - Choose between different agent personalities
   - Customize response styles
   - Set specific task focuses

2. **Context Management**:
   - Adjust context window size
   - Modify relevance thresholds
   - Configure memory retention

3. **Response Formatting**:
   - Define output structures
   - Set formatting preferences
   - Configure language style

## Example Inputs and Outputs

### Example 1: Code Analysis
**Input**:
```
"Analyze the vector database implementation for potential optimizations"
```

**Output**:
```
Analysis Results:
1. Current Implementation:
   - Using ChromaDB with FAISS backend
   - PQ compression enabled
   - Batch processing implemented

2. Optimization Opportunities:
   - Implement caching for frequent queries
   - Add parallel processing for large datasets
   - Optimize index parameters

3. Recommended Actions:
   - [ ] Implement query caching
   - [ ] Add batch processing optimization
   - [ ] Profile memory usage
```

### Example 2: Documentation Generation
**Input**:
```
"Generate API documentation for the knowledge base search function"
```

**Output**:
```
# Knowledge Base Search API

## Function: search(query: str, n_results: int = 5) -> List[Dict[str, Any]]

### Parameters:
- query (str): Search query string
- n_results (int): Number of results to return (default: 5)

### Returns:
List of dictionaries containing:
- content: Retrieved text content
- file_path: Source file path
- chunk_index: Position in source file
- similarity: Relevance score

### Example Usage:
```python
results = kb.search("vector database implementation", n_results=3)
for result in results:
    print(f"File: {result['file_path']}")
    print(f"Content: {result['content'][:200]}...")
```
```

## Troubleshooting

### Common Issues
1. **High Memory Usage**:
   - Clear HuggingFace cache
   - Use lightweight stats methods
   - Monitor concurrent DB access

2. **Model Loading Errors**:
   - Clear HuggingFace cache
   - Check PyTorch compatibility
   - Try alternative models

3. **Database Locking**:
   - Ensure single instance access
   - Check file permissions
   - Clear lock files if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Business Case Agent

A modular, AI-powered agent for analyzing business cases and generating actionable insights. The system processes documents, enriches context through vector stores and web search, and provides comprehensive analysis with task tracking and metrics.

## Features

- **Document Processing**: Support for multiple file formats (TXT, PDF, DOCX, MD)
- **Context Enrichment**: Integration with vector stores and web search
- **AI Analysis**: Multi-step analysis pipeline with customizable prompts
- **Task Management**: Automated checklist generation with dependencies
- **Metrics Tracking**: Comprehensive performance and quality metrics
- **User Interface**: Streamlit-based web interface with visualization

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/business-case-agent.git
cd business-case-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Access the web interface at `http://localhost:8501`

3. Upload a business case document and click "Analyze Document"

4. View results in the organized tabs:
   - Analysis: Document summary, key parties, situation, problem, and recommendations
   - Checklist: Generated tasks with dependencies and progress tracking
   - Context: Enriched context from vector stores and web search
   - Metrics: Performance and quality metrics with visualizations

## Architecture

The system consists of several key components:

1. **BusinessCaseAgent**: Core agent class handling document processing and analysis
2. **AIAssistant**: Manages AI model interactions and prompt processing
3. **LocalKnowledgeBase**: Handles vector store operations and document storage
4. **MetricsTracker**: Tracks performance and quality metrics
5. **Streamlit UI**: Web interface for user interaction

## Configuration

The system can be configured through environment variables or a configuration file:

```python
# .env
OPENAI_API_KEY=your_api_key
VECTOR_DB_PATH=path/to/vector/db
MAX_DOCUMENT_SIZE=10485760  # 10MB
```

## Development

### Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run specific test suite
python -m unittest tests/test_business_case_agent.py
python -m unittest tests/test_business_case_agent_performance.py
python -m unittest tests/test_business_case_agent_ui.py
```

### Code Style

The project follows PEP 8 style guidelines. Use the provided tools to maintain code quality:

```bash
# Run linter
flake8 .

# Run type checker
mypy .

# Run formatter
black .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/yourusername/business-case-agent/issues)
3. Create a new issue if needed

## Acknowledgments

- OpenAI for AI capabilities
- Streamlit for the web interface
- All contributors to the project 