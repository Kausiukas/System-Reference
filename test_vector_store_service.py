import unittest
from fastapi.testclient import TestClient
from vector_store_service import app
from unittest.mock import patch, MagicMock

class TestVectorStoreService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Mock the ChromaDB client and collection
        self.patcher = patch('vector_store_service.client')
        self.mock_client = self.patcher.start()
        self.mock_collection = MagicMock()
        self.mock_client.get_or_create_collection.return_value = self.mock_collection
        self.mock_collection.count.return_value = 0
        self.mock_collection.query.return_value = {"results": ["result1", "result2"]}

    def tearDown(self):
        self.patcher.stop()

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_search(self):
        """Test the search endpoint."""
        response = self.client.post("/search", json={"query": "test query"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.json())
        self.mock_collection.add.assert_called_once()
        self.mock_collection.query.assert_called_once()

    def test_recover(self):
        """Test the recovery endpoint."""
        response = self.client.post("/recover")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "recovered"})

    def test_search_degraded_mode(self):
        """Test search in degraded mode."""
        # Mock heartbeat to raise an exception
        self.mock_client.heartbeat.side_effect = Exception("ChromaDB heartbeat failed")
        
        # Set degraded mode
        self.client.get("/health")  # This will set degraded mode to True
        response = self.client.post("/search", json={"query": "test query"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Service in degraded mode"})

if __name__ == "__main__":
    unittest.main() 