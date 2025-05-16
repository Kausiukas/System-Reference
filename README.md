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

## Overview
This project is a Streamlit-based AI Assistant GUI that uses a vector database (ChromaDB, with Annoy as fallback) and HuggingFace embeddings for document search and retrieval. It supports RAG (Retrieval-Augmented Generation) workflows and integrates with OpenAI for LLM-based responses.

---

## Setup & Installation

1. **Clone the repository**
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   pip install python-dotenv
   ```
3. **Create a `.env` file** in the project root with the following content:
   ```env
   OPENAI_API_KEY=your-openai-key-here
   VECTOR_DB_PATH=D:/DATA/vectorstore
   LOCAL_VECTOR_DB_PATH=D:/GUI/vectorstore
   DATA_DIR=data
   HISTORY_FILE=data/chat_history.json
   ```
   Adjust paths as needed for your environment.

4. **(Optional) Clear HuggingFace cache if you encounter model loading errors:**
   - Delete the folder: `C:/Users/<YourUser>/.cache/huggingface`
   - Or run: `rmdir /s /q %USERPROFILE%\.cache\huggingface`

5. **Run the app:**
   ```sh
   streamlit run app.py
   ```

---

## Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required for LLM features)
- `VECTOR_DB_PATH`: Path to the main vectorstore (ChromaDB persistent storage)
- `LOCAL_VECTOR_DB_PATH`: Path to the local vectorstore (for local testing)
- `DATA_DIR`: Directory for app data (default: `data`)
- `HISTORY_FILE`: Path to chat history file (default: `data/chat_history.json`)

---

## Current Issues & Troubleshooting

### 1. **High Memory Consumption / Slow App Startup**
**Symptoms:**
- App takes a long time to load
- Memory usage spikes (can reach 10GB+)

**Potential Causes:**
- Some vector database backends (or wrappers) may load all documents/embeddings into memory when calling `.get()` or similar methods.
- Sidebar/status code that tries to display document count or dimension by loading all documents instead of using a lightweight stats method.
- Large or corrupted model cache in HuggingFace.
- Multiple clients accessing the same local ChromaDB DB concurrently (can cause locking and memory issues).

**What Has Been Done:**
- The sidebar now uses `get_stats()` for document count and dimension, which is lightweight and does not load all documents.
- Health checks only fetch a single document or use `.count()`/`.info()` if available.
- Embeddings are loaded with `device='cpu'` and only supported arguments.

**Ideas for Further Fixes:**
- Ensure all code (including any wrappers or custom scripts) uses only lightweight methods for stats and health checks.
- Avoid calling `.get()` or any method that loads all documents unless absolutely necessary.
- Profile memory usage with tools like `psutil` or Streamlit's built-in profiler to identify bottlenecks.
- If using custom vector DB backends, implement and use a `get_stats()` or `count()` method.
- Regularly clear the HuggingFace cache if you encounter model loading issues.

### 2. **Model Loading Errors (PyTorch/Meta Tensor)**
- If you see errors like `NotImplementedError: Cannot copy out of meta tensor; no data!`, clear the HuggingFace cache and ensure you are using compatible versions of `torch` and `sentence-transformers`.
- Try switching to a different model (e.g., `all-MiniLM-L6-v2`) if issues persist.

### 3. **ChromaDB Local DB Locking**
- If you see errors about the storage folder being locked, ensure only one instance of the app or client is accessing the local ChromaDB DB at a time.

---

## Logging
- The app writes logs to `app.log` in the project root. Check this file for troubleshooting information.

---

## Contributing & Extending
- Add new environment variables to `.env` as needed.
- Use the `get_stats()` pattern for any new vector DB integrations to keep memory usage low.
- PRs and issues welcome!

## System Architecture

### Module Structure

```
D:/DATA/                    # Main data processing module
├── uploads/               # Raw document storage
├── vectorstore/          # Main vector database storage (ChromaDB format)
└── utils/                # Core database utilities

