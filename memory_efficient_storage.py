import faiss
import numpy as np
import time
import logging
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_pq_index(dimension: int, num_vectors: int, m: int = 8, nbits: int = 8) -> Tuple[faiss.Index, Dict[str, Any]]:
    """
    Create a FAISS Product Quantization (PQ) index.
    
    Args:
        dimension: Vector dimension
        num_vectors: Number of vectors to index
        m: Number of sub-vectors (must divide dimension)
        nbits: Number of bits per sub-quantizer (1-8)
    
    Returns:
        Tuple of (index, metadata)
    """
    # Ensure dimension is divisible by m
    if dimension % m != 0:
        raise ValueError(f"Dimension {dimension} must be divisible by m={m}")
    
    # Create the PQ index
    index = faiss.IndexPQ(dimension, m, nbits)
    
    # Calculate compression ratio and memory usage
    original_size = dimension * 4  # float32 = 4 bytes
    compressed_size = m * nbits / 8  # bits to bytes
    compression_ratio = original_size / compressed_size
    
    metadata = {
        'dimension': dimension,
        'm': m,
        'nbits': nbits,
        'compression_ratio': compression_ratio,
        'original_size_bytes': original_size,
        'compressed_size_bytes': compressed_size
    }
    
    return index, metadata

def evaluate_pq_compression(vectors: np.ndarray, 
                          m_values: list = [4, 8, 16], 
                          nbits_values: list = [4, 8]) -> Dict[str, Any]:
    """
    Evaluate different PQ compression settings.
    
    Args:
        vectors: Input vectors to compress
        m_values: List of sub-vector counts to try
        nbits_values: List of bits per sub-quantizer to try
    
    Returns:
        Dictionary with evaluation results
    """
    dimension = vectors.shape[1]
    results = {}
    
    for m in m_values:
        if dimension % m != 0:
            logger.warning(f"Skipping m={m} as it doesn't divide dimension {dimension}")
            continue
            
        for nbits in nbits_values:
            try:
                # Create and train PQ index
                index, metadata = create_pq_index(dimension, len(vectors), m, nbits)
                
                # Train the index
                start_time = time.time()
                index.train(vectors)
                train_time = time.time() - start_time
                
                # Add vectors
                start_time = time.time()
                index.add(vectors)
                add_time = time.time() - start_time
                
                # Test search performance
                start_time = time.time()
                D, I = index.search(vectors[:5], 5)  # Search for 5 nearest neighbors
                search_time = time.time() - start_time
                
                # Calculate accuracy (using first 5 vectors as queries)
                correct = 0
                for i in range(5):
                    if i in I[i]:  # Check if vector finds itself
                        correct += 1
                accuracy = correct / 5
                
                results[f"m{m}_nbits{nbits}"] = {
                    **metadata,
                    'train_time': train_time,
                    'add_time': add_time,
                    'search_time': search_time,
                    'accuracy': accuracy
                }
                
            except Exception as e:
                logger.error(f"Error evaluating m={m}, nbits={nbits}: {e}")
                continue
    
    return results

def plot_pq_evaluation(results: Dict[str, Any], save_path: str = "pq_evaluation.png"):
    """Plot PQ compression evaluation results."""
    # Prepare data for plotting
    m_values = []
    nbits_values = []
    compression_ratios = []
    accuracies = []
    search_times = []
    
    for key, data in results.items():
        m_values.append(data['m'])
        nbits_values.append(data['nbits'])
        compression_ratios.append(data['compression_ratio'])
        accuracies.append(data['accuracy'])
        search_times.append(data['search_time'])
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot compression ratio vs accuracy
    scatter1 = ax1.scatter(compression_ratios, accuracies, c=nbits_values, cmap='viridis')
    ax1.set_xlabel('Compression Ratio')
    ax1.set_ylabel('Accuracy')
    ax1.set_title('Compression Ratio vs Accuracy')
    plt.colorbar(scatter1, ax=ax1, label='Bits per sub-quantizer')
    
    # Plot compression ratio vs search time
    scatter2 = ax2.scatter(compression_ratios, search_times, c=nbits_values, cmap='viridis')
    ax2.set_xlabel('Compression Ratio')
    ax2.set_ylabel('Search Time (s)')
    ax2.set_title('Compression Ratio vs Search Time')
    plt.colorbar(scatter2, ax=ax2, label='Bits per sub-quantizer')
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def evaluate_faiss(dimension: int = 128, num_vectors: int = 1000):
    """Evaluate FAISS implementation with memory mapping."""
    # Generate random vectors
    vectors = np.random.rand(num_vectors, dimension).astype('float32')
    
    # Create FAISS index
    index = faiss.IndexFlatL2(dimension)
    
    # Add vectors to the index
    index.add(vectors)
    
    # Test memory mapping
    start_time = time.time()
    # Save the index to disk
    faiss.write_index(index, "faiss_index.bin")
    # Load the index from disk with memory mapping
    index_mm = faiss.read_index("faiss_index.bin", faiss.IO_FLAG_MMAP)
    end_time = time.time()
    
    logger.info(f"Memory mapping load time: {end_time - start_time:.2f} seconds")
    
    # Compare performance
    start_time = time.time()
    # Perform a search
    D, I = index_mm.search(vectors[:5], 5)
    end_time = time.time()
    
    logger.info(f"Search time: {end_time - start_time:.2f} seconds")
    logger.info(f"Search results: {I}")

def evaluate_dataset(vectors: np.ndarray):
    """Evaluate dataset properties for compression."""
    # Calculate basic statistics
    mean = np.mean(vectors)
    std = np.std(vectors)
    min_val = np.min(vectors)
    max_val = np.max(vectors)
    
    logger.info(f"Dataset statistics:")
    logger.info(f"Mean: {mean:.4f}")
    logger.info(f"Std: {std:.4f}")
    logger.info(f"Min: {min_val:.4f}")
    logger.info(f"Max: {max_val:.4f}")
    
    # Plot distribution
    plt.figure(figsize=(10, 6))
    plt.hist(vectors.flatten(), bins=50)
    plt.title("Vector Value Distribution")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.savefig("vector_distribution.png")
    plt.close()

if __name__ == "__main__":
    # Generate test vectors
    dimension = 128
    num_vectors = 10000
    vectors = np.random.rand(num_vectors, dimension).astype('float32')
    
    # Evaluate PQ compression
    logger.info("Evaluating PQ compression...")
    results = evaluate_pq_compression(vectors)
    
    # Plot results
    plot_pq_evaluation(results)
    
    # Print summary
    logger.info("\nPQ Compression Evaluation Summary:")
    for key, data in results.items():
        logger.info(f"\nConfiguration {key}:")
        logger.info(f"Compression ratio: {data['compression_ratio']:.2f}x")
        logger.info(f"Accuracy: {data['accuracy']:.2f}")
        logger.info(f"Search time: {data['search_time']:.4f}s")
    
    # Evaluate dataset properties
    logger.info("\nEvaluating dataset properties...")
    evaluate_dataset(vectors) 