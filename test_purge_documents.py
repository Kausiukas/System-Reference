import unittest
import os
import shutil
import datetime
from vector_db import FAISSVectorDB, AnnoyVectorDB

# Try to import ChromaVectorDB if available
try:
    from vector_db import ChromaVectorDB
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

def make_docs(num, start_days_ago=10, obsolete_every=3):
    docs = []
    today = datetime.datetime.now()
    for i in range(num):
        created_at = (today - datetime.timedelta(days=start_days_ago - i)).isoformat()
        meta = {"created_at": created_at}
        if i % obsolete_every == 0:
            meta["obsolete"] = True
        docs.append({
            "text": f"Document {i}",
            "metadata": meta
        })
    return docs

class TestPurgeDocuments(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_vectorstore"
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)
        os.makedirs(self.db_path, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)

    def test_faiss_purge(self):
        db = FAISSVectorDB(db_path=self.db_path, use_pq=False)
        docs = make_docs(10)
        db.add_documents([d["text"] for d in docs], [d["metadata"] for d in docs])
        # Purge by age (older than 5 days)
        db.purge_documents(older_than_days=5)
        self.assertTrue(all((datetime.datetime.now() - datetime.datetime.fromisoformat(doc["metadata"]["created_at"])) .days <= 5 for doc in db.documents))
        # Purge by metadata
        db.purge_documents(metadata_filter={"obsolete": True})
        self.assertTrue(all(not doc["metadata"].get("obsolete", False) for doc in db.documents))
        # Purge to keep only 2 most recent
        db.purge_documents(keep_recent=2)
        self.assertEqual(len(db.documents), 2)
        print("FAISS purge test passed. Remaining docs:", [doc["text"] for doc in db.documents])

    def test_annoy_purge(self):
        db = AnnoyVectorDB(db_path=self.db_path)
        docs = make_docs(10)
        db.add_documents([d["text"] for d in docs], [d["metadata"] for d in docs])
        db.purge_documents(older_than_days=5)
        self.assertTrue(all((datetime.datetime.now() - datetime.datetime.fromisoformat(doc["metadata"]["created_at"])) .days <= 5 for doc in db.documents))
        db.purge_documents(metadata_filter={"obsolete": True})
        self.assertTrue(all(not doc["metadata"].get("obsolete", False) for doc in db.documents))
        db.purge_documents(keep_recent=2)
        self.assertEqual(len(db.documents), 2)
        print("Annoy purge test passed. Remaining docs:", [doc["text"] for doc in db.documents])

    @unittest.skipUnless(CHROMA_AVAILABLE, "ChromaDB not available")
    def test_chroma_purge(self):
        db = ChromaVectorDB(db_path=self.db_path)
        docs = make_docs(10)
        db.add_documents([d["text"] for d in docs], [d["metadata"] for d in docs])
        db.purge_documents(older_than_days=5)
        all_docs = db.collection.get()
        for meta in all_docs["metadatas"]:
            self.assertTrue((datetime.datetime.now() - datetime.datetime.fromisoformat(meta["created_at"])) .days <= 5)
        db.purge_documents(metadata_filter={"obsolete": True})
        all_docs = db.collection.get()
        for meta in all_docs["metadatas"]:
            self.assertTrue(not meta.get("obsolete", False))
        db.purge_documents(keep_recent=2)
        all_docs = db.collection.get()
        self.assertEqual(len(all_docs["documents"]), 2)
        print("ChromaDB purge test passed. Remaining docs:", all_docs["documents"])

    def test_faiss_purge_protection(self):
        db = FAISSVectorDB(db_path="D:/DATA/vectorstore_test", use_pq=False)
        with self.assertRaises(PermissionError):
            db.purge_documents(older_than_days=1)

    def test_annoy_purge_protection(self):
        db = AnnoyVectorDB(db_path="D:/DATA/vectorstore_test")
        with self.assertRaises(PermissionError):
            db.purge_documents(older_than_days=1)

    @unittest.skipUnless(CHROMA_AVAILABLE, "ChromaDB not available")
    def test_chroma_purge_protection(self):
        db = ChromaVectorDB(db_path="D:/DATA/vectorstore_test")
        with self.assertRaises(PermissionError):
            db.purge_documents(older_than_days=1)

if __name__ == "__main__":
    unittest.main() 