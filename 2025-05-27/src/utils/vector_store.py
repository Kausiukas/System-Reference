import os
from typing import List, Dict, Any, Optional
from chromadb import Client, Settings, PersistentClient
from chromadb.utils import embedding_functions
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from pathlib import Path
import email
import json
from datetime import datetime
import logging
import mimetypes
import extract_msg
import PyPDF2
import gc
import time
import shutil
import psutil
import sys

class VectorStore:
    def __init__(self, persist_directory: str = "D:/DATA", collection_name: str = "client_documents", reset: bool = False):
        """Initialize vector store with external data directory."""
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Clear any existing ONNX cache
        self._clear_onnx_cache()
        
        # Initialize ChromaDB client with minimal settings
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Use a more lightweight embedding function
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-MiniLM-L3-v2",
            device="cpu",
            normalize_embeddings=True
        )
        
        try:
            if reset:
                try:
                    self.client.delete_collection(name=collection_name)
                    logging.info(f"Deleted existing collection: {collection_name}")
                except Exception as e:
                    # Ignore if collection doesn't exist
                    logging.debug(f"Collection {collection_name} did not exist for deletion: {str(e)}")
            
            # Get existing collection or create new one
            try:
                self.collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )
                logging.info(f"Using existing collection: {collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                logging.info(f"Created new collection: {collection_name}")
                
        except Exception as e:
            logging.error(f"Failed to initialize vector store: {str(e)}")
            raise
        
        # Initialize text splitter with very conservative settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,  # Even smaller chunk size
            chunk_overlap=20,  # Minimal overlap
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
            keep_separator=False,
            add_start_index=True,
            strip_whitespace=True
        )
        
    def _clear_onnx_cache(self):
        """Clear ONNX runtime cache directory."""
        cache_dir = os.path.expanduser("~/.cache/chroma")
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
            except Exception as e:
                logging.warning(f"Failed to clear ONNX cache: {str(e)}")

    def _check_memory(self):
        """Check if system has enough available memory."""
        memory = psutil.virtual_memory()
        if memory.available < 1 * 1024 * 1024 * 1024:  # Less than 1GB available
            self._cleanup_memory()
            time.sleep(1)  # Wait for memory to be freed
            
    def _cleanup_memory(self):
        """Force garbage collection and clear caches."""
        gc.collect()
        if hasattr(sys, 'set_int_max_str_digits'):
            sys.set_int_max_str_digits(0)  # Reset string conversion limit
            
    def import_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, int]:
        """Import all supported documents from a directory."""
        stats = {
            "emails": 0,
            "profiles": 0,
            "documents": 0,
            "errors": 0,
            "skipped": 0
        }
        
        path = Path(directory_path)
        if not path.exists():
            raise ValueError(f"Directory {directory_path} does not exist")
            
        # Get all files
        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if file_path.is_file():
                try:
                    # Check file size first
                    file_size = os.path.getsize(file_path)
                    if file_size > 5 * 1024 * 1024:  # Skip files larger than 5MB
                        logging.warning(f"Skipping large file {file_path} ({file_size / 1024 / 1024:.2f} MB)")
                        stats["skipped"] += 1
                        continue
                        
                    # Check memory before processing each file
                    self._check_memory()
                    
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    
                    if file_path.suffix.lower() == '.msg':
                        self._process_outlook_msg(file_path)
                        stats["emails"] += 1
                    elif file_path.suffix.lower() == '.json' and 'profile' in file_path.name.lower():
                        self._process_profile_json(file_path)
                        stats["profiles"] += 1
                    elif mime_type and (mime_type.startswith('text/') or 
                          mime_type in ['application/pdf', 'application/json']):
                        self._process_document(file_path)
                        stats["documents"] += 1
                        
                    # Add a small delay between files
                    time.sleep(0.1)
                    
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {str(e)}")
                    stats["errors"] += 1
                    self._cleanup_memory()
                    
        return stats
        
    def _process_outlook_msg(self, file_path: Path) -> None:
        """Process Outlook MSG file."""
        msg = extract_msg.Message(file_path)
        content = f"Subject: {msg.subject}\nFrom: {msg.sender}\nTo: {msg.recipients}\nBody: {msg.body}"
        
        # Convert recipients list to string
        recipients_str = "; ".join(str(recipient) for recipient in msg.recipients) if msg.recipients else ""
        
        metadata = {
            "type": "email",
            "subject": msg.subject,
            "sender": msg.sender,
            "recipients": recipients_str,  # Now a string instead of a list
            "date": msg.date.isoformat() if msg.date else None,
            "file_path": str(file_path)
        }
        
        self.add_texts([content], [metadata])
        
    def _process_profile_json(self, file_path: Path) -> None:
        """Process client profile JSON file."""
        with open(file_path, 'r') as f:
            profile = json.load(f)
            
        # Extract text content from profile
        content = json.dumps(profile, indent=2)
        
        metadata = {
            "type": "profile",
            "client_id": profile.get("client_id"),
            "company_name": profile.get("company_name"),
            "last_updated": profile.get("last_interaction"),
            "file_path": str(file_path)
        }
        
        self.add_texts([content], [metadata])
        
    def _process_pdf(self, file_path: Path) -> None:
        """Process PDF file with proper chunking."""
        try:
            with open(file_path, 'rb') as file:
                # Create PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from each page
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
                
                # Create metadata
                metadata = {
                    "type": "document",
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "mime_type": "application/pdf",
                    "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                    "num_pages": len(pdf_reader.pages)
                }
                
                # Split text into smaller chunks
                chunks = self.text_splitter.split_text(text)
                
                # Process chunks in batches
                batch_size = 20
                for i in range(0, len(chunks), batch_size):
                    batch_chunks = chunks[i:i + batch_size]
                    batch_metadata = []
                    
                    for j, chunk in enumerate(batch_chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            "chunk_index": i + j,
                            "total_chunks": len(chunks)
                        })
                        batch_metadata.append(chunk_metadata)
                    
                    self.add_texts(batch_chunks, batch_metadata)
                    
        except Exception as e:
            logging.error(f"Error processing PDF {file_path}: {str(e)}")
            raise

    def _process_document(self, file_path: Path) -> None:
        """Process general document file."""
        try:
            # Check file size before processing
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # Skip files larger than 10MB
                logging.warning(f"Skipping large file {file_path} ({file_size / 1024 / 1024:.2f} MB)")
                return
                
            # Handle PDFs separately
            if file_path.suffix.lower() == '.pdf':
                self._process_pdf(file_path)
                return
                
            # Handle other document types
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            metadata = {
                "type": "document",
                "file_name": file_path.name,
                "file_path": str(file_path),
                "mime_type": mimetypes.guess_type(str(file_path))[0],
                "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                "file_size": file_size
            }
            
            self.add_texts([content], [metadata])
            
        except Exception as e:
            logging.error(f"Error processing document {file_path}: {str(e)}")
            raise

    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None):
        """Add documents to the vector store."""
        collection = self.client.get_or_create_collection("documents")
        collection.add(
            documents=documents,
            metadatas=metadata or [{}] * len(documents),
            ids=[f"doc_{i}" for i in range(len(documents))]
        )
        
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        collection = self.client.get_collection("documents")
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def generate_document_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique document ID based on content and metadata."""
        content = f"{text}{str(metadata)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> List[str]:
        """Add texts to the vector store with metadata."""
        if not texts:
            return []
        
        all_ids = []
        BATCH_SIZE = 3  # Even smaller batch size
        
        for text, metadata in zip(texts, metadatas):
            try:
                # Check memory before processing
                self._check_memory()
                
                chunks = self.text_splitter.split_text(text)
                
                # Process chunks in very small batches
                for i in range(0, len(chunks), BATCH_SIZE):
                    batch_chunks = chunks[i:i + BATCH_SIZE]
                    batch_metadatas = []
                    batch_ids = []
                    
                    for j, chunk in enumerate(batch_chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata["chunk_index"] = i + j
                        chunk_metadata["total_chunks"] = len(chunks)
                        doc_id = self.generate_document_id(chunk, chunk_metadata)
                        
                        batch_metadatas.append(chunk_metadata)
                        batch_ids.append(doc_id)
                    
                    # Retry logic for adding batches
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            self.collection.add(
                                documents=batch_chunks,
                                metadatas=batch_metadatas,
                                ids=batch_ids
                            )
                            all_ids.extend(batch_ids)
                            break
                        except Exception as e:
                            if retry == max_retries - 1:
                                logging.error(f"Failed to add batch after {max_retries} retries: {str(e)}")
                                raise
                            self._cleanup_memory()
                            time.sleep(1)  # Wait before retry
                    
                    # Small delay between batches
                    time.sleep(0.1)
                    
            except Exception as e:
                logging.error(f"Error processing text: {str(e)}")
                continue
                
        return all_ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_criteria: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Prepare filter if provided
        where = filter_criteria if filter_criteria else None
        
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where
        )
        
        # Format results
        documents = []
        for i in range(len(results['documents'][0])):
            documents.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None,
                'id': results['ids'][0][i]
            })
        
        return documents

    def delete_by_filter(self, filter_criteria: Dict[str, Any]) -> None:
        """Delete documents matching the filter criteria."""
        self.collection.delete(where=filter_criteria)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name,
        }

    def search_by_type(
        self,
        query: str,
        doc_type: str,
        k: int = 5,
        additional_filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for documents of a specific type."""
        filters = {"type": doc_type}
        if additional_filters:
            filters.update(additional_filters)
            
        return self.similarity_search(query, k, filters)
        
    def get_client_context(self, client_id: str, max_documents: int = 10) -> List[Dict[str, Any]]:
        """Get relevant context for a client."""
        # Get profile first
        profile_results = self.search_by_type("", "profile", 1, {"client_id": client_id})
        
        # Get recent emails and documents
        email_results = self.search_by_type("", "email", max_documents // 2, {"client_id": client_id})
        doc_results = self.search_by_type("", "document", max_documents // 2, {"client_id": client_id})
        
        return profile_results + email_results + doc_results 