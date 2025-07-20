"""
Repository Upload System for AI Help Agent
Handles Git repositories, ZIP files, and folder uploads with RAG integration
"""

import asyncio
import logging
import os
import tempfile
import zipfile
import shutil
import hashlib
import json
import fnmatch
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path
import requests
from urllib.parse import urlparse
import git
from dataclasses import dataclass

from .enhanced_rag_system import EnhancedRAGSystem, Document
from .knowledge_base_validator import KnowledgeBaseValidator


@dataclass
class RepositoryInfo:
    """Repository information structure"""
    repo_id: str
    name: str
    source_type: str  # 'git', 'zip', 'folder'
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    file_count: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = None
    upload_timestamp: datetime = None
    user_id: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = {}
        if self.upload_timestamp is None:
            self.upload_timestamp = datetime.now(timezone.utc)


class FileTypeDetector:
    """Detects and categorizes file types in repositories"""
    
    def __init__(self):
        self.code_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.m': 'Objective-C',
            '.mm': 'Objective-C++',
            '.pl': 'Perl',
            '.sh': 'Shell',
            '.sql': 'SQL',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.cxx': 'C++',
            '.h': 'C/C++ Header',
            '.hpp': 'C++ Header',
            '.hh': 'C++ Header',
            '.hxx': 'C++ Header',
            '.mjs': 'JavaScript',
            '.cjs': 'JavaScript',
            '.fs': 'F#',
            '.fsx': 'F#',
            '.dart': 'Dart',
            '.erl': 'Erlang',
            '.ex': 'Elixir',
            '.exs': 'Elixir',
            '.groovy': 'Groovy',
            '.jl': 'Julia',
            '.lua': 'Lua',
            '.mat': 'MATLAB',
            '.ml': 'OCaml',
            '.pas': 'Pascal',
            '.vb': 'Visual Basic',
            '.vbs': 'VBScript',
            '.tsv': 'TSV',
            '.csv': 'CSV',
        }
        self.config_extensions = {
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.toml': 'TOML',
            '.ini': 'INI',
            '.cfg': 'Config',
            '.conf': 'Config',
            '.env': 'Environment',
            '.properties': 'Properties',
            '.xml': 'XML',
            '.json5': 'JSON',
        }
        self.documentation_extensions = {
            '.md': 'Markdown',
            '.txt': 'Text',
            '.rst': 'reStructuredText',
            '.adoc': 'AsciiDoc',
            '.asciidoc': 'AsciiDoc',
            '.tex': 'LaTeX',
            '.doc': 'Word',
            '.docx': 'Word',
            '.pdf': 'PDF',
            '.ipynb': 'Jupyter Notebook',
            '.mdx': 'Markdown',
        }
        
        self.ignore_patterns = [
            '.gitignore', '*.pyc', '*.log', '*.DS_Store', 'Thumbs.db', '*.swp', '*.swo', '*~',
            'node_modules/*', '*/node_modules/*', '__pycache__/*', '*/__pycache__/*',
            'venv/*', '*/venv/*', 'env/*', '*/env/*', '.venv/*', '*/.venv/*',
            'dist/*', '*/dist/*', 'build/*', '*/build/*',
            'logs/*', '*/logs/*', 'temp/*', '*/temp/*', 'tmp/*', '*/tmp/*', '.cache/*', '*/.cache/*',
            'htmlcov/*', '*/htmlcov/*', '.coverage*', 'test_results/*', '*/test_results/*'
        ]
    
    def detect_file_types(self, repo_path: Path) -> Dict[str, Any]:
        """Detect and categorize all files in the repository"""
        file_types = {
            'code_files': {},
            'config_files': {},
            'documentation_files': {},
            'other_files': {},
            'statistics': {
                'total_files': 0,
                'code_files': 0,
                'config_files': 0,
                'documentation_files': 0,
                'other_files': 0,
                'total_lines': 0
            }
        }
        
        try:
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and not self._should_ignore(file_path):
                    file_type = self._categorize_file(file_path)
                    rel_path = str(file_path.relative_to(repo_path))
                    
                    # Count lines
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                    except:
                        lines = 0
                    
                    file_info = {
                        'path': rel_path,
                        'type': file_type,
                        'lines': lines,
                        'size': file_path.stat().st_size
                    }
                    
                    if file_type in self.code_extensions.values():
                        file_types['code_files'][rel_path] = file_info
                        file_types['statistics']['code_files'] += 1
                    elif file_type in self.config_extensions.values():
                        file_types['config_files'][rel_path] = file_info
                        file_types['statistics']['config_files'] += 1
                    elif file_type in self.documentation_extensions.values():
                        file_types['documentation_files'][rel_path] = file_info
                        file_types['statistics']['documentation_files'] += 1
                    else:
                        file_types['other_files'][rel_path] = file_info
                        file_types['statistics']['other_files'] += 1
                    
                    file_types['statistics']['total_files'] += 1
                    file_types['statistics']['total_lines'] += lines
                    
        except Exception as e:
            logging.error(f"Error detecting file types: {e}")
        
        return file_types
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        file_str = str(file_path)
        # Directory ignore logic
        ignored_dirs = [
            '.git', 'node_modules', '__pycache__', 'venv', 'env', '.venv', 'dist', 'build', 'logs', 'temp', 'tmp', '.cache', 'htmlcov', 'test_results'
        ]
        for part in file_path.parts:
            if part in ignored_dirs:
                return True
        # File pattern ignore logic
        ignored_files = [
            '.gitignore', '*.pyc', '*.log', '*.DS_Store', 'Thumbs.db', '*.swp', '*.swo', '*~', '.coverage*'
        ]
        for pattern in ignored_files:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        return False
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize a file based on its extension"""
        suffix = file_path.suffix.lower()
        
        if suffix in self.code_extensions:
            return self.code_extensions[suffix]
        elif suffix in self.config_extensions:
            return self.config_extensions[suffix]
        elif suffix in self.documentation_extensions:
            return self.documentation_extensions[suffix]
        else:
            return 'Unknown'


class RepositoryIngestionEngine:
    """Handles repository ingestion from various sources"""
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.file_detector = FileTypeDetector()
        
    async def ingest_git_repository(self, repo_url: str, repo_id: str) -> Tuple[Path, RepositoryInfo]:
        """Clone and ingest a Git repository"""
        try:
            repo_path = Path(self.temp_dir) / repo_id
            
            # Clone repository
            logging.info(f"Cloning repository: {repo_url}")
            git.Repo.clone_from(repo_url, repo_path)
            
            # Extract repository information
            repo_info = RepositoryInfo(
                repo_id=repo_id,
                name=repo_path.name,
                source_type='git',
                source_url=repo_url,
                local_path=str(repo_path),
                status='processing'
            )
            
            # Detect file types
            file_types = self.file_detector.detect_file_types(repo_path)
            repo_info.file_count = file_types['statistics']['total_files']
            repo_info.total_lines = file_types['statistics']['total_lines']
            repo_info.languages = self._extract_languages(file_types)
            
            return repo_path, repo_info
            
        except Exception as e:
            logging.error(f"Failed to ingest Git repository {repo_url}: {e}")
            raise
    
    async def ingest_zip_archive(self, zip_file_path: str, repo_id: str) -> Tuple[Path, RepositoryInfo]:
        """Extract and ingest a ZIP archive"""
        try:
            repo_path = Path(self.temp_dir) / repo_id
            
            # Extract ZIP file
            logging.info(f"Extracting ZIP archive: {zip_file_path}")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(repo_path)
            
            # Extract repository information
            repo_info = RepositoryInfo(
                repo_id=repo_id,
                name=Path(zip_file_path).stem,
                source_type='zip',
                local_path=str(repo_path),
                status='processing'
            )
            
            # Detect file types
            file_types = self.file_detector.detect_file_types(repo_path)
            repo_info.file_count = file_types['statistics']['total_files']
            repo_info.total_lines = file_types['statistics']['total_lines']
            repo_info.languages = self._extract_languages(file_types)
            
            return repo_path, repo_info
            
        except Exception as e:
            logging.error(f"Failed to ingest ZIP archive {zip_file_path}: {e}")
            raise
    
    async def ingest_folder(self, folder_path: str, repo_id: str) -> Tuple[Path, RepositoryInfo]:
        """Ingest a local folder"""
        try:
            source_path = Path(folder_path)
            repo_path = Path(self.temp_dir) / repo_id
            
            # Copy folder to temp directory
            logging.info(f"Copying folder: {folder_path}")
            shutil.copytree(source_path, repo_path)
            
            # Extract repository information
            repo_info = RepositoryInfo(
                repo_id=repo_id,
                name=source_path.name,
                source_type='folder',
                local_path=str(repo_path),
                status='processing'
            )
            
            # Detect file types
            file_types = self.file_detector.detect_file_types(repo_path)
            repo_info.file_count = file_types['statistics']['total_files']
            repo_info.total_lines = file_types['statistics']['total_lines']
            repo_info.languages = self._extract_languages(file_types)
            
            return repo_path, repo_info
            
        except Exception as e:
            logging.error(f"Failed to ingest folder {folder_path}: {e}")
            raise
    
    def _extract_languages(self, file_types: Dict[str, Any]) -> Dict[str, int]:
        """Extract language statistics from file types"""
        languages = {}
        for file_info in file_types['code_files'].values():
            lang = file_info['type']
            if lang not in languages:
                languages[lang] = 0
            languages[lang] += file_info['lines']
        return languages
    
    def cleanup_temp_files(self, repo_id: str):
        """Clean up temporary files for a repository"""
        try:
            repo_path = Path(self.temp_dir) / repo_id
            if repo_path.exists():
                shutil.rmtree(repo_path)
                logging.info(f"Cleaned up temporary files for {repo_id}")
        except Exception as e:
            logging.error(f"Failed to cleanup temp files for {repo_id}: {e}")


class RepositoryUploadSystem:
    """Main repository upload system with RAG integration"""
    
    def __init__(self, shared_state=None):
        self.shared_state = shared_state
        self.ingestion_engine = RepositoryIngestionEngine()
        self.rag_system = EnhancedRAGSystem()
        self.validator = KnowledgeBaseValidator()
        self.uploaded_repos = {}  # Cache for uploaded repositories
        
    async def initialize(self):
        """Initialize the repository upload system"""
        try:
            await self.rag_system.initialize()
            logging.info("Repository Upload System initialized")
        except Exception as e:
            logging.error(f"Failed to initialize Repository Upload System: {e}")
            raise
    
    async def upload_repository(self, repo_source: str, user_id: str = None, 
                              source_type: str = 'git') -> Dict[str, Any]:
        """
        Upload and process a repository
        
        Args:
            repo_source: Git URL, ZIP file path, or folder path
            user_id: Optional user identifier for isolation
            source_type: 'git', 'zip', or 'folder'
            
        Returns:
            Dictionary with upload status and metadata
        """
        try:
            # Generate unique repository ID
            repo_id = self._generate_repo_id(repo_source, user_id)
            
            # Ingest repository based on source type
            if source_type == 'git':
                repo_path, repo_info = await self.ingestion_engine.ingest_git_repository(repo_source, repo_id)
            elif source_type == 'zip':
                repo_path, repo_info = await self.ingestion_engine.ingest_zip_archive(repo_source, repo_id)
            elif source_type == 'folder':
                repo_path, repo_info = await self.ingestion_engine.ingest_folder(repo_source, repo_id)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            repo_info.user_id = user_id
            
            # Process repository for RAG indexing
            indexed_docs = await self._process_repository_for_rag(repo_path, repo_info)
            
            # Update repository status
            repo_info.status = 'completed'
            
            # Cache repository info
            self.uploaded_repos[repo_id] = repo_info
            
            return {
                'status': 'success',
                'repo_id': repo_id,
                'repo_info': repo_info,
                'indexed_documents': len(indexed_docs),
                'message': f"Successfully uploaded and indexed {repo_info.name}"
            }
            
        except Exception as e:
            logging.error(f"Repository upload failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f"Failed to upload repository: {str(e)}"
            }
    
    async def _process_repository_for_rag(self, repo_path: Path, repo_info: RepositoryInfo) -> List[Document]:
        """Process repository files for RAG indexing"""
        documents = []
        
        try:
            # Process code files
            code_files = self._get_code_files(repo_path)
            for file_path in code_files:
                doc = await self._create_document_from_file(file_path, repo_path, repo_info, 'code')
                if doc:
                    documents.append(doc)
            
            # Process documentation files
            doc_files = self._get_documentation_files(repo_path)
            for file_path in doc_files:
                doc = await self._create_document_from_file(file_path, repo_path, repo_info, 'documentation')
                if doc:
                    documents.append(doc)
            
            # Process configuration files
            config_files = self._get_config_files(repo_path)
            for file_path in config_files:
                doc = await self._create_document_from_file(file_path, repo_path, repo_info, 'config')
                if doc:
                    documents.append(doc)
            
            # Index documents in RAG system
            if documents:
                await self.rag_system._index_documents(documents, repo_info.repo_id)
            
            return documents
            
        except Exception as e:
            logging.error(f"Failed to process repository for RAG: {e}")
            return []
    
    def _get_code_files(self, repo_path: Path) -> List[Path]:
        """Get all code files in the repository (refactored to use FileTypeDetector)"""
        code_extensions = set(self.file_detector.code_extensions.keys())
        return [f for f in repo_path.rglob('*') if f.is_file() and f.suffix.lower() in code_extensions]

    def _get_documentation_files(self, repo_path: Path) -> List[Path]:
        """Get all documentation files in the repository (refactored to use FileTypeDetector)"""
        doc_extensions = set(self.file_detector.documentation_extensions.keys())
        return [f for f in repo_path.rglob('*') if f.is_file() and f.suffix.lower() in doc_extensions]

    def _get_config_files(self, repo_path: Path) -> List[Path]:
        """Get all configuration files in the repository (refactored to use FileTypeDetector)"""
        config_extensions = set(self.file_detector.config_extensions.keys())
        return [f for f in repo_path.rglob('*') if f.is_file() and f.suffix.lower() in config_extensions]
    
    async def _create_document_from_file(self, file_path: Path, repo_path: Path, 
                                       repo_info: RepositoryInfo, file_type: str) -> Optional[Document]:
        """Create a Document object from a file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                return None
            
            # Generate document ID
            rel_path = str(file_path.relative_to(repo_path))
            doc_id = f"{repo_info.repo_id}_{hashlib.md5(rel_path.encode()).hexdigest()}"
            
            # Create metadata
            metadata = {
                'repo_id': repo_info.repo_id,
                'repo_name': repo_info.name,
                'file_path': rel_path,
                'file_type': file_type,
                'language': file_path.suffix.lower(),
                'lines': len(content.splitlines()),
                'size': len(content),
                'source': 'repository_upload',
                'user_id': repo_info.user_id or 'anonymous'
            }
            
            # Validate metadata
            metadata = self.validator.validate_and_normalize_metadata(metadata)
            
            # Create document
            doc = Document(
                id=doc_id,
                content=content,
                metadata=metadata,
                source=f"repo_{repo_info.repo_id}",
                timestamp=datetime.now(timezone.utc)
            )
            
            return doc
            
        except Exception as e:
            logging.error(f"Failed to create document from {file_path}: {e}")
            return None
    
    def _generate_repo_id(self, repo_source: str, user_id: str = None) -> str:
        """Generate a unique repository ID"""
        base = f"{repo_source}_{user_id or 'anonymous'}"
        return hashlib.md5(base.encode()).hexdigest()[:12]
    
    async def get_repository_info(self, repo_id: str) -> Optional[RepositoryInfo]:
        """Get information about an uploaded repository"""
        return self.uploaded_repos.get(repo_id)
    
    async def list_uploaded_repositories(self, user_id: str = None) -> List[RepositoryInfo]:
        """List all uploaded repositories for a user"""
        if user_id:
            return [repo for repo in self.uploaded_repos.values() if repo.user_id == user_id]
        else:
            return list(self.uploaded_repos.values())
    
    async def delete_repository(self, repo_id: str) -> bool:
        """Delete an uploaded repository"""
        try:
            if repo_id in self.uploaded_repos:
                repo_info = self.uploaded_repos[repo_id]
                
                # Clean up temporary files
                self.ingestion_engine.cleanup_temp_files(repo_id)
                
                # Remove from cache
                del self.uploaded_repos[repo_id]
                
                # TODO: Remove from RAG system (implement collection deletion)
                
                logging.info(f"Deleted repository: {repo_id}")
                return True
            else:
                logging.warning(f"Repository not found: {repo_id}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to delete repository {repo_id}: {e}")
            return False
    
    async def search_repository(self, repo_id: str, query: str, top_k: int = 10) -> List[Document]:
        """Search within a specific repository"""
        try:
            # Add repository filter to search
            filters = {'repo_id': repo_id}
            return await self.rag_system.retrieve_relevant_content(query, filters=filters, top_k=top_k)
        except Exception as e:
            logging.error(f"Repository search failed: {e}")
            return []
    
    async def get_repository_statistics(self, repo_id: str) -> Dict[str, Any]:
        """Get statistics for an uploaded repository"""
        repo_info = await self.get_repository_info(repo_id)
        if not repo_info:
            return {}
        
        return {
            'repo_id': repo_info.repo_id,
            'name': repo_info.name,
            'source_type': repo_info.source_type,
            'file_count': repo_info.file_count,
            'total_lines': repo_info.total_lines,
            'languages': repo_info.languages,
            'upload_timestamp': repo_info.upload_timestamp.isoformat(),
            'status': repo_info.status
        } 