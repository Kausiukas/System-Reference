import unittest
import os
import numpy as np
from memory_efficient_storage import (
    create_pq_index,
    evaluate_pq_compression,
    plot_pq_evaluation,
    evaluate_faiss
)
import faiss

class TestMemoryEfficientStorage(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.dimension = 128
        self.num_vectors = 1000
        self.vectors = np.random.rand(self.num_vectors, self.dimension).astype('float32')

    def test_create_pq_index(self):
        """Test PQ index creation with different parameters."""
        # Test valid parameters
        m = 8
        nbits = 8
        index, metadata = create_pq_index(self.dimension, self.num_vectors, m, nbits)
        
        self.assertIsInstance(index, faiss.IndexPQ)
        self.assertEqual(index.d, self.dimension)
        self.assertEqual(index.m, m)
        self.assertEqual(index.nbits, nbits)
        
        # Test metadata
        self.assertIn('compression_ratio', metadata)
        self.assertIn('original_size_bytes', metadata)
        self.assertIn('compressed_size_bytes', metadata)
        
        # Test invalid parameters
        with self.assertRaises(ValueError):
            create_pq_index(self.dimension, self.num_vectors, m=7)  # m must divide dimension

    def test_evaluate_pq_compression(self):
        """Test PQ compression evaluation with different settings."""
        results = evaluate_pq_compression(
            self.vectors,
            m_values=[4, 8],
            nbits_values=[4, 8]
        )
        
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)
        
        # Check result structure
        for key, data in results.items():
            self.assertIn('compression_ratio', data)
            self.assertIn('accuracy', data)
            self.assertIn('search_time', data)
            self.assertIn('train_time', data)
            self.assertIn('add_time', data)

    def test_plot_pq_evaluation(self):
        """Test plotting of PQ evaluation results."""
        results = evaluate_pq_compression(
            self.vectors,
            m_values=[4, 8],
            nbits_values=[4, 8]
        )
        
        plot_path = "test_pq_evaluation.png"
        plot_pq_evaluation(results, save_path=plot_path)
        
        self.assertTrue(os.path.exists(plot_path))
        os.remove(plot_path)  # Clean up

    def test_evaluate_faiss(self):
        """Test FAISS evaluation with memory mapping."""
        evaluate_faiss(dimension=64, num_vectors=100)
        self.assertTrue(os.path.exists("faiss_index.bin"))
        os.remove("faiss_index.bin")  # Clean up

    def test_pq_compression_accuracy(self):
        """Test that PQ compression maintains reasonable accuracy."""
        # Create and train PQ index
        index, _ = create_pq_index(self.dimension, self.num_vectors, m=8, nbits=8)
        index.train(self.vectors)
        index.add(self.vectors)
        
        # Search for nearest neighbors
        D, I = index.search(self.vectors[:5], 5)
        
        # Check that vectors find themselves (high accuracy)
        for i in range(5):
            self.assertIn(i, I[i])

    def test_flat_index(self):
        """Test flat (uncompressed) FAISS index for accuracy and speed."""
        vectors = np.random.rand(10000, 64).astype('float32')
        index_flat = faiss.IndexFlatL2(64)
        index_flat.add(vectors)
        D, I = index_flat.search(vectors[:5], 5)
        # Check if the index is valid and returns expected shape
        self.assertIsNotNone(index_flat)
        self.assertEqual(I.shape, (5, 5))

if __name__ == '__main__':
    unittest.main() 