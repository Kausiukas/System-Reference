"""
Enhanced RAG System for AI Help Agent
Implements true vector-based retrieval with semantic search capabilities
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

import openai
import chromadb
from chromadb.config import Settings
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class Document:
    """Enhanced document structure for RAG system"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    source: str = ""
    timestamp: datetime = None
    relevance_score: float = 0.0


class EmbeddingManager:
    """Manages embeddings generation and caching"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embedding_cache = {}
        
    async def initialize(self):
        """Initialize embedding model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logging.info(f"Initialized embedding model: {self.model_name}")
        except Exception as e:
            logging.error(f"Failed to initialize embedding model: {e}")
            self.model = None
    
    async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of texts"""
        if not self.model:
            await self.initialize()
            
        if not self.model:
            # Fallback to OpenAI embeddings
            return await self._generate_openai_embeddings(texts)
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logging.error(f"Embedding generation failed: {e}")
            return [np.zeros(384) for _ in texts]  # Fallback zero vectors
    
    async def _generate_openai_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Fallback to OpenAI embeddings if local model fails"""
        try:
            client = openai.OpenAI()
            embeddings = []
            
            for text in texts:
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text[:8000]  # OpenAI limit
                )
                embeddings.append(np.array(response.data[0].embedding))
            
            return embeddings
        except Exception as e:
            logging.error(f"OpenAI embedding generation failed: {e}")
            return [np.zeros(1536) for _ in texts]  # OpenAI embedding dimension


class VectorStore:
    """ChromaDB-based vector store for document retrieval"""
    
    def __init__(self, collection_name: str = "ai_help_documents"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Use the new ChromaDB client initialization
            self.client = chromadb.PersistentClient(path="./vectorstore_db")
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "AI Help Agent document store"}
            )
            
            logging.info(f"Initialized vector store with collection: {self.collection_name}")
        except Exception as e:
            logging.error(f"Failed to initialize vector store: {e}")
            self.client = None
    
    async def add_documents(self, documents: List[Document]):
        """Add documents to vector store"""
        if not self.collection:
            await self.initialize()
            
        if not self.collection:
            return
        
        try:
            # Prepare data for ChromaDB
            ids = [doc.id for doc in documents]
            embeddings = [doc.embedding.tolist() for doc in documents if doc.embedding is not None]
            metadatas = [doc.metadata for doc in documents]
            documents_text = [doc.content for doc in documents]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=documents_text,
                metadatas=metadatas,
                ids=ids
            )
            
            logging.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logging.error(f"Failed to add documents to vector store: {e}")
    
    async def similarity_search(self, query_embedding: np.ndarray, top_k: int = 10, 
                               filters: Dict = None) -> List[Document]:
        """Perform similarity search in vector store"""
        if not self.collection:
            return []
        
        try:
            # Query the collection
            query_args = {
                'query_embeddings': [query_embedding.tolist()],
                'n_results': top_k
            }
            
            # Only add where clause if filters are not empty
            if filters:
                query_args['where'] = filters
            
            results = self.collection.query(**query_args)
            
            # Convert results to Document objects
            documents = []
            for i in range(len(results['ids'][0])):
                doc = Document(
                    id=results['ids'][0][i],
                    content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i],
                    source=results['metadatas'][0][i].get('source', 'unknown'),
                    relevance_score=1.0 - results['distances'][0][i]  # Convert distance to similarity
                )
                documents.append(doc)
            
            return documents
        except Exception as e:
            logging.error(f"Similarity search failed: {e}")
            return []


