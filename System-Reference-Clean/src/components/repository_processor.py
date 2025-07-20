"""
Repository Processor Component

Handles repository cloning, analysis, and processing for the System-Reference application.
"""

import os
import tempfile
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import ast
import re
import requests
from github import Github
import streamlit as st

class RepositoryProcessor:
    """Handles repository processing and analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize repository processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.github_token = config.get('github_token')
        self.github_client = Github(self.github_token) if self.github_token else None
        self.temp_dirs = []
        
        # Processing stages
        self.stages = [
            'initialization',
            'metadata_extraction',
            'structure_analysis',
            'code_analysis',
            'rag_indexing'
        ]
    
    def initialize_repository(self, repo_url: str) -> Dict[str, Any]:
        """
        Initialize and clone repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Repository information dictionary
        """
        try:
            # Update status
            self._update_status('initializing', 'Validating repository URL...')
            
            # Validate URL
            if not self._is_valid_github_url(repo_url):
                raise ValueError("Invalid GitHub repository URL")
            
            # Extract repository info
            repo_info = self._extract_repo_info(repo_url)
            
            # Update status
            self._update_status('initializing', 'Cloning repository...')
            
            # Clone repository
            repo_path = self._clone_repository(repo_url)
            
            # Get basic repository information
            basic_info = self._get_basic_info(repo_path, repo_info)
            
            return {
                'url': repo_url,
                'local_path': repo_path,
                'name': repo_info['name'],
                'owner': repo_info['owner'],
                'size': basic_info['size'],
                'file_count': basic_info['file_count'],
                'primary_language': basic_info['primary_language'],
                'last_commit': basic_info['last_commit'],
                'description': basic_info['description']
            }
            
        except Exception as e:
            logging.error(f"Repository initialization failed: {e}")
            raise
    
    def extract_metadata(self, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract repository metadata.
        
        Args:
            repo_info: Repository information
            
        Returns:
            Metadata dictionary
        """
        try:
            self._update_status('extracting_metadata', 'Extracting README...')
            
            repo_path = repo_info['local_path']
            metadata = {}
            
            # Extract README
            readme_info = self._extract_readme(repo_path)
            metadata['readme'] = readme_info
            
            # Extract dependencies
            self._update_status('extracting_metadata', 'Extracting dependencies...')
            dependencies = self._extract_dependencies(repo_path)
            metadata['dependencies'] = dependencies
            
            # Extract configuration files
            self._update_status('extracting_metadata', 'Extracting configuration...')
            config_files = self._extract_config_files(repo_path)
            metadata['config_files'] = config_files
            
            # Extract license
            license_info = self._extract_license(repo_path)
            metadata['license'] = license_info
            
            # Extract git information
            git_info = self._extract_git_info(repo_path)
            metadata['git_info'] = git_info
            
            return metadata
            
        except Exception as e:
            logging.error(f"Metadata extraction failed: {e}")
            raise
    
    def analyze_file_structure(self, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze repository file structure.
        
        Args:
            repo_info: Repository information
            
        Returns:
            File structure analysis
        """
        try:
            self._update_status('analyzing_structure', 'Scanning directories...')
            
            repo_path = repo_info['local_path']
            structure = {
                'directories': [],
                'files': [],
                'file_types': {},
                'key_directories': []
            }
            
            # Scan directory structure
            self._scan_directories(repo_path, structure)
            
            # Analyze file types
            self._update_status('analyzing_structure', 'Analyzing file types...')
            self._analyze_file_types(structure)
            
            # Identify key directories
            self._update_status('analyzing_structure', 'Identifying key directories...')
            self._identify_key_directories(structure)
            
            return structure
            
        except Exception as e:
            logging.error(f"File structure analysis failed: {e}")
            raise
    
    def analyze_code(self, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code files.
        
        Args:
            repo_info: Repository information
            
        Returns:
            Code analysis results
        """
        try:
            self._update_status('analyzing_code', 'Identifying code files...')
            
            repo_path = repo_info['local_path']
            code_files = self._get_code_files(repo_path)
            
            analysis = {
                'files': {},
                'functions': [],
                'classes': [],
                'imports': [],
                'statistics': {
                    'total_files': len(code_files),
                    'total_functions': 0,
                    'total_classes': 0,
                    'total_lines': 0
                }
            }
            
            # Analyze each code file
            for i, file_path in enumerate(code_files):
                self._update_status('analyzing_code', f'Analyzing file {i+1}/{len(code_files)}...')
                
                file_analysis = self._analyze_code_file(file_path)
                analysis['files'][file_path] = file_analysis
                
                # Aggregate statistics
                analysis['statistics']['total_functions'] += len(file_analysis.get('functions', []))
                analysis['statistics']['total_classes'] += len(file_analysis.get('classes', []))
                analysis['statistics']['total_lines'] += file_analysis.get('line_count', 0)
            
            # Analyze imports and dependencies
            self._update_status('analyzing_code', 'Analyzing imports...')
            analysis['imports'] = self._analyze_imports(analysis['files'])
            
            # Identify entry points
            analysis['entry_points'] = self._identify_entry_points(analysis['files'])
            
            return analysis
            
        except Exception as e:
            logging.error(f"Code analysis failed: {e}")
            raise
    
    def build_rag_index(self, metadata: Dict[str, Any], structure: Dict[str, Any], 
                       code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build RAG index from repository data.
        
        Args:
            metadata: Repository metadata
            structure: File structure analysis
            code_analysis: Code analysis results
            
        Returns:
            RAG index information
        """
        try:
            self._update_status('building_rag', 'Creating documents...')
            
            documents = []
            
            # Add README content
            if metadata.get('readme'):
                documents.extend(self._create_readme_documents(metadata['readme']))
            
            # Add code documentation
            self._update_status('building_rag', 'Processing code documentation...')
            documents.extend(self._create_code_documents(code_analysis))
            
            # Add file structure information
            documents.extend(self._create_structure_documents(structure))
            
            # Add dependency information
            documents.extend(self._create_dependency_documents(metadata.get('dependencies', {})))
            
            # Generate embeddings (placeholder - would integrate with ChromaDB)
            self._update_status('building_rag', 'Generating embeddings...')
            embeddings = self._generate_embeddings(documents)
            
            # Build vector index (placeholder - would integrate with ChromaDB)
            self._update_status('building_rag', 'Building vector index...')
            vector_index = self._build_vector_index(documents, embeddings)
            
            return {
                'documents': documents,
                'embeddings': embeddings,
                'vector_index': vector_index,
                'metadata': {
                    'total_documents': len(documents),
                    'total_embeddings': len(embeddings),
                    'index_size': len(vector_index)
                }
            }
            
        except Exception as e:
            logging.error(f"RAG index building failed: {e}")
            raise
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logging.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
        
        self.temp_dirs.clear()
    
    def _update_status(self, stage: str, message: str):
        """Update processing status."""
        if hasattr(st, 'session_state'):
            st.session_state.processing_status = stage
            st.session_state.status_message = message
    
    def _is_valid_github_url(self, url: str) -> bool:
        """Validate GitHub repository URL."""
        pattern = r'^https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+/?$'
        return bool(re.match(pattern, url))
    
    def _extract_repo_info(self, repo_url: str) -> Dict[str, str]:
        """Extract repository owner and name from URL."""
        parts = repo_url.rstrip('/').split('/')
        return {
            'owner': parts[-2],
            'name': parts[-1]
        }
    
    def _clone_repository(self, repo_url: str) -> str:
        """Clone repository to temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix="repo_analysis_")
        self.temp_dirs.append(temp_dir)
        
        try:
            # Use git command to clone
            import subprocess
            result = subprocess.run(
                ['git', 'clone', repo_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            return temp_dir
            
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
    
    def _get_basic_info(self, repo_path: str, repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Get basic repository information."""
        try:
            # Get repository size
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(repo_path):
                # Skip .git directory
                if '.git' in root:
                    continue
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except OSError:
                        pass
            
            # Get primary language (simplified)
            primary_language = self._detect_primary_language(repo_path)
            
            # Get last commit info (simplified)
            last_commit = self._get_last_commit_info(repo_path)
            
            # Get description from GitHub API if available
            description = ""
            if self.github_client:
                try:
                    repo = self.github_client.get_repo(f"{repo_info['owner']}/{repo_info['name']}")
                    description = repo.description or ""
                except Exception:
                    pass
            
            return {
                'size': total_size,
                'file_count': file_count,
                'primary_language': primary_language,
                'last_commit': last_commit,
                'description': description
            }
            
        except Exception as e:
            logging.error(f"Failed to get basic info: {e}")
            return {
                'size': 0,
                'file_count': 0,
                'primary_language': 'Unknown',
                'last_commit': 'Unknown',
                'description': ''
            }
    
    def _detect_primary_language(self, repo_path: str) -> str:
        """Detect primary programming language."""
        language_counts = {}
        
        for root, dirs, files in os.walk(repo_path):
            if '.git' in root:
                continue
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.py']:
                    language_counts['Python'] = language_counts.get('Python', 0) + 1
                elif ext in ['.js', '.ts']:
                    language_counts['JavaScript'] = language_counts.get('JavaScript', 0) + 1
                elif ext in ['.java']:
                    language_counts['Java'] = language_counts.get('Java', 0) + 1
                elif ext in ['.go']:
                    language_counts['Go'] = language_counts.get('Go', 0) + 1
                elif ext in ['.rs']:
                    language_counts['Rust'] = language_counts.get('Rust', 0) + 1
        
        if language_counts:
            return max(language_counts, key=language_counts.get)
        return 'Unknown'
    
    def _get_last_commit_info(self, repo_path: str) -> str:
        """Get last commit information."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cd', '--date=short'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return 'Unknown'
    
    def _extract_readme(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Extract and parse README files."""
        readme_files = [
            'README.md', 'README.txt', 'README.rst',
            'readme.md', 'readme.txt', 'readme.rst'
        ]
        
        for readme_file in readme_files:
            readme_path = os.path.join(repo_path, readme_file)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    return {
                        'filename': readme_file,
                        'content': content,
                        'sections': self._parse_readme_sections(content),
                        'size': len(content)
                    }
                except Exception as e:
                    logging.warning(f"Failed to read README {readme_file}: {e}")
        
        return None
    
    def _parse_readme_sections(self, content: str) -> Dict[str, str]:
        """Parse README content into sections."""
        sections = {}
        current_section = "overview"
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('#'):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                section_name = line.strip('# ').lower().replace(' ', '_')
                current_section = section_name
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_dependencies(self, repo_path: str) -> Dict[str, List[str]]:
        """Extract dependencies from various files."""
        dependencies = {}
        
        # Python requirements
        req_files = ['requirements.txt', 'requirements-dev.txt', 'setup.py', 'pyproject.toml']
        for req_file in req_files:
            req_path = os.path.join(repo_path, req_file)
            if os.path.exists(req_path):
                try:
                    with open(req_path, 'r') as f:
                        content = f.read()
                    
                    if req_file == 'requirements.txt':
                        deps = self._parse_requirements_txt(content)
                        dependencies['python'] = deps
                    elif req_file == 'setup.py':
                        deps = self._parse_setup_py(content)
                        dependencies['python'] = deps
                except Exception as e:
                    logging.warning(f"Failed to parse {req_file}: {e}")
        
        # Node.js package.json
        package_json = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    content = f.read()
                deps = self._parse_package_json(content)
                dependencies['javascript'] = deps
            except Exception as e:
                logging.warning(f"Failed to parse package.json: {e}")
        
        return dependencies
    
    def _parse_requirements_txt(self, content: str) -> List[str]:
        """Parse requirements.txt file."""
        deps = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (remove version specifiers)
                package = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
                deps.append(package)
        return deps
    
    def _parse_setup_py(self, content: str) -> List[str]:
        """Parse setup.py file for dependencies."""
        # Simplified parsing - in production would use ast
        deps = []
        if 'install_requires' in content:
            # Extract dependencies from install_requires
            import re
            matches = re.findall(r"['\"]([^'\"]+)['\"]", content)
            deps.extend(matches)
        return deps
    
    def _parse_package_json(self, content: str) -> List[str]:
        """Parse package.json file."""
        try:
            import json
            data = json.loads(content)
            deps = []
            
            if 'dependencies' in data:
                deps.extend(list(data['dependencies'].keys()))
            if 'devDependencies' in data:
                deps.extend(list(data['devDependencies'].keys()))
            
            return deps
        except Exception:
            return []
    
    def _extract_config_files(self, repo_path: str) -> List[Dict[str, str]]:
        """Extract configuration files."""
        config_files = []
        config_patterns = [
            '*.yml', '*.yaml', '*.json', '*.toml', '*.ini', '*.cfg',
            '.env*', 'docker-compose*', 'Dockerfile*', 'Makefile'
        ]
        
        for pattern in config_patterns:
            for file_path in Path(repo_path).rglob(pattern):
                if '.git' not in str(file_path):
                    config_files.append({
                        'name': file_path.name,
                        'path': str(file_path.relative_to(repo_path)),
                        'type': file_path.suffix or 'no_extension'
                    })
        
        return config_files
    
    def _extract_license(self, repo_path: str) -> Optional[Dict[str, str]]:
        """Extract license information."""
        license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'license']
        
        for license_file in license_files:
            license_path = os.path.join(repo_path, license_file)
            if os.path.exists(license_path):
                try:
                    with open(license_path, 'r') as f:
                        content = f.read()
                    
                    return {
                        'filename': license_file,
                        'content': content,
                        'type': self._detect_license_type(content)
                    }
                except Exception as e:
                    logging.warning(f"Failed to read license {license_file}: {e}")
        
        return None
    
    def _detect_license_type(self, content: str) -> str:
        """Detect license type from content."""
        content_lower = content.lower()
        
        if 'mit license' in content_lower:
            return 'MIT'
        elif 'apache license' in content_lower:
            return 'Apache'
        elif 'gnu general public license' in content_lower:
            return 'GPL'
        elif 'bsd license' in content_lower:
            return 'BSD'
        else:
            return 'Unknown'
    
    def _extract_git_info(self, repo_path: str) -> Dict[str, str]:
        """Extract Git repository information."""
        try:
            import subprocess
            
            # Get branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip() if result.returncode == 0 else 'Unknown'
            
            # Get remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            remote_url = result.stdout.strip() if result.returncode == 0 else 'Unknown'
            
            return {
                'branch': branch,
                'remote_url': remote_url
            }
            
        except Exception as e:
            logging.warning(f"Failed to extract git info: {e}")
            return {
                'branch': 'Unknown',
                'remote_url': 'Unknown'
            }
    
    def _scan_directories(self, repo_path: str, structure: Dict[str, Any]):
        """Scan directory structure."""
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in root:
                continue
            
            # Calculate relative path
            rel_path = os.path.relpath(root, repo_path)
            
            # Add directory info
            if rel_path != '.':
                structure['directories'].append({
                    'path': rel_path,
                    'file_count': len(files),
                    'subdirectories': len(dirs)
                })
            
            # Add file info
            for file in files:
                file_path = os.path.join(rel_path, file)
                full_path = os.path.join(root, file)
                
                try:
                    file_info = {
                        'path': file_path,
                        'size': os.path.getsize(full_path),
                        'type': self._detect_file_type(file),
                        'language': self._detect_language(file_path, full_path)
                    }
                    structure['files'].append(file_info)
                except OSError:
                    pass
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type based on extension."""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
            return 'code'
        elif ext in ['.md', '.txt', '.rst', '.adoc']:
            return 'documentation'
        elif ext in ['.yml', '.yaml', '.json', '.toml', '.ini']:
            return 'configuration'
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            return 'image'
        else:
            return 'other'
    
    def _detect_language(self, file_path: str, full_path: str) -> str:
        """Detect programming language."""
        ext = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.md': 'Markdown',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON'
        }
        
        return language_map.get(ext, 'Unknown')
    
    def _analyze_file_types(self, structure: Dict[str, Any]):
        """Analyze file type distribution."""
        file_types = {}
        for file_info in structure['files']:
            file_type = file_info['type']
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        structure['file_types'] = file_types
    
    def _identify_key_directories(self, structure: Dict[str, Any]):
        """Identify key directories in the repository."""
        key_patterns = [
            'src', 'lib', 'app', 'main', 'core', 'utils', 'helpers',
            'tests', 'test', 'spec', 'docs', 'documentation',
            'config', 'conf', 'settings', 'scripts', 'tools'
        ]
        
        key_dirs = []
        for directory in structure['directories']:
            dir_name = os.path.basename(directory['path']).lower()
            if dir_name in key_patterns:
                key_dirs.append(directory['path'])
        
        structure['key_directories'] = key_dirs
    
    def _get_code_files(self, repo_path: str) -> List[str]:
        """Get list of code files."""
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']
        code_files = []
        
        for root, dirs, files in os.walk(repo_path):
            if '.git' in root:
                continue
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    code_files.append(rel_path)
        
        return code_files
    
    def _analyze_code_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single code file."""
        analysis = {
            'functions': [],
            'classes': [],
            'imports': [],
            'line_count': 0,
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis['line_count'] = len(content.split('\n'))
            
            # Detect language and analyze accordingly
            if file_path.endswith('.py'):
                self._analyze_python_file(content, analysis)
            elif file_path.endswith(('.js', '.ts')):
                self._analyze_javascript_file(content, analysis)
            else:
                # Generic analysis for other languages
                self._analyze_generic_file(content, analysis)
                
        except Exception as e:
            analysis['errors'].append(f"Failed to analyze {file_path}: {e}")
        
        return analysis
    
    def _analyze_python_file(self, content: str, analysis: Dict[str, Any]):
        """Analyze Python file."""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append({
                        'name': node.name,
                        'line_number': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'parameters': [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'line_number': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        analysis['imports'].append(f"{module}.{alias.name}")
                        
        except SyntaxError as e:
            analysis['errors'].append(f"Syntax error: {e}")
    
    def _analyze_javascript_file(self, content: str, analysis: Dict[str, Any]):
        """Analyze JavaScript/TypeScript file."""
        # Simplified JavaScript analysis
        import re
        
        # Find function declarations
        function_pattern = r'function\s+(\w+)\s*\('
        functions = re.findall(function_pattern, content)
        for func_name in functions:
            analysis['functions'].append({
                'name': func_name,
                'line_number': 0,  # Would need more complex parsing
                'docstring': '',
                'parameters': []
            })
        
        # Find class declarations
        class_pattern = r'class\s+(\w+)'
        classes = re.findall(class_pattern, content)
        for class_name in classes:
            analysis['classes'].append({
                'name': class_name,
                'line_number': 0,
                'docstring': '',
                'methods': []
            })
    
    def _analyze_generic_file(self, content: str, analysis: Dict[str, Any]):
        """Generic file analysis."""
        # Basic line counting and content analysis
        lines = content.split('\n')
        analysis['line_count'] = len(lines)
        
        # Count comments (simplified)
        comment_lines = sum(1 for line in lines if line.strip().startswith('//') or line.strip().startswith('#'))
        analysis['comment_lines'] = comment_lines
    
    def _analyze_imports(self, files_analysis: Dict[str, Any]) -> List[str]:
        """Analyze imports across all files."""
        all_imports = []
        for file_analysis in files_analysis.values():
            all_imports.extend(file_analysis.get('imports', []))
        
        return list(set(all_imports))  # Remove duplicates
    
    def _identify_entry_points(self, files_analysis: Dict[str, Any]) -> List[str]:
        """Identify potential entry points."""
        entry_points = []
        
        for file_path, analysis in files_analysis.items():
            # Look for main functions or entry points
            for func in analysis.get('functions', []):
                if func['name'] in ['main', 'app', 'run', 'start']:
                    entry_points.append(file_path)
                    break
        
        return entry_points
    
    def _create_readme_documents(self, readme: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create documents from README content."""
        documents = []
        
        # Create overview document
        documents.append({
            'id': 'readme_overview',
            'content': readme['content'][:1000],  # First 1000 chars
            'metadata': {
                'type': 'readme_overview',
                'source': 'README.md',
                'section': 'overview'
            }
        })
        
        # Create section-specific documents
        for section_name, section_content in readme.get('sections', {}).items():
            documents.append({
                'id': f'readme_{section_name}',
                'content': section_content,
                'metadata': {
                    'type': 'readme_section',
                    'source': 'README.md',
                    'section': section_name
                }
            })
        
        return documents
    
    def _create_code_documents(self, code_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create documents from code analysis."""
        documents = []
        
        for file_path, file_analysis in code_analysis.get('files', {}).items():
            # Create function documents
            for func in file_analysis.get('functions', []):
                documents.append({
                    'id': f'func_{file_path}_{func["name"]}',
                    'content': f"Function: {func['name']}\nParameters: {func['parameters']}\nDocstring: {func['docstring']}",
                    'metadata': {
                        'type': 'function',
                        'file': file_path,
                        'name': func['name'],
                        'line': func['line_number']
                    }
                })
            
            # Create class documents
            for cls in file_analysis.get('classes', []):
                documents.append({
                    'id': f'class_{file_path}_{cls["name"]}',
                    'content': f"Class: {cls['name']}\nMethods: {cls['methods']}\nDocstring: {cls['docstring']}",
                    'metadata': {
                        'type': 'class',
                        'file': file_path,
                        'name': cls['name'],
                        'line': cls['line_number']
                    }
                })
        
        return documents
    
    def _create_structure_documents(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create documents from file structure."""
        documents = []
        
        # Create directory structure document
        dir_info = []
        for directory in structure.get('directories', []):
            dir_info.append(f"Directory: {directory['path']} ({directory['file_count']} files)")
        
        documents.append({
            'id': 'file_structure',
            'content': '\n'.join(dir_info),
            'metadata': {
                'type': 'file_structure',
                'source': 'analysis'
            }
        })
        
        return documents
    
    def _create_dependency_documents(self, dependencies: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Create documents from dependency information."""
        documents = []
        
        for dep_type, deps in dependencies.items():
            if deps:
                documents.append({
                    'id': f'dependencies_{dep_type}',
                    'content': f"{dep_type.title()} Dependencies:\n" + '\n'.join(f"- {dep}" for dep in deps),
                    'metadata': {
                        'type': 'dependencies',
                        'language': dep_type
                    }
                })
        
        return documents
    
    def _generate_embeddings(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for documents (placeholder)."""
        # This would integrate with ChromaDB or similar
        embeddings = []
        for doc in documents:
            embeddings.append({
                'document_id': doc['id'],
                'embedding': [0.0] * 384,  # Placeholder embedding
                'metadata': doc['metadata']
            })
        return embeddings
    
    def _build_vector_index(self, documents: List[Dict[str, Any]], 
                           embeddings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build vector index (placeholder)."""
        # This would integrate with ChromaDB or similar
        return {
            'index_type': 'placeholder',
            'document_count': len(documents),
            'embedding_dimension': 384
        } 