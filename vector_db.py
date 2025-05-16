import os
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
from annoy import AnnoyIndex
import faiss
import logging
import datetime

# Add ChromaDB import
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class BaseVectorDB:
    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        raise NotImplementedError
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError
    def get_stats(self) -> Dict[str, Any]:
        raise NotImplementedError

class FAISSVectorDB(BaseVectorDB):
    def __init__(self, db_path: str = "D:/DATA", use_pq: bool = False, m: int = 8, nbits: int = 8):
        """
        Initialize FAISS vector database with optional PQ compression.
        
        Args:
            db_path: Path to store the database
            use_pq: Whether to use Product Quantization
            m: Number of sub-vectors for PQ (must divide dimension)
            nbits: Number of bits per sub-quantizer for PQ
        """
        self.db_path = Path(db_path)
        self.use_pq = use_pq
        self.m = m
        self.nbits = nbits
        self.index = None
        self.documents = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self._initialize_db()

    def _initialize_db(self):
        """Initialize or load the vector database."""
        if not self.db_path.exists():
            self.db_path.mkdir(parents=True, exist_ok=True)
            self._create_index()
        else:
            self._load_db()

    def _create_index(self):
        """Create a new FAISS index."""
        if self.use_pq:
            if self.dimension % self.m != 0:
                raise ValueError(f"Dimension {self.dimension} must be divisible by m={self.m}")
            self.index = faiss.IndexPQ(self.dimension, self.m, self.nbits)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

    def _load_db(self):
        """Load existing vector database."""
        index_path = self.db_path / "index.bin"
        docs_path = self.db_path / "documents.json"
        
        if index_path.exists() and docs_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(docs_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        else:
            self._create_index()

    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        """Add documents to the vector database."""
        if metadata is None:
            metadata = [{} for _ in texts]
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Convert to float32 for FAISS
        embeddings = embeddings.astype('float32')
        
        # Train index if using PQ and it's not trained
        if self.use_pq and not self.index.is_trained:
            logger.info("Training PQ index...")
            self.index.train(embeddings)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store documents and metadata
        for text, meta in zip(texts, metadata):
            self.documents.append({
                'text': text,
                'metadata': meta
            })
        
        self._save_db()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = self.model.encode([query])[0].astype('float32')
        
        # Search in FAISS index
        D, I = self.index.search(query_embedding.reshape(1, -1), k)
        
        # Return results with metadata
        results = []
        for idx, distance in zip(I[0], D[0]):
            if idx < len(self.documents):
                result = self.documents[idx].copy()
                # Convert L2 distance to similarity score
                result['score'] = float(1 / (1 + distance))  # Convert distance to similarity
                results.append(result)
        
        return results

    def _save_db(self):
        """Save the vector database to disk."""
        # Save FAISS index
        faiss.write_index(self.index, str(self.db_path / "index.bin"))
        
        # Save documents
        with open(self.db_path / "documents.json", 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {
            'total_documents': len(self.documents),
            'dimension': self.dimension,
            'is_trained': self.index.is_trained if hasattr(self.index, 'is_trained') else True,
            'use_pq': self.use_pq
        }
        
        if self.use_pq:
            stats.update({
                'm': self.m,
                'nbits': self.nbits,
                'compression_ratio': (self.dimension * 4) / (self.m * self.nbits / 8)
            })
        
        return stats

    def purge_documents(self, *, older_than_days: int = None, keep_recent: int = None, metadata_filter: dict = None):
        """
        Purge documents from the FAISS vector DB based on criteria.
        Args:
            older_than_days: Remove documents older than this many days (requires 'created_at' in metadata)
            keep_recent: Keep only the most recent N documents
            metadata_filter: Dict of metadata key/values to match for removal (e.g., {"obsolete": True})
        """
        # Enforce purging rules
        if str(self.db_path).replace('\\', '/').lower().startswith('d:/data'):
            logger.warning("Purging is not allowed on the persistent main database (D:/DATA). Operation aborted.")
            raise PermissionError("Purging is not allowed on the persistent main database (D:/DATA).")
        logger.info("Purging documents from FAISSVectorDB...")
        now = datetime.datetime.now()
        filtered_docs = []
        filtered_embeddings = []
        # Gather embeddings for all documents
        embeddings = self.model.encode([doc['text'] for doc in self.documents]).astype('float32')
        for i, doc in enumerate(self.documents):
            remove = False
            # Age-based
            if older_than_days is not None and 'created_at' in doc['metadata']:
                created = datetime.datetime.fromisoformat(doc['metadata']['created_at'])
                if (now - created).days > older_than_days:
                    remove = True
            # Metadata filter
            if metadata_filter is not None:
                for k, v in metadata_filter.items():
                    if doc['metadata'].get(k) == v:
                        remove = True
            if not remove:
                filtered_docs.append(doc)
                filtered_embeddings.append(embeddings[i])
        # Count-based
        if keep_recent is not None and len(filtered_docs) > keep_recent:
            filtered_docs = filtered_docs[-keep_recent:]
            filtered_embeddings = filtered_embeddings[-keep_recent:]
        # Rebuild index
        self.documents = filtered_docs
        if self.use_pq:
            self.index = faiss.IndexPQ(self.dimension, self.m, self.nbits)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
        if filtered_embeddings:
            self.index.train(np.array(filtered_embeddings)) if self.use_pq and not self.index.is_trained else None
            self.index.add(np.array(filtered_embeddings))
        self._save_db()
        logger.info(f"Purged documents. Remaining: {len(self.documents)}")

class AnnoyVectorDB(BaseVectorDB):
    def __init__(self, db_path: str = "D:/DATA"):
        self.db_path = Path(db_path)
        self.index = None
        self.documents = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self._initialize_db()

    def _initialize_db(self):
        """Initialize or load the vector database."""
        if not self.db_path.exists():
            self.db_path.mkdir(parents=True, exist_ok=True)
            self.index = AnnoyIndex(self.dimension, 'angular')
        else:
            self._load_db()

    def _load_db(self):
        """Load existing vector database."""
        index_path = self.db_path / "index.ann"
        docs_path = self.db_path / "documents.json"
        
        if index_path.exists() and docs_path.exists():
            self.index = AnnoyIndex(self.dimension, 'angular')
            self.index.load(str(index_path))
            with open(docs_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        else:
            self.index = AnnoyIndex(self.dimension, 'angular')

    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        """Add documents to the vector database."""
        if metadata is None:
            metadata = [{} for _ in texts]
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Add to Annoy index
        for i, embedding in enumerate(embeddings):
            self.index.add_item(len(self.documents) + i, embedding)
        
        # Store documents and metadata
        for text, meta in zip(texts, metadata):
            self.documents.append({
                'text': text,
                'metadata': meta
            })
        
        # Build the index
        self.index.build(n_trees=10)  # You can adjust n_trees for better accuracy/speed trade-off
        self._save_db()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Search in Annoy index
        indices = self.index.get_nns_by_vector(query_embedding, k, include_distances=True)
        
        # Return results with metadata
        results = []
        for idx, distance in zip(indices[0], indices[1]):
            if idx < len(self.documents):
                result = self.documents[idx].copy()
                # Convert angular distance to similarity score (1 - normalized distance)
                result['score'] = float(1 - (distance / 2))  # Angular distance is in [0, 2]
                results.append(result)
        
        return results

    def _save_db(self):
        """Save the vector database to disk."""
        # Save Annoy index
        self.index.save(str(self.db_path / "index.ann"))
        
        # Save documents
        with open(self.db_path / "documents.json", 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            'total_documents': len(self.documents),
            'dimension': self.dimension,
            'is_built': self.index.get_n_items() > 0
        }

    def purge_documents(self, *, older_than_days: int = None, keep_recent: int = None, metadata_filter: dict = None):
        """
        Purge documents from the Annoy vector DB based on criteria.
        Args:
            older_than_days: Remove documents older than this many days (requires 'created_at' in metadata)
            keep_recent: Keep only the most recent N documents
            metadata_filter: Dict of metadata key/values to match for removal (e.g., {"obsolete": True})
        """
        # Enforce purging rules
        if str(self.db_path).replace('\\', '/').lower().startswith('d:/data'):
            logger.warning("Purging is not allowed on the persistent main database (D:/DATA). Operation aborted.")
            raise PermissionError("Purging is not allowed on the persistent main database (D:/DATA).")
        logger.info("Purging documents from AnnoyVectorDB...")
        now = datetime.datetime.now()
        filtered_docs = []
        filtered_embeddings = []
        embeddings = self.model.encode([doc['text'] for doc in self.documents])
        for i, doc in enumerate(self.documents):
            remove = False
            if older_than_days is not None and 'created_at' in doc['metadata']:
                created = datetime.datetime.fromisoformat(doc['metadata']['created_at'])
                if (now - created).days > older_than_days:
                    remove = True
            if metadata_filter is not None:
                for k, v in metadata_filter.items():
                    if doc['metadata'].get(k) == v:
                        remove = True
            if not remove:
                filtered_docs.append(doc)
                filtered_embeddings.append(embeddings[i])
        if keep_recent is not None and len(filtered_docs) > keep_recent:
            filtered_docs = filtered_docs[-keep_recent:]
            filtered_embeddings = filtered_embeddings[-keep_recent:]
        self.documents = filtered_docs
        self.index = AnnoyIndex(self.dimension, 'angular')
        for i, emb in enumerate(filtered_embeddings):
            self.index.add_item(i, emb)
        if filtered_embeddings:
            self.index.build(n_trees=10)
        self._save_db()
        logger.info(f"Purged documents. Remaining: {len(self.documents)}")

class ChromaVectorDB(BaseVectorDB):
    def __init__(self, db_path: str = "D:/DATA/vectorstore"):
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb is not installed.")
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings(allow_reset=True))
        # Use the first collection or create one
        collections = self.client.list_collections()
        if collections:
            self.collection = self.client.get_collection(collections[0].name)
        else:
            self.collection = self.client.create_collection("default")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384

    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        if metadata is None:
            # Ensure metadata is a non-empty dict for each document
            metadata = [{"source": "unknown"} for _ in texts]
        else:
            # Replace any empty dicts with a default value
            metadata = [m if m else {"source": "unknown"} for m in metadata]
        embeddings = [emb.tolist() for emb in self.model.encode(texts)]
        ids = [str(len(self.collection.get()['ids']) + i) for i in range(len(texts))]
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadata,
            ids=ids
        )

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.model.encode([query])[0].tolist()
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        output = []
        for i in range(len(results['ids'][0])):
            output.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'score': results['distances'][0][i]  # Chroma returns distance, lower is better
            })
        return output

    def get_stats(self) -> Dict[str, Any]:
        count = len(self.collection.get()['ids'])
        return {
            'total_documents': count,
            'dimension': self.dimension,
            'is_built': count > 0
        }

    def purge_documents(self, *, older_than_days: int = None, keep_recent: int = None, metadata_filter: dict = None):
        """
        Purge documents from the ChromaDB vector DB based on criteria.
        Args:
            older_than_days: Remove documents older than this many days (requires 'created_at' in metadata)
            keep_recent: Keep only the most recent N documents
            metadata_filter: Dict of metadata key/values to match for removal (e.g., {"obsolete": True})
        """
        # Enforce purging rules
        if str(self.db_path).replace('\\', '/').lower().startswith('d:/data'):
            logger.warning("Purging is not allowed on the persistent main database (D:/DATA). Operation aborted.")
            raise PermissionError("Purging is not allowed on the persistent main database (D:/DATA).")
        logger.info("Purging documents from ChromaVectorDB...")
        now = datetime.datetime.now()
        all_docs = self.collection.get()
        docs = list(zip(all_docs['ids'], all_docs['documents'], all_docs['metadatas']))
        # Filter
        filtered = []
        for doc_id, text, meta in docs:
            remove = False
            if older_than_days is not None and 'created_at' in meta:
                created = datetime.datetime.fromisoformat(meta['created_at'])
                if (now - created).days > older_than_days:
                    remove = True
            if metadata_filter is not None:
                for k, v in metadata_filter.items():
                    if meta.get(k) == v:
                        remove = True
            if not remove:
                filtered.append((doc_id, text, meta))
        # Count-based
        if keep_recent is not None and len(filtered) > keep_recent:
            filtered = filtered[-keep_recent:]
        # Compute IDs to delete
        filtered_ids = set(doc_id for doc_id, _, _ in filtered)
        all_ids = set(doc_id for doc_id, _, _ in docs)
        ids_to_delete = list(all_ids - filtered_ids)
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
        logger.info(f"Purged documents. Remaining: {len(filtered)}")

    def close(self):
        # Attempt to close the client to release file handles (for test cleanup)
        if hasattr(self.client, 'close'):
            self.client.close()