class DocumentProcessor:
    """Advanced document processing with chunking and metadata extraction"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    async def process_codebase(self, codebase_analysis: Dict) -> List[Document]:
        """Process codebase analysis into documents"""
        documents = []
        
        # Process full files
        for file_path, file_info in codebase_analysis.get('full_files', {}).items():
            content = file_info.get('content', '')
            if not content:
                continue
                
            # Create chunks for large files
            chunks = self._create_text_chunks(content)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"code_{hashlib.md5(f'{file_path}_{i}'.encode()).hexdigest()}"
                
                document = Document(
                    id=doc_id,
                    content=chunk,
                    metadata={
                        'source': 'codebase',
                        'file_path': file_path,
                        'chunk_index': i,
                        'language': file_info.get('language', 'unknown'),
                        'functions': ', '.join(file_info.get('functions', [])[:5]),  # Convert to string
                        'classes': ', '.join(file_info.get('classes', [])[:3]),     # Convert to string
                        'imports': ', '.join(file_info.get('imports', [])[:5]),     # Convert to string
                        'summary': file_info.get('summary', ''),
                        'lines': file_info.get('lines', 0)
                    },
                    source='codebase',
                    timestamp=datetime.now()
                )
                documents.append(document)
        
        # Process key files with enhanced metadata
        for key_file in codebase_analysis.get('key_files', []):
            doc_id = f"key_{hashlib.md5(key_file['path'].encode()).hexdigest()}"
            
            # Create enhanced content for key files
            enhanced_content = self._create_enhanced_file_content(key_file)
            
            document = Document(
                id=doc_id,
                content=enhanced_content,
                metadata={
                    'source': 'key_file',
                    'file_path': key_file['path'],
                    'type': key_file['type'],
                    'functions': ', '.join(key_file.get('functions', [])[:5]),  # Convert to string
                    'classes': ', '.join(key_file.get('classes', [])[:3]),     # Convert to string
                    'imports': ', '.join(key_file.get('imports', [])[:5]),     # Convert to string
                    'summary': key_file.get('summary', ''),
                    'importance': 'high'
                },
                source='key_file',
                timestamp=datetime.now()
            )
            documents.append(document)
            
        return documents
    
    async def process_system_documentation(self, knowledge_base: Dict) -> List[Document]:
        """Process system documentation into searchable documents"""
        documents = []
        
        for topic, content in knowledge_base.items():
            # Create chunks for long documentation
            chunks = self._create_text_chunks(content)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"doc_{topic}_{i}"
                
                document = Document(
                    id=doc_id,
                    content=chunk,
                    metadata={
                        'source': 'documentation',
                        'topic': topic,
                        'chunk_index': i,
                        'category': self._categorize_documentation(topic, chunk)
                    },
                    source='documentation',
                    timestamp=datetime.now()
                )
                documents.append(document)
                
        return documents
    
    async def process_conversation_history(self, conversation_memory) -> List[Document]:
        """Process conversation history into retrievable documents"""
        documents = []
        
        if not hasattr(conversation_memory, 'conversation_history'):
            return documents
            
        for i, exchange in enumerate(conversation_memory.conversation_history):
            # Create document for Q&A pair
            content = f"Question: {exchange['question']}\nAnswer: {exchange['response']}"
            doc_id = f"conv_{i}_{hashlib.md5(content.encode()).hexdigest()}"
            
            document = Document(
                id=doc_id,
                content=content,
                metadata={
                    'source': 'conversation',
                    'timestamp': exchange['timestamp'],
                    'question_type': self._classify_question_type(exchange['question']),
                    'topics': ', '.join(self._extract_topics(exchange['question'] + ' ' + exchange['response']))  # Convert to string
                },
                source='conversation',
                timestamp=datetime.fromisoformat(exchange['timestamp'])
            )
            documents.append(document)
            
        return documents
    
    def _create_text_chunks(self, text: str) -> List[str]:
        """Create overlapping text chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to end at word boundary
            if end < len(text) and not text[end].isspace():
                last_space = chunk.rfind(' ')
                if last_space > start + self.chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
            
        return chunks
    
    def _create_enhanced_file_content(self, key_file: Dict) -> str:
        """Create enhanced content representation for key files"""
        content_parts = [
            f"File: {key_file['path']}",
            f"Type: {key_file['type']}",
            f"Summary: {key_file.get('summary', 'No summary available')}"
        ]
        
        if key_file.get('functions'):
            content_parts.append("Functions:")
            for func in key_file['functions'][:5]:  # Top 5 functions
                content_parts.append(f"  - {func}")
        
        if key_file.get('classes'):
            content_parts.append("Classes:")
            for cls in key_file['classes'][:3]:  # Top 3 classes
                content_parts.append(f"  - {cls}")
        
        if key_file.get('imports'):
            content_parts.append("Key Imports:")
            for imp in key_file['imports'][:5]:  # Top 5 imports
                content_parts.append(f"  - {imp}")
        
        return '\n'.join(content_parts)
    
    def _categorize_documentation(self, topic: str, content: str) -> str:
        """Categorize documentation content"""
        if 'troubleshoot' in topic.lower() or 'error' in content.lower():
            return 'troubleshooting'
        elif 'performance' in topic.lower() or 'monitor' in content.lower():
            return 'performance'
        elif 'architecture' in topic.lower() or 'system' in content.lower():
            return 'architecture'
        else:
            return 'general'
    
    def _classify_question_type(self, question: str) -> str:
        """Classify the type of question for better retrieval"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['how', 'explain', 'what']):
            return 'explanation'
        elif any(word in question_lower for word in ['error', 'problem', 'fix']):
            return 'troubleshooting'
        elif any(word in question_lower for word in ['status', 'health', 'performance']):
            return 'monitoring'
        else:
            return 'general'
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text for better categorization"""
        # Simple keyword-based topic extraction
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            'agents': ['agent', 'background', 'worker'],
            'database': ['database', 'postgresql', 'sql'],
            'monitoring': ['monitor', 'health', 'performance'],
            'configuration': ['config', 'setting', 'environment'],
            'api': ['api', 'endpoint', 'request'],
            'ui': ['streamlit', 'interface', 'ui']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ['general']


