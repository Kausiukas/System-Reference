import sys
import os
import importlib.util
import unittest
import shutil
from pathlib import Path
import numpy as np

# Load db.py from DATA/utils
utils_db_path = os.path.abspath('../DATA/utils/db.py')
spec = importlib.util.spec_from_file_location('db', utils_db_path)
db = importlib.util.module_from_spec(spec)
sys.modules['db'] = db
spec.loader.exec_module(db)
get_vector_db = db.get_vector_db

class TestVectorDB(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.vector_db = get_vector_db()

    def tearDown(self):
        self.vector_db = None

    def test_initialization(self):
        self.assertIsNotNone(self.vector_db)

    def test_add_and_search_documents(self):
        # Add and search documents using Qdrant
        from langchain.schema import Document
        docs = [Document(page_content="This is a test document about AI."),
                Document(page_content="Machine learning is a subset of AI."),
                Document(page_content="Deep learning uses neural networks.")]
        self.vector_db.add_documents(docs)
        results = db.search_documents(self.vector_db, "AI", k=2)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)
        if results:
            self.assertTrue(hasattr(results[0], 'page_content'))

if __name__ == '__main__':
    unittest.main() 