class AutoVectorDB(BaseVectorDB):
    def __init__(self, db_path: str = "D:/DATA/vectorstore", use_pq: bool = False, m: int = 8, nbits: int = 8):
        self.db_path = Path(db_path)
        # Detect existing database type
        if (self.db_path / "index.bin").exists():
            self.backend = FAISSVectorDB(str(self.db_path), use_pq=use_pq, m=m, nbits=nbits)
        # Detect ChromaDB
        elif (self.db_path / "chroma.sqlite3").exists() and (self.db_path / "meta.json").exists() and CHROMA_AVAILABLE:
            self.backend = ChromaVectorDB(str(self.db_path))
        # Detect Annoy
        elif (self.db_path / "index.ann").exists() and (self.db_path / "documents.json").exists():
            self.backend = AnnoyVectorDB(str(self.db_path))
        else:
            # Default to FAISS with PQ compression if specified
            if use_pq:
                self.backend = FAISSVectorDB(str(self.db_path), use_pq=True, m=m, nbits=nbits)
            else:
                # Default to Annoy, will create new if needed
                self.backend = AnnoyVectorDB(str(self.db_path))

    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]] = None):
        return self.backend.add_documents(texts, metadata)
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return self.backend.search(query, k)
    def get_stats(self) -> Dict[str, Any]:
        return self.backend.get_stats() 