D:/GUI/                    # GUI application module
├── vectorstore/          # Local vector database cache (ChromaDB format)
├── test_data/            # Test documents
├── data/                 # Application data
└── [application files]   # GUI implementation files
```

### Vector Database Interaction

The system uses two vector database locations:

1. **Main Vectorstore** (`D:/DATA/vectorstore`)
   - Primary storage for document embeddings
   - Uses ChromaDB for vector storage (persistent, disk-backed)
   - Stores all processed documents and their metadata
   - Handles all production data

2. **GUI Vectorstore** (`D:/GUI/vectorstore`)
   - Local cache for the GUI application
   - Contains configuration and metadata
   - Used for development and testing
   - Improves GUI performance

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the DATA module is properly set up:
   - Verify `D:/DATA/vectorstore` exists (ChromaDB format)
   - Check `D:/DATA/utils/db.py` is accessible

## Usage

### Document Processing

1. **Upload Documents**:
```bash
# Place document in test_data folder
python process_and_upload.py
```

2. **Process and Index**:
```bash
# Process document and add to vectorstore
python process_and_index.py
```

### Running the GUI

1. **Launch the Application**:
```bash
streamlit run app.py
```

2. **Using the Interface**:
   - Enter queries in the chat interface
   - View document statistics in the sidebar
   - Upload new documents through the interface
   - Monitor vector database status

## Features

### 1. Document Management
- Upload and process new documents
- Automatic document chunking and indexing
- Metadata management
- Document version control

### 2. Vector Database Operations
- Semantic search capabilities
- Document similarity matching
- Metadata-based filtering
- Real-time indexing

### 3. GUI Features
- Interactive chat interface
- Document visualization
- Search result scoring
- Real-time status monitoring

## Vector Database Integration

### How It Works

1. **Document Processing Flow**:
   ```
   Document → Upload → Chunking → Embedding → Vectorstore
   ```
   - Documents are uploaded to `D:/DATA/uploads`
   - Processed and chunked by `process_and_index.py`
   - Embeddings stored in main vectorstore (ChromaDB)
   - Metadata maintained for retrieval

2. **Query Processing Flow**:
   ```
   Query → Embedding → Vector Search → Result Retrieval → Response
   ```
   - User query is converted to embedding
   - Similar documents retrieved from vectorstore
   - Results processed and formatted
   - Response generated with context

### Database Inspection Tools

The project includes tools for inspecting and analyzing the vector database:

1. **ChromaDB Inspector** (`inspect_chromadb.py`):
   - Analyzes the structure and content of the ChromaDB database
   - Provides detailed statistics about collections and documents
   - Features:
     - Collection-level document counts
     - Metadata analysis (filetypes, categories, sources)
     - Sample document inspection
     - SQLite database analysis for the communications collection
   - Usage:
     ```bash
     python inspect_chromadb.py
     ```
   - Output includes:
     - Total document counts per collection
     - Distribution of filetypes and categories
     - Top sources of documents
     - Sample metadata entries
     - Example document content

### Vector Database Types

The system supports multiple vector database backends:

1. **ChromaDB** (Primary)
   - Persistent storage
   - Efficient similarity search
   - Metadata filtering
   - Collection management

2. **Annoy** (Fallback)
   - Fast approximate nearest neighbor search
   - Lightweight implementation
   - Used when ChromaDB is unavailable

> **Note:**
> Previous documentation and some comments may reference Qdrant. The current implementation does not use Qdrant. All storage and search operations are handled by ChromaDB (or Annoy as fallback). If you wish to add Qdrant support, you will need to implement and test it separately.

## Development

### Testing

1. **Unit Tests**:
```bash
python -m unittest test_app.py
python -m unittest test_vector_db.py
```

2. **Integration Tests**:
```bash
python -m unittest test_integration.py
```

### Adding New Features

1. **Document Processing**:
   - Add new processors in `process_and_index.py`
   - Update chunking logic as needed
   - Modify metadata handling

2. **GUI Components**:
   - Extend `app.py` with new features
   - Add visualization components
   - Implement new search capabilities

## Best Practices

- Use ChromaDB for persistent, production-grade vector storage.
- Use Annoy for lightweight, local, or fallback scenarios.
- Avoid concurrent access to the same ChromaDB local DB from multiple processes.
- Use `get_stats()` or similar lightweight methods for status and health checks.
- Regularly clear model caches if you encounter memory or loading issues.

## Troubleshooting

### Common Issues

1. **Vector Database Connection**:
   - Verify paths in configuration
   - Check database permissions
   - Ensure proper initialization

2. **Document Processing**:
   - Check file permissions
   - Verify chunking parameters
   - Monitor processing logs

3. **GUI Issues**:
   - Clear browser cache
   - Restart Streamlit server
   - Check session state

## Contributing

1. Follow the established code structure
2. Add appropriate tests
3. Update documentation
4. Submit pull requests

## License

[Add your license information here]

## FAISS Product Quantization (PQ) Compression

### What is PQ Compression?
Product Quantization (PQ) is a technique in FAISS that compresses high-dimensional vectors into compact codes, significantly reducing index size and memory usage with a small trade-off in search accuracy. This is especially useful for large-scale vector databases.

### How to Enable PQ Compression
To use PQ compression in the vector store, initialize `FAISSVectorDB` with `use_pq=True` and specify the number of sub-vectors (`m`) and bits per sub-quantizer (`nbits`).

#### Example Usage
```python
from vector_db import FAISSVectorDB

db = FAISSVectorDB(db_path="D:/DATA/vectorstore_pq", use_pq=True, m=8, nbits=8)
db.add_documents(["example text 1", "example text 2"])
results = db.search("example query")
print(results)
```

- `m`: Number of sub-vectors (must divide the embedding dimension, e.g., 8 for 384-dim vectors)
- `nbits`: Number of bits per sub-quantizer (1-8, higher means less compression, more accuracy)

### Trade-offs
- **Index size**: PQ can reduce index size by 2x or more.
- **Accuracy**: Slightly lower than flat (uncompressed) FAISS, but often acceptable for large-scale search.
- **Training**: PQ requires more training vectors than the number of centroids (m*256). For best results, use at least 10,000 training vectors.

### Evaluation Results
- On 1,000 documents (dim=384):
  - PQ index size: 0.92MB (vs. 2.01MB for flat FAISS)
  - Accuracy: 0.4689 (vs. 0.4727 for flat FAISS)
  - Add time: ~10.5s
  - Search time: ~0.012s/query

See `memory_optimization_checklist.md` for more details and recommendations. 