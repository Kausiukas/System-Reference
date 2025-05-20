# Getting Started with AI Assistant GUI

This guide will help you get up and running with the AI Assistant GUI quickly.

## Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key
- 4GB RAM minimum (8GB recommended)
- 1GB free disk space

## Installation

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

## Configuration

1. Create a `.env` file in the project root:
```env
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Vector Database Paths
VECTOR_DB_PATH=path/to/vectorstore
LOCAL_VECTOR_DB_PATH=path/to/local/vectorstore

# Application Data
DATA_DIR=data
HISTORY_FILE=data/chat_history.json

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=app.log

# Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
MAX_TOKENS=2000
```

2. Create necessary directories:
```bash
mkdir -p data vectorstore
```

## Quick Start Guide

1. **Start the Application**:
```bash
streamlit run app.py
```

2. **Access the Web Interface**:
   - Open your browser and navigate to `http://localhost:8501`
   - You should see the main dashboard

3. **Basic Usage**:
   - Select your preferred AI agent from the sidebar
   - Upload or select documents for analysis
   - Use the chat interface to interact with the AI
   - View and manage checklists
   - Monitor system metrics

## First Steps

1. **Upload a Document**:
   - Click "Upload Document" in the sidebar
   - Select a file (supported formats: PDF, TXT, MD, DOCX)
   - Wait for processing to complete

2. **Try a Sample Query**:
   - Type "Analyze the uploaded document" in the chat
   - Review the AI's response and suggestions

3. **Create a Checklist**:
   - Navigate to the Checklist tab
   - Click "New Checklist"
   - Add tasks and subtasks
   - Set priorities and deadlines

4. **Monitor Performance**:
   - Check the Metrics tab
   - Review system performance
   - Monitor resource usage

## Common Issues

1. **Memory Usage**:
   - If you encounter high memory usage, try:
     - Clearing the HuggingFace cache
     - Reducing the chunk size in configuration
     - Using a smaller embedding model

2. **Model Loading Errors**:
   - Clear the HuggingFace cache:
     ```bash
     rm -rf ~/.cache/huggingface  # Linux/Mac
     rmdir /s /q %USERPROFILE%\.cache\huggingface  # Windows
     ```

3. **Database Locking**:
   - Ensure only one instance is running
   - Check file permissions
   - Clear lock files if needed

## Next Steps

- Read the [User Guide](user_guide.md) for detailed usage instructions
- Check the [API Reference](api.md) for development information
- Review [Best Practices](best_practices.md) for optimal usage
- Join the [Community](community.md) for support and updates 