class EnhancedRAGSystem:
    """Enhanced RAG system with vector search and advanced retrieval"""
    
    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        self.vector_store = VectorStore()
        self.document_processor = DocumentProcessor()
        self.initialized = False
        
    async def initialize(self):
        """Initialize all components"""
        try:
            await self.embedding_manager.initialize()
            await self.vector_store.initialize()
            self.initialized = True
            logging.info("Enhanced RAG system initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Enhanced RAG system: {e}")
            self.initialized = False
    
    async def index_knowledge_base(self, codebase_analysis: Dict, 
                                  knowledge_base: Dict, 
                                  conversation_memory=None):
        """Index all available knowledge sources"""
        if not self.initialized:
            await self.initialize()
            
        try:
            all_documents = []
            
            # Process codebase
            code_docs = await self.document_processor.process_codebase(codebase_analysis)
            all_documents.extend(code_docs)
            
            # Process documentation
            doc_docs = await self.document_processor.process_system_documentation(knowledge_base)
            all_documents.extend(doc_docs)
            
            # Process conversation history
            if conversation_memory:
                conv_docs = await self.document_processor.process_conversation_history(conversation_memory)
                all_documents.extend(conv_docs)
            
            # Generate embeddings for all documents
            texts = [doc.content for doc in all_documents]
            embeddings = await self.embedding_manager.generate_embeddings(texts)
            
            # Assign embeddings to documents
            for doc, embedding in zip(all_documents, embeddings):
                doc.embedding = embedding
            
            # Add to vector store
            await self.vector_store.add_documents(all_documents)
            
            logging.info(f"Indexed {len(all_documents)} documents in knowledge base")
            
        except Exception as e:
            logging.error(f"Failed to index knowledge base: {e}")
    
    async def retrieve_relevant_content(self, query: str, 
                                       system_context: Dict = None, 
                                       top_k: int = 10) -> List[Document]:
        """Retrieve relevant content using vector similarity search"""
        if not self.initialized:
            return []
        
        try:
            # Generate query embedding
            query_embeddings = await self.embedding_manager.generate_embeddings([query])
            query_embedding = query_embeddings[0]
            
            # Build filters based on system context
            filters = self._build_context_filters(system_context)
            
            # Perform similarity search
            similar_docs = await self.vector_store.similarity_search(
                query_embedding, top_k=top_k, filters=filters
            )
            
            # Re-rank results based on context and query intent
            reranked_docs = await self._rerank_documents(query, similar_docs, system_context)
            
            return reranked_docs
            
        except Exception as e:
            logging.error(f"Content retrieval failed: {e}")
            return []
    
    def _build_context_filters(self, system_context: Dict = None) -> Dict:
        """Build filters based on system context"""
        filters = {}
        
        if not system_context:
            return filters
        
        # Filter by relevance to current system state
        query_category = system_context.get('query_category', '')
        if query_category:
            filters['category'] = query_category
            
        return filters
    
    async def _rerank_documents(self, query: str, documents: List[Document], 
                               system_context: Dict = None) -> List[Document]:
        """Re-rank documents based on query intent and system context"""
        
        # Simple re-ranking based on source priority and system context
        source_weights = {
            'key_file': 1.2,      # Prioritize key files
            'codebase': 1.0,      # Standard codebase content
            'conversation': 0.9,   # Previous conversations
            'documentation': 0.8   # Static documentation
        }
        
        # Apply contextual boosts
        for doc in documents:
            base_score = doc.relevance_score
            source_boost = source_weights.get(doc.source, 1.0)
            
            # Boost based on query category match
            if system_context and system_context.get('query_category'):
                category = system_context['query_category']
                if category in doc.metadata.get('category', ''):
                    source_boost *= 1.1
            
            # Boost recent conversation content
            if doc.source == 'conversation' and doc.timestamp:
                hours_old = (datetime.now() - doc.timestamp).total_seconds() / 3600
                if hours_old < 24:  # Recent conversations
                    source_boost *= 1.15
            
            doc.relevance_score = base_score * source_boost
        
        # Sort by enhanced relevance score
        documents.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return documents 