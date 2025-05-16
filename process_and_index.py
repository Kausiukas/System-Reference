import os
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import sys
import importlib.util

# Load db.py from DATA/utils
utils_db_path = os.path.abspath('../DATA/utils/db.py')
spec = importlib.util.spec_from_file_location('db', utils_db_path)
db = importlib.util.module_from_spec(spec)
sys.modules['db'] = db
spec.loader.exec_module(db)
get_vector_db = db.get_vector_db

def process_and_index_file():
    # Initialize vector database
    vector_db = get_vector_db()
    
    # Read the test file
    file_path = "D:/DATA/uploads/sample_document.txt"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content into chunks (simple paragraph-based splitting)
    chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
    
    # Add documents to vector store
    metadata = [{"source": "sample_document.txt", "chunk_index": i} for i in range(len(chunks))]
    vector_db.add_documents(chunks, metadata)
    
    print(f"Successfully processed and indexed {len(chunks)} chunks from the test file")
    return True

if __name__ == "__main__":
    process_and_index_file() 