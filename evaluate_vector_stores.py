import os
import time
import logging
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import psutil
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing ChromaDB
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available. Skipping ChromaDB evaluation.")

from vector_db import FAISSVectorDB, AnnoyVectorDB, ChromaVectorDB

def generate_test_data(num_docs: int = 1000, doc_length: int = 100) -> tuple[List[str], List[str]]:
    """Generate random test documents and queries."""
    documents = [
        f"This is test document {i} with some random content. " * (doc_length // 10)
        for i in range(num_docs)
    ]
    queries = [
        f"Query about document {i}" for i in range(10)
    ]
    return documents, queries

def evaluate_vector_store(
    vector_store: Any,
    documents: List[str],
    queries: List[str],
    db_path: str
) -> Dict[str, Any]:
    """Evaluate a vector store's performance."""
    results = {}
    
    # Measure addition time
    start_time = time.time()
    vector_store.add_documents(documents)
    results['add_time'] = time.time() - start_time
    
    # Measure search time and accuracy
    search_times = []
    accuracies = []
    
    for query in queries:
        start_time = time.time()
        results_list = vector_store.search(query, k=5)
        search_times.append(time.time() - start_time)
        
        # Calculate accuracy (simplified - assumes first result is correct)
        if results_list:
            accuracies.append(results_list[0]['score'])
    
    results['avg_search_time'] = np.mean(search_times)
    results['accuracy'] = np.mean(accuracies)
    
    # Measure memory usage
    process = psutil.Process()
    results['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
    
    # Measure index size
    if os.path.exists(db_path):
        results['index_size'] = sum(
            os.path.getsize(os.path.join(db_path, f))
            for f in os.listdir(db_path)
        ) / 1024 / 1024  # MB
    
    return results

def compare_vector_stores() -> Dict[str, Any]:
    """Compare different vector store implementations."""
    logger.info("Starting vector store comparison...")
    
    # Generate test data
    documents, queries = generate_test_data()
    
    # Define configurations to test
    configs = [
        {
            'name': 'FAISS (PQ)',
            'class': FAISSVectorDB,
            'params': {'use_pq': True, 'm': 8, 'nbits': 8}
        },
        {
            'name': 'FAISS (No PQ)',
            'class': FAISSVectorDB,
            'params': {'use_pq': False}
        },
        {
            'name': 'Annoy',
            'class': AnnoyVectorDB,
            'params': {}
        }
    ]
    
    if CHROMA_AVAILABLE:
        configs.append({
            'name': 'ChromaDB',
            'class': ChromaVectorDB,
            'params': {}
        })
    
    results = {}
    
    for config in configs:
        logger.info(f"Testing {config['name']}...")
        
        # Create unique path for each configuration
        db_path = f"D:/DATA/eval/{config['name'].lower().replace(' ', '_')}"
        os.makedirs(db_path, exist_ok=True)
        
        try:
            # Initialize vector store
            vector_store = config['class'](db_path=db_path, **config['params'])
            
            # Evaluate performance
            config_results = evaluate_vector_store(vector_store, documents, queries, db_path)
            results[config['name']] = config_results
            
            # Clean up
            del vector_store
            gc.collect()
            
        except Exception as e:
            logger.error(f"Error testing {config['name']}: {str(e)}")
            results[config['name']] = {'error': str(e)}
        
        finally:
            # Clean up database files
            try:
                for file in os.listdir(db_path):
                    os.remove(os.path.join(db_path, file))
                os.rmdir(db_path)
            except Exception as e:
                logger.warning(f"Error cleaning up {db_path}: {str(e)}")
    
    # Save results
    results_path = "D:/DATA/eval/results.json"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    return results

if __name__ == "__main__":
    results = compare_vector_stores()
    
    # Print summary
    print("\nVector Store Comparison Results:")
    print("-" * 50)
    for name, metrics in results.items():
        print(f"\n{name}:")
        if 'error' in metrics:
            print(f"  Error: {metrics['error']}")
        else:
            print(f"  Add Time: {metrics['add_time']:.2f}s")
            print(f"  Avg Search Time: {metrics['avg_search_time']:.4f}s")
            print(f"  Memory Usage: {metrics['memory_usage']:.2f}MB")
            print(f"  Index Size: {metrics['index_size']:.2f}MB")
            print(f"  Accuracy: {metrics['accuracy']:.4f}") 