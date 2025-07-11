import streamlit as st
import psycopg2
import psycopg2.extras
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import fnmatch
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

class ConversationMemory:
    """Manages conversation history and context for continuous learning"""
    
    def __init__(self, max_exchanges: int = 10):
        self.max_exchanges = max_exchanges
        self.conversation_history = []
        self.context_insights = {}  # Store learned insights about the system
        
    def add_exchange(self, question: str, response: str, metadata: Dict = None):
        """Add a question-response exchange to memory"""
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'response': response,
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(exchange)
        
        # Keep only recent exchanges to manage memory
        if len(self.conversation_history) > self.max_exchanges:
            self.conversation_history = self.conversation_history[-self.max_exchanges:]
        
        # Extract insights from the conversation
        self._extract_insights(question, response, metadata)
    
    def _extract_insights(self, question: str, response: str, metadata: Dict):
        """Extract and store insights from conversation for learning"""
        question_lower = question.lower()
        
        # Learn about user interests
        if 'agent' in question_lower:
            self.context_insights['user_interested_in_agents'] = True
        if 'performance' in question_lower or 'metric' in question_lower:
            self.context_insights['user_interested_in_performance'] = True
        if 'code' in question_lower or 'implementation' in question_lower:
            self.context_insights['user_interested_in_code'] = True
        if 'error' in question_lower or 'issue' in question_lower:
            self.context_insights['user_interested_in_troubleshooting'] = True
        
        # Learn from metadata
        if metadata:
            if metadata.get('codebase_analyzed'):
                self.context_insights['codebase_accessed'] = True
            system_health = metadata.get('system_health', 0)
            if system_health < 70:
                self.context_insights['system_has_issues'] = True
            elif system_health > 80:
                self.context_insights['system_healthy'] = True
    
    def get_conversation_context(self) -> str:
        """Generate conversation context for LLM"""
        if not self.conversation_history:
            return ""
        
        context_parts = ["=== CONVERSATION HISTORY ==="]
        
        # Add recent exchanges
        for exchange in self.conversation_history[-5:]:  # Last 5 exchanges
            context_parts.append(f"Q: {exchange['question']}")
            context_parts.append(f"A: {exchange['response'][:200]}...")  # Truncate response
            context_parts.append("---")
        
        # Add learned insights
        if self.context_insights:
            context_parts.append("=== LEARNED INSIGHTS ===")
            for insight, value in self.context_insights.items():
                if value:
                    context_parts.append(f"- {insight.replace('_', ' ').title()}")
        
        return "\n".join(context_parts)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation for UI display"""
        return {
            'total_exchanges': len(self.conversation_history),
            'topics_discussed': list(self.context_insights.keys()),
            'recent_questions': [ex['question'] for ex in self.conversation_history[-3:]],
            'first_interaction': self.conversation_history[0]['timestamp'] if self.conversation_history else None,
            'last_interaction': self.conversation_history[-1]['timestamp'] if self.conversation_history else None
        }
    
    def clear_memory(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.context_insights = {}
    
    def export_conversation(self) -> str:
        """Export conversation history as formatted text"""
        if not self.conversation_history:
            return "No conversation history available."
        
        export_parts = ["# AI Help Agent Conversation History\n"]
        export_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        export_parts.append(f"Total Exchanges: {len(self.conversation_history)}\n")
        
        for i, exchange in enumerate(self.conversation_history, 1):
            timestamp = datetime.fromisoformat(exchange['timestamp']).strftime('%H:%M:%S')
            export_parts.append(f"## Exchange {i} ({timestamp})")
            export_parts.append(f"**Question:** {exchange['question']}")
            export_parts.append(f"**Response:** {exchange['response']}")
            export_parts.append("")
        
        return "\n".join(export_parts)

class CodebaseAnalyzer:
    """Analyzes workspace codebase to provide intelligent code insights"""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.file_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.sql': 'SQL',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.env': 'Environment',
            '.toml': 'TOML',
            '.cfg': 'Config'
        }
        
        self.ignore_patterns = [
            '*.git*', '*node_modules*', '*__pycache__*', '*.pyc',
            '*venv*', '*env*', '*.venv*', '*dist*', '*build*',
            '*.log', '*logs*', '*temp*', '*tmp*', '*.cache*',
            '*htmlcov*', '*.coverage*', '*test_results*'
        ]
    
    def analyze_codebase(self, max_files: int = 50, include_full_content: bool = True) -> Dict[str, Any]:
        """Analyze the codebase and return structured information with full file contents"""
        
        analysis = {
            'file_structure': {},
            'languages': {},
            'key_files': [],
            'total_files': 0,
            'total_lines': 0,
            'file_samples': {},
            'full_files': {},  # Store complete file contents
            'architecture_insights': [],
            'code_patterns': {},  # Store detected code patterns
            'imports_map': {},  # Track imports and dependencies
            'functions_map': {},  # Track functions and classes
        }
        
        try:
            # Get all relevant files
            files = self._get_relevant_files(max_files)
            analysis['total_files'] = len(files)
            
            # Analyze each file
            for file_path in files:
                file_info = self._analyze_file(file_path, include_full_content)
                if file_info:
                    rel_path = str(file_path.relative_to(self.workspace_path))
                    
                    # Update language counts
                    lang = file_info['language']
                    if lang not in analysis['languages']:
                        analysis['languages'][lang] = {'count': 0, 'lines': 0}
                    analysis['languages'][lang]['count'] += 1
                    analysis['languages'][lang]['lines'] += file_info['lines']
                    analysis['total_lines'] += file_info['lines']
                    
                    # Store key files with more details
                    if self._is_key_file(file_path):
                        analysis['key_files'].append({
                            'path': rel_path,
                            'type': file_info['language'],
                            'lines': file_info['lines'],
                            'summary': file_info['summary'],
                            'functions': file_info.get('functions', []),
                            'classes': file_info.get('classes', []),
                            'imports': file_info.get('imports', [])
                        })
                    
                    # Store full content for important files
                    if include_full_content and self._is_important_file(file_path):
                        analysis['full_files'][rel_path] = {
                            'content': file_info.get('full_content', ''),
                            'language': file_info['language'],
                            'summary': file_info['summary'],
                            'functions': file_info.get('functions', []),
                            'classes': file_info.get('classes', []),
                            'imports': file_info.get('imports', [])
                        }
                    
                    # Store file samples for UI display
                    if len(analysis['file_samples']) < 10:
                        analysis['file_samples'][rel_path] = file_info['content_sample']
                    
                    # Track code patterns
                    if file_info.get('imports'):
                        analysis['imports_map'][rel_path] = file_info['imports']
                    if file_info.get('functions'):
                        analysis['functions_map'][rel_path] = file_info['functions']
            
            # Generate enhanced architecture insights
            analysis['architecture_insights'] = self._generate_architecture_insights(analysis)
            analysis['code_patterns'] = self._analyze_code_patterns(analysis)
            
        except Exception as e:
            analysis['error'] = f"Error analyzing codebase: {str(e)}"
        
        return analysis
    
    def _get_relevant_files(self, max_files: int) -> List[Path]:
        """Get list of relevant files, filtering out ignored patterns"""
        files = []
        
        for file_path in self.workspace_path.rglob('*'):
            if file_path.is_file() and len(files) < max_files:
                # Check if file should be ignored
                rel_path = str(file_path.relative_to(self.workspace_path))
                if not any(fnmatch.fnmatch(rel_path, pattern) for pattern in self.ignore_patterns):
                    if file_path.suffix in self.file_extensions or file_path.name in ['README.md', 'requirements.txt', 'package.json']:
                        files.append(file_path)
        
        return files
    
    def _analyze_file(self, file_path: Path, include_full_content: bool = True) -> Dict[str, Any]:
        """Analyze individual file and extract comprehensive information"""
        try:
            # Get basic file info
            file_info = {
                'path': file_path,
                'language': self.file_extensions.get(file_path.suffix, 'Unknown'),
                'lines': 0,
                'summary': '',
                'content_sample': '',
                'functions': [],
                'classes': [],
                'imports': [],
                'full_content': ''
            }
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    file_info['lines'] = len(lines)
                    
                    # Store full content if requested
                    if include_full_content:
                        file_info['full_content'] = content
                    
                    # Extract code elements based on file type
                    if file_path.suffix == '.py':
                        file_info.update(self._extract_python_elements(content))
                    elif file_path.suffix in ['.js', '.ts']:
                        file_info.update(self._extract_javascript_elements(content))
                    elif file_path.suffix in ['.yml', '.yaml']:
                        file_info.update(self._extract_yaml_elements(content))
                    
                    # Generate summary based on file type and content
                    file_info['summary'] = self._generate_file_summary(file_path, content, file_info)
                    
                    # Store content sample (first 500 chars for context)
                    file_info['content_sample'] = content[:500] + '...' if len(content) > 500 else content
                    
            except UnicodeDecodeError:
                # Skip binary files
                return None
                
            return file_info
            
        except Exception:
            return None
    
    def _extract_python_elements(self, content: str) -> Dict[str, List]:
        """Extract Python-specific elements like functions, classes, imports"""
        elements = {
            'functions': [],
            'classes': [],
            'imports': []
        }
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            
            # Extract function definitions
            if stripped.startswith('def ') and '(' in stripped:
                func_name = stripped.split('(')[0].replace('def ', '').strip()
                elements['functions'].append({
                    'name': func_name,
                    'line': line_num + 1,
                    'signature': stripped
                })
            
            # Extract class definitions
            elif stripped.startswith('class ') and ':' in stripped:
                class_name = stripped.split(':')[0].replace('class ', '').strip()
                if '(' in class_name:
                    class_name = class_name.split('(')[0].strip()
                elements['classes'].append({
                    'name': class_name,
                    'line': line_num + 1,
                    'definition': stripped
                })
            
            # Extract imports
            elif stripped.startswith(('import ', 'from ')):
                elements['imports'].append({
                    'line': line_num + 1,
                    'statement': stripped
                })
        
        return elements
    
    def _extract_javascript_elements(self, content: str) -> Dict[str, List]:
        """Extract JavaScript/TypeScript elements"""
        elements = {
            'functions': [],
            'classes': [],
            'imports': []
        }
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            
            # Extract function definitions
            if 'function ' in stripped or '=>' in stripped:
                elements['functions'].append({
                    'line': line_num + 1,
                    'definition': stripped
                })
            
            # Extract class definitions
            elif stripped.startswith('class '):
                elements['classes'].append({
                    'line': line_num + 1,
                    'definition': stripped
                })
            
            # Extract imports
            elif stripped.startswith(('import ', 'export ', 'require(')):
                elements['imports'].append({
                    'line': line_num + 1,
                    'statement': stripped
                })
        
        return elements
    
    def _extract_yaml_elements(self, content: str) -> Dict[str, List]:
        """Extract YAML configuration elements"""
        elements = {
            'functions': [],
            'classes': [],
            'imports': [],
            'config_keys': []
        }
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            
            # Extract top-level keys
            if ':' in stripped and not stripped.startswith(' ') and not stripped.startswith('#'):
                key = stripped.split(':')[0].strip()
                elements['config_keys'].append({
                    'key': key,
                    'line': line_num + 1,
                    'definition': stripped
                })
        
        return elements
    
    def _analyze_code_patterns(self, analysis: Dict) -> Dict[str, Any]:
        """Analyze code patterns and relationships"""
        patterns = {
            'common_imports': {},
            'agent_patterns': [],
            'config_patterns': [],
            'test_patterns': []
        }
        
        # Analyze import patterns
        all_imports = []
        for file_imports in analysis['imports_map'].values():
            for imp in file_imports:
                all_imports.append(imp['statement'])
        
        # Count common imports
        from collections import Counter
        import_counter = Counter(all_imports)
        patterns['common_imports'] = dict(import_counter.most_common(10))
        
        # Detect agent patterns
        for file_path, file_info in analysis['full_files'].items():
            if 'agent' in file_path.lower():
                patterns['agent_patterns'].append({
                    'file': file_path,
                    'type': 'agent_implementation',
                    'classes': file_info.get('classes', []),
                    'functions': file_info.get('functions', [])
                })
        
        return patterns
    
    def _generate_file_summary(self, file_path: Path, content: str, file_info: Dict = None) -> str:
        """Generate a comprehensive summary of what the file does"""
        file_name = file_path.name.lower()
        
        if file_info is None:
            file_info = {}
        
        # Get extracted elements
        classes = file_info.get('classes', [])
        functions = file_info.get('functions', [])
        imports = file_info.get('imports', [])
        
        # Generate detailed summary based on content
        if file_path.suffix == '.py':
            summary_parts = []
            
            if classes:
                class_names = [c['name'] for c in classes[:3]]
                summary_parts.append(f"Python module with classes: {', '.join(class_names)}")
            
            if functions:
                func_count = len(functions)
                key_functions = [f['name'] for f in functions[:3] if not f['name'].startswith('_')]
                if key_functions:
                    summary_parts.append(f"{func_count} functions including: {', '.join(key_functions)}")
                else:
                    summary_parts.append(f"{func_count} functions")
            
            if imports:
                key_imports = []
                for imp in imports[:3]:
                    stmt = imp['statement']
                    if 'streamlit' in stmt:
                        key_imports.append('Streamlit UI')
                    elif 'psycopg2' in stmt or 'sqlite' in stmt:
                        key_imports.append('Database')
                    elif 'openai' in stmt:
                        key_imports.append('OpenAI LLM')
                    elif 'agent' in stmt.lower():
                        key_imports.append('Agent framework')
                
                if key_imports:
                    summary_parts.append(f"Uses: {', '.join(key_imports)}")
            
            # Special file type detection
            if 'agent' in file_name:
                summary_parts.insert(0, "Background agent implementation")
            elif 'test' in file_name:
                summary_parts.insert(0, "Test module")
            elif 'config' in file_name:
                summary_parts.insert(0, "Configuration module")
            elif 'main' in file_name or 'app' in file_name:
                summary_parts.insert(0, "Main application module")
            elif 'streamlit' in file_name:
                summary_parts.insert(0, "Streamlit web interface")
            
            return "; ".join(summary_parts) if summary_parts else "Python module"
        
        elif file_path.suffix in ['.yml', '.yaml']:
            config_keys = file_info.get('config_keys', [])
            if config_keys:
                key_names = [k['key'] for k in config_keys[:3]]
                return f"Configuration file with: {', '.join(key_names)}"
            return "Configuration file"
        
        elif file_name == 'requirements.txt':
            return "Python dependencies"
        
        elif file_name == 'readme.md':
            return "Project documentation"
        
        elif file_name == 'dockerfile':
            return "Docker container configuration"
        
        elif file_path.suffix == '.sql':
            return "Database schema/queries"
        
        elif file_path.suffix == '.json':
            return "JSON configuration/data"
        
        return f"{self.file_extensions.get(file_path.suffix, 'Unknown')} file"
    
    def _is_key_file(self, file_path: Path) -> bool:
        """Determine if a file is considered a key file"""
        file_name = file_path.name.lower()
        key_names = ['main', 'app', 'index', 'config', 'settings', 'agent', 'init', 'setup', 'launch']
        return any(key in file_name for key in key_names) or file_name == 'readme.md'
    
    def _is_important_file(self, file_path: Path) -> bool:
        """Determine if file should be included in samples"""
        file_name = file_path.name.lower()
        important_patterns = ['agent', 'main', 'app', 'config', 'setup', 'launch', 'background']
        return any(pattern in file_name for pattern in important_patterns) or file_path.suffix == '.py'
    
    def _generate_architecture_insights(self, analysis: Dict) -> List[str]:
        """Generate insights about the codebase architecture"""
        insights = []
        
        # Language distribution insights
        if analysis['languages']:
            primary_lang = max(analysis['languages'].items(), key=lambda x: x[1]['lines'])
            insights.append(f"Primary language: {primary_lang[0]} ({primary_lang[1]['lines']} lines)")
        
        # File structure insights
        total_files = analysis['total_files']
        if total_files > 50:
            insights.append(f"Large codebase with {total_files} files")
        elif total_files > 20:
            insights.append(f"Medium-sized project with {total_files} files")
        else:
            insights.append(f"Small project with {total_files} files")
        
        # Architecture patterns
        key_files = [f['path'] for f in analysis['key_files']]
        if any('agent' in f for f in key_files):
            insights.append("Agent-based architecture detected")
        if any('background' in f for f in key_files):
            insights.append("Background processing system")
        if 'requirements.txt' in [f['path'] for f in analysis['key_files']]:
            insights.append("Python project with dependency management")
        
        return insights
    
    def get_file_content(self, file_path: str, max_lines: int = 100) -> str:
        """Get content of specific file for detailed analysis"""
        try:
            full_path = self.workspace_path / file_path
            if full_path.exists() and full_path.is_file():
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) <= max_lines:
                        return ''.join(lines)
                    else:
                        return ''.join(lines[:max_lines]) + f"\n... (truncated, {len(lines)} total lines)"
            else:
                return f"File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def find_files_by_pattern(self, pattern: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Find files by name pattern or functionality"""
        if not hasattr(self, '_file_index'):
            # Build file index if not already done
            self.analyze_codebase()
        
        results = []
        pattern_lower = pattern.lower()
        
        # Search in analyzed files
        analysis = getattr(self, '_analysis_cache', self.analyze_codebase())
        
        for file_path, file_info in analysis.get('full_files', {}).items():
            # Search by file name
            if pattern_lower in file_path.lower():
                results.append({
                    'path': file_path,
                    'type': 'filename_match',
                    'summary': file_info.get('summary', ''),
                    'relevance_score': 10
                })
            
            # Search by function names
            for func in file_info.get('functions', []):
                if pattern_lower in func['name'].lower():
                    results.append({
                        'path': file_path,
                        'type': 'function_match',
                        'function': func['name'],
                        'summary': file_info.get('summary', ''),
                        'relevance_score': 8
                    })
            
            # Search by class names
            for cls in file_info.get('classes', []):
                if pattern_lower in cls['name'].lower():
                    results.append({
                        'path': file_path,
                        'type': 'class_match',
                        'class': cls['name'],
                        'summary': file_info.get('summary', ''),
                        'relevance_score': 8
                    })
            
            # Search in file content (for important matches)
            if pattern_lower in file_info.get('content', '').lower():
                results.append({
                    'path': file_path,
                    'type': 'content_match',
                    'summary': file_info.get('summary', ''),
                    'relevance_score': 5
                })
        
        # Sort by relevance and remove duplicates
        seen_files = set()
        unique_results = []
        for result in sorted(results, key=lambda x: x['relevance_score'], reverse=True):
            if result['path'] not in seen_files:
                unique_results.append(result)
                seen_files.add(result['path'])
        
        return unique_results[:max_results]
    
    def get_related_files(self, file_path: str) -> List[Dict[str, Any]]:
        """Get files related to a given file (imports, similar functionality)"""
        analysis = getattr(self, '_analysis_cache', self.analyze_codebase())
        
        if file_path not in analysis.get('full_files', {}):
            return []
        
        file_info = analysis['full_files'][file_path]
        related = []
        
        # Find files with similar imports
        file_imports = set(imp['statement'] for imp in file_info.get('imports', []))
        
        for other_path, other_info in analysis['full_files'].items():
            if other_path == file_path:
                continue
            
            other_imports = set(imp['statement'] for imp in other_info.get('imports', []))
            
            # Calculate import similarity
            if file_imports and other_imports:
                common_imports = file_imports.intersection(other_imports)
                similarity = len(common_imports) / len(file_imports.union(other_imports))
                
                if similarity > 0.2:  # At least 20% similarity
                    related.append({
                        'path': other_path,
                        'relationship': 'similar_imports',
                        'similarity_score': similarity,
                        'common_imports': list(common_imports)[:3]
                    })
        
        return sorted(related, key=lambda x: x['similarity_score'], reverse=True)[:5]
    
    def get_code_context_for_query(self, query: str) -> Dict[str, Any]:
        """Get relevant code context for a specific query"""
        context = {
            'relevant_files': [],
            'code_snippets': {},
            'architecture_overview': {}
        }
        
        query_lower = query.lower()
        analysis = getattr(self, '_analysis_cache', self.analyze_codebase(max_files=150))
        
        # Find relevant files based on query keywords
        relevant_files = []
        
        # Enhanced keyword mapping for better search including RAG system
        keyword_mappings = {
            'health': ['health', 'monitor', 'heartbeat'],
            'agent': ['agent', 'background', 'worker'],
            'database': ['database', 'db', 'postgresql', 'sql'],
            'config': ['config', 'setting', 'env'],
            'api': ['api', 'endpoint', 'route'],
            'ui': ['streamlit', 'interface', 'ui', 'web'],
            'memory': ['memory', 'cache', 'storage'],
            'performance': ['performance', 'metric', 'monitoring'],
            'rag': ['rag', 'retrieval', 'enhanced', 'vector', 'embedding', 'semantic', 'chromadb'],
            'enhanced': ['enhanced', 'vector', 'embedding', 'chromadb', 'semantic', 'retrieval'],
            'vector': ['vector', 'embedding', 'chromadb', 'semantic', 'similarity'],
            'search': ['search', 'retrieval', 'semantic', 'vector', 'similarity']
        }
        
        # Expand query with related keywords
        expanded_keywords = []
        for keyword, synonyms in keyword_mappings.items():
            if any(syn in query_lower for syn in synonyms):
                expanded_keywords.extend(synonyms)
        
        # Search for relevant files
        for file_path, file_info in analysis.get('full_files', {}).items():
            relevance_score = 0
            
            # Check file path
            for keyword in expanded_keywords:
                if keyword in file_path.lower():
                    relevance_score += 10
            
            # Check file summary
            summary = file_info.get('summary', '').lower()
            for keyword in expanded_keywords:
                if keyword in summary:
                    relevance_score += 5
            
            # Check function/class names
            for func in file_info.get('functions', []):
                for keyword in expanded_keywords:
                    if keyword in func['name'].lower():
                        relevance_score += 8
            
            for cls in file_info.get('classes', []):
                for keyword in expanded_keywords:
                    if keyword in cls['name'].lower():
                        relevance_score += 8
            
            if relevance_score > 0:
                relevant_files.append({
                    'path': file_path,
                    'relevance_score': relevance_score,
                    'file_info': file_info
                })
        
        # Sort and select top relevant files
        relevant_files.sort(key=lambda x: x['relevance_score'], reverse=True)
        context['relevant_files'] = relevant_files[:5]
        
        # Extract code snippets from top relevant files
        for file_data in relevant_files[:3]:
            file_path = file_data['path']
            file_info = file_data['file_info']
            
            # Get key functions/classes
            key_elements = []
            for func in file_info.get('functions', [])[:3]:
                key_elements.append(f"Function: {func['name']} (line {func['line']})")
            for cls in file_info.get('classes', [])[:2]:
                key_elements.append(f"Class: {cls['name']} (line {cls['line']})")
            
            context['code_snippets'][file_path] = {
                'summary': file_info.get('summary', ''),
                'key_elements': key_elements,
                'content_preview': file_info.get('content', '')[:1000] + '...' if len(file_info.get('content', '')) > 1000 else file_info.get('content', '')
            }
        
        return context

class LLMResponseGenerator:
    """LLM-powered response generator for intelligent explanations"""
    
    def __init__(self):
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.llm_available = True
        else:
            self.client = None
            self.llm_available = False
        
    def generate_intelligent_response(self, query: str, system_data: Dict, context: str = "") -> str:
        """Generate LLM-powered intelligent response with system data analysis"""
        
        # Create comprehensive system prompt
        codebase_info = ""
        if system_data.get('codebase_available'):
            codebase_info = f"\n- Codebase: {system_data.get('total_code_files', 0)} files, {system_data.get('total_code_lines', 0)} lines analyzed"
        
        system_prompt = f"""You are an expert AI system administrator and software development assistant with deep expertise in:
1. Background agent system monitoring and analysis
2. Codebase understanding and development support
3. Software architecture analysis and guidance
4. Code debugging and troubleshooting assistance

You have access to:
- Real-time system operational data (agents, metrics, events)
- Complete codebase analysis with actual source code
- File-level details including functions, classes, and imports
- Code relationship mapping and dependency analysis
- Historical conversation context for continuous learning

Key Responsibilities:
- Analyze system health and performance data with specific insights
- Provide in-depth code analysis and development guidance
- Help users navigate, understand, and modify their codebase
- Identify potential issues and provide actionable solutions
- Explain complex technical concepts in clear, practical terms
- Offer specific code examples and implementation suggestions
- Guide users through debugging and troubleshooting processes
- Recommend best practices for both system operations and code development

Current System Context:
- System Health: {system_data.get('system_health', 'Unknown')}%
- Active Agents: {system_data.get('active_agents', 0)}/{system_data.get('total_agents', 0)}
- Recent Metrics: {system_data.get('recent_metrics', 0)} in last hour
- Recent Events: {system_data.get('recent_events', 0)} in last hour
- Total Data: {system_data.get('total_metrics', 0)} metrics, {system_data.get('total_events', 0)} events{codebase_info}

Code Analysis Capabilities:
- Files Analyzed: {system_data.get('total_code_files', 0)} files, {system_data.get('total_code_lines', 0)} lines
- Relevant Code Context: {'Available' if system_data.get('code_context_available') else 'General overview only'}
- Query-Specific Files: {system_data.get('relevant_files_found', 0)} files found for this query

Instructions for Responses:
- Ground all responses in actual data provided (system metrics + real code)
- When discussing code, provide specific file paths, function names, and line numbers
- Include actual code snippets when relevant to the user's question
- Offer concrete implementation suggestions and code modifications
- Explain how code relates to system behavior and performance
- Provide step-by-step guidance for development tasks
- Help users understand code architecture and relationships
- Identify specific areas for improvement or debugging
- Reference previous conversation context when building on earlier discussions
- Be practical, actionable, and developer-focused in your assistance"""

        # Create user prompt with data context
        user_prompt = f"""User Query: {query}

{context}

Please analyze this system data and provide a comprehensive, intelligent response that:
1. Directly addresses the user's question
2. Provides insights based on the actual system data
3. Explains what the data means in practical terms
4. Offers specific recommendations if issues are detected
5. Highlights any notable patterns or trends

Make your response informative, actionable, and based on the real data provided."""

        # Check if LLM is available
        if not self.llm_available or not self.client:
            return f"⚠️ **LLM Analysis Not Configured**\n\nOpenAI API key not found. Here's what I can tell you from your system data:\n\n" + self._generate_fallback_response(query, system_data, context)
        
        try:
            # Generate LLM response using new OpenAI client
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to descriptive error message
            return f"⚠️ **LLM Analysis Temporarily Unavailable**\n\nI can see your system data but can't generate the full AI analysis right now (Error: {str(e)}). Here's what I observe from your data:\n\n" + self._generate_fallback_response(query, system_data, context)
    
    def _generate_fallback_response(self, query: str, system_data: Dict, context: str) -> str:
        """Generate fallback response when LLM is unavailable"""
        health = system_data.get('system_health', 0)
        active = system_data.get('active_agents', 0)
        total = system_data.get('total_agents', 0)
        
        response = f"**System Overview**: {health}% health with {active}/{total} agents active\n\n"
        
        if health < 70:
            response += f"⚠️ **Attention Needed**: System health at {health}% indicates issues\n"
        elif health >= 80:
            response += f"✅ **System Healthy**: {health}% health is good\n"
        
        if active < total:
            response += f"🔍 **{total - active} Agents Offline**: May need investigation\n"
        
        response += f"\n📊 **Recent Activity**: {system_data.get('recent_metrics', 0)} metrics, {system_data.get('recent_events', 0)} events collected in the last hour"
        
        return response

# Configure Streamlit page
st.set_page_config(
    page_title="🤖 AI Help Agent - System Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SyncDatabaseClient:
    """Synchronous database client that avoids async conflicts with background agents"""
    
    def __init__(self):
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Create synchronous database connection"""
        try:
            # Database configuration
            host = os.getenv('POSTGRESQL_HOST', 'localhost')
            port = int(os.getenv('POSTGRESQL_PORT', 5432))
            database = os.getenv('POSTGRESQL_DATABASE', 'background_agents')
            user = os.getenv('POSTGRESQL_USER', 'postgres')
            password = os.getenv('POSTGRESQL_PASSWORD', '')
            
            # Use psycopg2 for synchronous operations (no conflict with asyncpg pools)
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                application_name='streamlit_ai_help_agent'
            )
            
            print("✅ Synchronous database connection established")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.connection = None
    
    def get_agents_data(self):
        """Get agents data using synchronous query"""
        if not self.connection:
            return []
            
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT agent_id, agent_type, state, capabilities, created_at, last_seen
                    FROM agents 
                    ORDER BY created_at DESC
                """)
                
                agents = cursor.fetchall()
                return [dict(agent) for agent in agents]
                
        except Exception as e:
            print(f"Error getting agents: {e}")
            return []
    
    def get_performance_metrics(self, hours=24):
        """Get performance metrics using synchronous query"""
        if not self.connection:
            return []
            
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT metric_name, metric_value, metric_unit, agent_id, timestamp
                    FROM performance_metrics 
                    WHERE timestamp > NOW() - INTERVAL %s
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (f"{hours} hours",))
                
                metrics = cursor.fetchall()
                return [dict(metric) for metric in metrics]
                
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return []
    
    def get_system_events(self, hours=24):
        """Get system events using synchronous query"""
        if not self.connection:
            return []
            
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT event_type, event_data, agent_id, severity, timestamp
                    FROM system_events 
                    WHERE timestamp > NOW() - INTERVAL %s
                    ORDER BY timestamp DESC
                    LIMIT 50
                """, (f"{hours} hours",))
                
                events = cursor.fetchall()
                return [dict(event) for event in events]
                
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    def get_system_summary(self):
        """Get comprehensive system summary"""
        if not self.connection:
            return {}
            
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get agent counts
                cursor.execute("SELECT COUNT(*) as total_agents FROM agents")
                total_agents = cursor.fetchone()['total_agents']
                
                cursor.execute("SELECT COUNT(*) as active_agents FROM agents WHERE state = 'active'")
                active_agents = cursor.fetchone()['active_agents']
                
                # Get recent activity counts
                cursor.execute("""
                    SELECT COUNT(*) as recent_metrics 
                    FROM performance_metrics 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                """)
                recent_metrics = cursor.fetchone()['recent_metrics']
                
                cursor.execute("""
                    SELECT COUNT(*) as recent_events 
                    FROM system_events 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                """)
                recent_events = cursor.fetchone()['recent_events']
                
                return {
                    'total_agents': total_agents,
                    'active_agents': active_agents,
                    'recent_metrics': recent_metrics,
                    'recent_events': recent_events,
                    'system_health': round((active_agents / total_agents * 100) if total_agents > 0 else 0, 1)
                }
                
        except Exception as e:
            print(f"Error getting system summary: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("✅ Database connection closed")

class StreamlitAIHelpAgent:
    """AI Help Agent designed specifically for Streamlit with LLM intelligence"""
    
    def __init__(self):
        self.db_client = SyncDatabaseClient()
        self.llm_generator = LLMResponseGenerator()
        self.codebase_analyzer = CodebaseAnalyzer()
        self.conversation_memory = ConversationMemory()
        self.agent_id = "streamlit_ai_help_agent"
        
        # Cache codebase analysis (expensive operation)
        self._codebase_analysis = None
        
        # Enhanced RAG system status tracking
        self.enhanced_rag_available = False
        self.rag_status = {
            'system_status': 'checking',
            'documents_indexed': 0,
            'vector_store_ready': False,
            'last_indexing': None,
            'fallback_count': 0,
            'semantic_accuracy': 0.0
        }
        
        # Check enhanced RAG availability on initialization
        self._check_enhanced_rag_availability()
    
    def _check_enhanced_rag_availability(self):
        """Check if enhanced RAG system is available from background agent"""
        try:
            # Try to check if background AI Help Agent is running with enhanced RAG
            # This would typically connect to the background agent's status endpoint
            agents_data = self.db_client.get_agents_data()
            
            # Look for AI Help Agent with enhanced RAG
            for agent in agents_data:
                if agent.get('agent_id') == 'ai_help_agent' and agent.get('state') == 'active':
                    # Check if this agent has enhanced RAG capabilities
                    # This would be determined by checking agent metadata or status
                    self.enhanced_rag_available = True
                    self.rag_status['system_status'] = 'available'
                    break
            else:
                self.rag_status['system_status'] = 'not_available'
                
        except Exception as e:
            self.rag_status['system_status'] = 'error'
            self.rag_status['error'] = str(e)
    
    def get_enhanced_rag_status(self) -> Dict[str, Any]:
        """Get current enhanced RAG system status"""
        return {
            'enhanced_rag_available': self.enhanced_rag_available,
            'rag_status': self.rag_status,
            'integration_level': 'streamlit_frontend',
            'background_agent_connection': 'active' if self.enhanced_rag_available else 'inactive'
        }
    
    def process_help_request(self, question: str, context: Dict = None) -> Dict[str, Any]:
        """Process help request with conversation memory and return intelligent response"""
        start_time = time.time()
        
        try:
            # Gather system data
            agents_data = self.db_client.get_agents_data()
            metrics_data = self.db_client.get_performance_metrics()
            events_data = self.db_client.get_system_events()
            system_summary = self.db_client.get_system_summary()
            
            # Check if question is code-related and analyze codebase if needed
            codebase_analysis = None
            code_context = None
            if self._is_code_related_query(question):
                codebase_analysis = self._get_codebase_analysis()
                code_context = self._get_enhanced_code_context(question)
            
            # Generate response based on query type with conversation context
            response_text = self._generate_intelligent_response(
                question, agents_data, metrics_data, events_data, system_summary, codebase_analysis, code_context
            )
            
            processing_time = time.time() - start_time
            
            # Prepare metadata for conversation memory
            conversation_metadata = {
                'agents_count': len(agents_data),
                'metrics_count': len(metrics_data),
                'events_count': len(events_data),
                'codebase_analyzed': codebase_analysis is not None,
                'total_files': codebase_analysis.get('total_files', 0) if codebase_analysis else 0,
                'system_health': system_summary.get('system_health', 0),
                'processing_time': processing_time
            }
            
            # Store this exchange in conversation memory
            self.conversation_memory.add_exchange(question, response_text, conversation_metadata)
            
            return {
                'success': True,
                'response': response_text,
                'processing_time': processing_time,
                'data_sources': conversation_metadata,
                'system_health': system_summary.get('system_health', 0),
                'conversation_summary': self.conversation_memory.get_conversation_summary(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_response = f"I encountered an error while processing your request: {e}"
            
            # Store error in conversation memory too
            self.conversation_memory.add_exchange(question, error_response, {'error': True})
            
            return {
                'success': False,
                'error': str(e),
                'response': error_response,
                'processing_time': time.time() - start_time,
                'conversation_summary': self.conversation_memory.get_conversation_summary(),
                'timestamp': datetime.now().isoformat()
            }
    
    def _is_code_related_query(self, question: str) -> bool:
        """Determine if the question requires codebase analysis"""
        code_keywords = [
            'code', 'file', 'function', 'class', 'implementation', 'directory',
            'structure', 'architecture', 'agent', 'module', 'script', 'repository',
            'project', 'workspace', 'codebase', 'python', 'config', 'show me',
            'find', 'where', 'how is', 'point me', 'navigate', 'locate',
            'develop', 'build', 'create', 'modify', 'understand', 'explain',
            'help me with', 'assist', 'guide', 'troubleshoot', 'debug'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in code_keywords)
    
    def _get_enhanced_code_context(self, question: str) -> Dict[str, Any]:
        """Get enhanced code context specifically relevant to the question"""
        return self.codebase_analyzer.get_code_context_for_query(question)
    
    def _get_codebase_analysis(self) -> Dict[str, Any]:
        """Get codebase analysis with automatic refresh detection"""
        # Check if we need to refresh the cache
        if self._should_refresh_codebase_analysis():
            self._codebase_analysis = None  # Force refresh
        
        if self._codebase_analysis is None:
            # Increase max_files to catch new files like enhanced_rag_system.py
            self._codebase_analysis = self.codebase_analyzer.analyze_codebase(max_files=150)
            # Cache in analyzer for other methods
            self.codebase_analyzer._analysis_cache = self._codebase_analysis
            # Store timestamp for refresh detection
            self._codebase_analysis_timestamp = time.time()
        return self._codebase_analysis
    
    def _should_refresh_codebase_analysis(self) -> bool:
        """Check if codebase analysis should be refreshed"""
        # Refresh if cache is older than 5 minutes or doesn't exist
        if not hasattr(self, '_codebase_analysis_timestamp'):
            return True
        
        cache_age = time.time() - self._codebase_analysis_timestamp
        if cache_age > 300:  # 5 minutes
            return True
        
        # Check if enhanced RAG file is missing from current analysis
        if self._codebase_analysis:
            # Check for enhanced RAG system (normalize path separators)
            enhanced_rag_files = [
                path for path in self._codebase_analysis.get('full_files', {}).keys()
                if 'enhanced_rag_system.py' in path.replace('\\', '/')
            ]
            if not enhanced_rag_files:
                return True
        
        return False
    
    def force_refresh_codebase_analysis(self):
        """Force refresh of codebase analysis"""
        self._codebase_analysis = None
        if hasattr(self, '_codebase_analysis_timestamp'):
            del self._codebase_analysis_timestamp
    
    def get_file_content(self, file_path: str, max_lines: int = 100) -> str:
        """Get content of specific file for detailed analysis"""
        return self.codebase_analyzer.get_file_content(file_path, max_lines)
    
    def _generate_intelligent_response(self, query: str, agents_data: List, metrics_data: List, 
                                     events_data: List, system_summary: Dict, codebase_analysis: Dict = None, code_context: Dict = None) -> str:
        """Generate LLM-powered intelligent response with real system data and detailed code analysis"""
        
        # Prepare comprehensive context for LLM
        context = self._prepare_system_context(agents_data, metrics_data, events_data, system_summary, codebase_analysis, code_context)
        
        # Enhanced system data for LLM
        enhanced_system_data = {
            **system_summary,
            'total_metrics': len(metrics_data),
            'total_events': len(events_data),
            'agents_data_available': len(agents_data) > 0,
            'metrics_data_available': len(metrics_data) > 0,
            'events_data_available': len(events_data) > 0,
            'codebase_available': codebase_analysis is not None,
            'total_code_files': codebase_analysis.get('total_files', 0) if codebase_analysis else 0,
            'total_code_lines': codebase_analysis.get('total_lines', 0) if codebase_analysis else 0,
            'code_context_available': code_context is not None,
            'relevant_files_found': len(code_context.get('relevant_files', [])) if code_context else 0
        }
        
        # Use LLM to generate intelligent response
        return self.llm_generator.generate_intelligent_response(query, enhanced_system_data, context)
    
    def _prepare_system_context(self, agents_data: List, metrics_data: List, events_data: List, system_summary: Dict, codebase_analysis: Dict = None, code_context: Dict = None) -> str:
        """Prepare comprehensive system context including conversation history and detailed code analysis"""
        
        context_parts = []
        
        # Add conversation history context if available
        conversation_context = self.conversation_memory.get_conversation_context()
        if conversation_context:
            context_parts.append(conversation_context)
        
        # Agents context
        if agents_data:
            agent_states = {}
            agent_types = {}
            inactive_agents = []
            
            for agent in agents_data:
                state = agent['state']
                agent_type = agent['agent_type']
                agent_states[state] = agent_states.get(state, 0) + 1
                agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
                
                if state != 'active':
                    inactive_agents.append(f"{agent['agent_id']} ({agent_type}, {state})")
            
            agents_context = f"AGENTS DATA:\n"
            agents_context += f"- States: {dict(agent_states)}\n"
            agents_context += f"- Types: {dict(agent_types)}\n"
            if inactive_agents:
                agents_context += f"- Inactive Agents: {', '.join(inactive_agents[:5])}\n"
            context_parts.append(agents_context)
        
        # Metrics context
        if metrics_data:
            metric_types = {}
            recent_metrics = []
            
            for metric in metrics_data[:10]:  # Last 10 metrics
                metric_name = metric['metric_name']
                metric_types[metric_name] = metric_types.get(metric_name, 0) + 1
                recent_metrics.append(f"{metric_name}: {metric['metric_value']} {metric.get('metric_unit', '')}")
            
            metrics_context = f"PERFORMANCE METRICS:\n"
            metrics_context += f"- Top Metric Types: {dict(sorted(metric_types.items(), key=lambda x: x[1], reverse=True)[:5])}\n"
            metrics_context += f"- Recent Values: {'; '.join(recent_metrics[:5])}\n"
            context_parts.append(metrics_context)
        
        # Events context
        if events_data:
            event_types = {}
            severities = {}
            recent_events = []
            
            for event in events_data[:10]:  # Last 10 events
                event_type = event['event_type']
                severity = event.get('severity', 'INFO')
                event_types[event_type] = event_types.get(event_type, 0) + 1
                severities[severity] = severities.get(severity, 0) + 1
                recent_events.append(f"{event_type} ({severity})")
            
            events_context = f"SYSTEM EVENTS:\n"
            events_context += f"- Event Types: {dict(sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:5])}\n"
            events_context += f"- Severities: {dict(severities)}\n"
            events_context += f"- Recent Events: {'; '.join(recent_events[:5])}\n"
            context_parts.append(events_context)
        
        # Codebase analysis context
        if codebase_analysis and not codebase_analysis.get('error'):
            codebase_context = f"CODEBASE ANALYSIS:\n"
            codebase_context += f"- Total Files: {codebase_analysis.get('total_files', 0)}\n"
            codebase_context += f"- Total Lines: {codebase_analysis.get('total_lines', 0)}\n"
            
            # Language breakdown
            languages = codebase_analysis.get('languages', {})
            if languages:
                codebase_context += f"- Languages: {dict(sorted(languages.items(), key=lambda x: x[1]['lines'], reverse=True))}\n"
            
            # Architecture insights
            insights = codebase_analysis.get('architecture_insights', [])
            if insights:
                codebase_context += f"- Architecture: {'; '.join(insights)}\n"
            
            # Key files
            key_files = codebase_analysis.get('key_files', [])
            if key_files:
                key_file_info = [f"{f['path']} ({f['type']}, {f['lines']} lines)" for f in key_files[:5]]
                codebase_context += f"- Key Files: {'; '.join(key_file_info)}\n"
            
            # File samples for code context
            file_samples = codebase_analysis.get('file_samples', {})
            if file_samples:
                codebase_context += f"- Code Samples Available: {list(file_samples.keys())[:3]}\n"
            
            context_parts.append(codebase_context)
        
        # Enhanced code context for specific queries
        if code_context and code_context.get('relevant_files'):
            code_detail_context = f"RELEVANT CODE ANALYSIS:\n"
            
            # Add relevant files with their details
            for file_data in code_context['relevant_files'][:3]:  # Top 3 relevant files
                file_path = file_data['path']
                file_info = file_data['file_info']
                
                code_detail_context += f"- File: {file_path} (relevance: {file_data['relevance_score']})\n"
                code_detail_context += f"  Summary: {file_info.get('summary', 'N/A')}\n"
                
                # Add functions and classes
                functions = file_info.get('functions', [])
                if functions:
                    func_names = [f['name'] for f in functions[:3]]
                    code_detail_context += f"  Functions: {', '.join(func_names)}\n"
                
                classes = file_info.get('classes', [])
                if classes:
                    class_names = [c['name'] for c in classes[:2]]
                    code_detail_context += f"  Classes: {', '.join(class_names)}\n"
                
                code_detail_context += "\n"
            
            # Add actual code snippets for the most relevant files
            code_snippets = code_context.get('code_snippets', {})
            if code_snippets:
                code_detail_context += "CODE SNIPPETS:\n"
                for file_path, snippet_info in list(code_snippets.items())[:2]:  # Top 2 files
                    code_detail_context += f"--- {file_path} ---\n"
                    code_detail_context += f"Summary: {snippet_info.get('summary', '')}\n"
                    
                    # Add key elements
                    key_elements = snippet_info.get('key_elements', [])
                    if key_elements:
                        code_detail_context += f"Key Elements: {'; '.join(key_elements)}\n"
                    
                    # Add code preview
                    content_preview = snippet_info.get('content_preview', '')
                    if content_preview:
                        code_detail_context += f"Code Preview:\n{content_preview}\n"
                    
                    code_detail_context += "\n"
            
            context_parts.append(code_detail_context)
        
        # System trends and insights
        health = system_summary.get('system_health', 0)
        active_agents = system_summary.get('active_agents', 0)
        total_agents = system_summary.get('total_agents', 0)
        
        trends_context = f"SYSTEM ANALYSIS:\n"
        trends_context += f"- Health Status: {health}% ({'Excellent' if health >= 80 else 'Good' if health >= 60 else 'Needs Attention'})\n"
        trends_context += f"- Agent Availability: {active_agents}/{total_agents} ({(active_agents/total_agents*100) if total_agents > 0 else 0:.1f}%)\n"
        trends_context += f"- Recent Activity Level: {system_summary.get('recent_metrics', 0)} metrics, {system_summary.get('recent_events', 0)} events\n"
        
        if health < 70:
            trends_context += f"- ALERT: System health below optimal threshold\n"
        if active_agents < total_agents:
            trends_context += f"- CONCERN: {total_agents - active_agents} agents offline\n"
        
        context_parts.append(trends_context)
        
        return "\n\n".join(context_parts)
    
    def _generate_status_response(self, summary: Dict, agents: List, metrics: List, events: List) -> str:
        health = summary.get('system_health', 0)
        active = summary.get('active_agents', 0) 
        total = summary.get('total_agents', 0)
        
        status_emoji = "🟢" if health >= 80 else "🟡" if health >= 60 else "🔴"
        
        response = f"{status_emoji} **System Health: {health}%**\n\n"
        response += f"🤖 **Agents**: {active}/{total} active\n"
        response += f"📊 **Recent Activity**: {summary.get('recent_metrics', 0)} metrics, {summary.get('recent_events', 0)} events (last hour)\n\n"
        
        if health < 80:
            inactive_count = total - active
            response += f"⚠️ **Attention**: {inactive_count} agents are currently inactive.\n"
        
        response += f"📈 **Data Collection**: {len(metrics)} metrics and {len(events)} events available for analysis."
        
        return response
    
    def _generate_agents_response(self, summary: Dict, agents: List) -> str:
        active = summary.get('active_agents', 0)
        total = summary.get('total_agents', 0)
        inactive = total - active
        
        response = f"🤖 **Agent Status Report**\n\n"
        response += f"• **Active Agents**: {active}\n"
        response += f"• **Total Agents**: {total}\n"
        
        if inactive > 0:
            response += f"• **Inactive Agents**: {inactive}\n\n"
            response += "**Recent Agents**:\n"
            for agent in agents[:5]:
                status_emoji = "🟢" if agent['state'] == 'active' else "🔴"
                response += f"{status_emoji} {agent['agent_id']} ({agent['agent_type']})\n"
        else:
            response += "\n✅ All agents are currently active and operational!"
        
        return response
    
    def _generate_performance_response(self, metrics: List, summary: Dict) -> str:
        response = f"📊 **Performance Overview**\n\n"
        response += f"• **Recent Metrics**: {summary.get('recent_metrics', 0)} (last hour)\n"
        response += f"• **Total Metrics**: {len(metrics)} available\n\n"
        
        if metrics:
            # Group metrics by type
            metric_types = {}
            for metric in metrics:
                metric_name = metric['metric_name']
                if metric_name not in metric_types:
                    metric_types[metric_name] = []
                metric_types[metric_name].append(metric)
            
            response += "**Top Metric Types**:\n"
            for metric_name, metric_list in list(metric_types.items())[:5]:
                response += f"• {metric_name}: {len(metric_list)} measurements\n"
        else:
            response += "⚠️ No recent performance metrics available."
        
        return response
    
    def _generate_issues_response(self, events: List, agents: List, summary: Dict) -> str:
        active = summary.get('active_agents', 0)
        total = summary.get('total_agents', 0)
        inactive = total - active
        
        response = f"🔍 **System Issues Analysis**\n\n"
        
        if inactive == 0:
            response += "✅ **No major issues detected!**\n"
            response += f"All {total} agents are active and operational.\n\n"
        else:
            response += f"⚠️ **Issues Found**: {inactive} agents are inactive\n\n"
            response += "**Inactive Agents**:\n"
            for agent in agents:
                if agent['state'] != 'active':
                    response += f"🔴 {agent['agent_id']} - {agent['state']}\n"
        
        # Check recent error events
        error_events = [e for e in events if e.get('severity') in ['ERROR', 'CRITICAL']]
        if error_events:
            response += f"\n🚨 **Recent Errors**: {len(error_events)} error events detected\n"
            for event in error_events[:3]:
                response += f"• {event['event_type']} - {event['timestamp']}\n"
        
        return response
    
    def _generate_events_response(self, events: List, summary: Dict) -> str:
        response = f"📝 **Recent System Activity**\n\n"
        response += f"• **Recent Events**: {summary.get('recent_events', 0)} (last hour)\n"
        response += f"• **Total Events**: {len(events)} available\n\n"
        
        if events:
            # Group events by type
            event_types = {}
            for event in events:
                event_type = event['event_type']
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            response += "**Event Types**:\n"
            for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                response += f"• {event_type}: {count} events\n"
            
            response += "\n**Latest Events**:\n"
            for event in events[:5]:
                severity_emoji = {"ERROR": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(event.get('severity', 'INFO'), "🔵")
                response += f"{severity_emoji} {event['event_type']} - {event['timestamp']}\n"
        
        return response
    
    def _generate_help_response(self) -> str:
        return """🤖 **AI Help Agent Capabilities**

I can help you with:

🔍 **System Status**
• "What's the current system status?"
• "How is the system health?"
• "Give me a system overview"

🤖 **Agent Information**  
• "How many agents are running?"
• "Which agents are active?"
• "Are there any inactive agents?"

📊 **Performance Metrics**
• "Show me performance data"
• "What metrics are being collected?"
• "How is the system performing?"

🚨 **Issue Detection**
• "Are there any issues?"
• "What problems exist?"
• "Show me recent errors"

📝 **System Activity**
• "What's happening recently?"
• "Show me recent events"
• "What's the latest activity?"

Just ask me anything about your background agents system!"""
    
    def _generate_ui_explanation_response(self, summary: Dict, query: str) -> str:
        """Generate dynamic UI explanation based on current system state"""
        health = summary.get('system_health', 0)
        active = summary.get('active_agents', 0)
        total = summary.get('total_agents', 0)
        
        response = f"🖥️ **How to Use This AI Help Interface**\n\n"
        response += f"You're currently looking at your background agents monitoring system. "
        response += f"Right now, you have **{active} out of {total} agents running** with **{health}% system health**.\n\n"
        
        response += "**📊 Sidebar Information:**\n"
        response += f"• **System Health**: {health}% - {'🟢 Great!' if health >= 80 else '🟡 Needs attention' if health >= 60 else '🔴 Critical'}\n"
        response += f"• **Active Agents**: {active}/{total} - {'All systems operational' if active == total else f'{total-active} agents need attention'}\n"
        response += f"• **Recent Metrics**: {summary.get('recent_metrics', 0)} data points collected in the last hour\n"
        response += f"• **Recent Events**: {summary.get('recent_events', 0)} system events logged recently\n\n"
        
        response += "**💬 How to Ask Questions:**\n"
        response += "• **System Status**: 'What's my system health?' or 'Give me an overview'\n"
        response += "• **Agent Info**: 'Which agents are down?' or 'Show me inactive agents'\n"
        response += "• **Performance**: 'How is performance?' or 'Show me metrics'\n"
        response += "• **Issues**: 'Any problems?' or 'What errors occurred?'\n\n"
        
        response += "**🚀 Quick Commands**: Use the buttons in the sidebar for instant answers!\n\n"
        response += f"**Current Insight**: With {health}% health, "
        if health >= 80:
            response += "your system is performing well. Try asking about performance trends!"
        elif health >= 60:
            response += f"you have {total-active} inactive agents that might need attention."
        else:
            response += "your system needs immediate attention. Ask 'What issues do I have?'"
        
        return response
    
    def _generate_dynamic_status_response(self, summary: Dict, agents: List, metrics: List, events: List, query: str) -> str:
        """Generate dynamic status response with real-time insights"""
        health = summary.get('system_health', 0)
        active = summary.get('active_agents', 0)
        total = summary.get('total_agents', 0)
        
        # Dynamic status assessment
        if health >= 80:
            status_assessment = "🟢 **Excellent** - System is performing optimally"
        elif health >= 60:
            status_assessment = "🟡 **Good** - Minor issues detected"
        else:
            status_assessment = "🔴 **Attention Required** - System needs immediate attention"
        
        response = f"📊 **Live System Status Report**\n\n"
        response += f"{status_assessment}\n\n"
        
        # Real-time data
        response += f"**🤖 Agent Status**: {active} of {total} agents active ({health}% health)\n"
        response += f"**📈 Data Collection**: {summary.get('recent_metrics', 0)} metrics, {summary.get('recent_events', 0)} events (last hour)\n"
        response += f"**📊 Total Data**: {len(metrics)} metrics, {len(events)} events available\n\n"
        
        # Dynamic insights based on current state
        if active < total:
            inactive_count = total - active
            response += f"⚠️ **Action Needed**: {inactive_count} agents are inactive:\n"
            for agent in agents:
                if agent['state'] != 'active':
                    response += f"   • {agent['agent_id']} - {agent['state']}\n"
        else:
            response += "✅ **All Systems Operational**: All agents are running smoothly\n"
        
        # Recent activity analysis
        recent_activity_level = "High" if summary.get('recent_metrics', 0) > 1000 else "Medium" if summary.get('recent_metrics', 0) > 100 else "Low"
        response += f"\n📈 **Activity Level**: {recent_activity_level} ({summary.get('recent_metrics', 0)} metrics/hour)\n"
        
        # Dynamic recommendations
        if health < 70:
            response += "\n🔧 **Recommended Actions**: Check inactive agents and recent error events"
        elif recent_activity_level == "Low":
            response += "\n💡 **Insight**: Low activity detected - system may be in maintenance mode"
        else:
            response += "\n✨ **System Status**: Everything looks good! Keep monitoring for optimal performance"
        
        return response
    
    def _generate_contextual_response(self, query: str, summary: Dict, agents: List, metrics: List, events: List) -> str:
        """Generate contextual response based on specific questions"""
        query_lower = query.lower()
        
        # Extract key information based on query
        if 'how many' in query_lower:
            if 'agent' in query_lower:
                active = summary.get('active_agents', 0)
                total = summary.get('total_agents', 0)
                return f"🤖 **Agent Count**: You have **{active} active agents** out of **{total} total agents** ({summary.get('system_health', 0)}% health)"
            elif 'metric' in query_lower:
                return f"📊 **Metrics Count**: **{len(metrics)} total metrics** with **{summary.get('recent_metrics', 0)} collected in the last hour**"
            elif 'event' in query_lower:
                return f"📝 **Events Count**: **{len(events)} total events** with **{summary.get('recent_events', 0)} in the last hour**"
        
        elif 'what is' in query_lower:
            if 'health' in query_lower:
                health = summary.get('system_health', 0)
                status = "Excellent" if health >= 80 else "Good" if health >= 60 else "Needs Attention"
                return f"💚 **System Health**: **{health}%** - {status}. Based on {summary.get('active_agents', 0)}/{summary.get('total_agents', 0)} active agents."
            elif 'status' in query_lower:
                return self._generate_dynamic_status_response(summary, agents, metrics, events, query)
        
        elif 'why' in query_lower:
            if any(word in query_lower for word in ['down', 'offline', 'inactive']):
                inactive_agents = [a for a in agents if a['state'] != 'active']
                if inactive_agents:
                    response = f"🔍 **Why Agents Are Down**: {len(inactive_agents)} agents are inactive:\n\n"
                    for agent in inactive_agents:
                        response += f"• **{agent['agent_id']}**: Status '{agent['state']}'\n"
                    response += "\n**Possible Reasons**: Resource issues, configuration problems, or scheduled maintenance"
                    return response
                else:
                    return "✅ **No Agents Down**: All agents are currently active and operational!"
        
        elif 'show me' in query_lower:
            if 'recent' in query_lower:
                return self._generate_dynamic_events_response(events, summary, query)
            elif 'agent' in query_lower:
                return self._generate_dynamic_agents_response(summary, agents, query)
            elif 'metric' in query_lower or 'performance' in query_lower:
                return self._generate_dynamic_performance_response(metrics, summary, query)
        
        # Default contextual response
        return self._generate_intelligent_general_response(query, summary, agents)
    
    def _generate_intelligent_general_response(self, query: str, summary: Dict, agents: List) -> str:
        """Generate intelligent general response with real-time context"""
        health = summary.get('system_health', 0)
        active = summary.get('active_agents', 0)
        total = summary.get('total_agents', 0)
        
        response = f"🤖 **AI Analysis of Your Query**: *\"{query}\"*\n\n"
        
        # Provide current context
        response += f"**📊 Current System Context**:\n"
        response += f"• Health: {health}% ({'🟢 Good' if health >= 70 else '🟡 Fair' if health >= 50 else '🔴 Poor'})\n"
        response += f"• Agents: {active}/{total} active\n"
        response += f"• Activity: {summary.get('recent_metrics', 0)} metrics, {summary.get('recent_events', 0)} events (last hour)\n\n"
        
        # Intelligent suggestions based on query and system state
        response += "**💡 Relevant Information**:\n"
        
        if health < 70:
            response += f"• Your system health is at {health}% - consider checking inactive agents\n"
        
        if active < total:
            response += f"• {total - active} agents are inactive and may need attention\n"
        
        # Smart suggestions based on query content
        query_lower = query.lower()
        if any(word in query_lower for word in ['slow', 'performance', 'speed']):
            response += "• For performance issues, check recent metrics and agent response times\n"
        elif any(word in query_lower for word in ['error', 'problem', 'issue']):
            response += "• For troubleshooting, review recent error events and agent logs\n"
        elif any(word in query_lower for word in ['monitor', 'watch', 'track']):
            response += "• Use the sidebar metrics to monitor real-time system health\n"
        
        response += "\n**🎯 Try asking me**:\n"
        response += "• 'What specific issues do I have?'\n"
        response += "• 'Show me my worst performing agents'\n"
        response += "• 'What happened in the last hour?'\n"
        response += "• 'How can I improve system health?'"
        
        return response
    
    def _generate_dynamic_agents_response(self, summary: Dict, agents: List, query: str) -> str:
        """Generate dynamic agent response with real-time analysis"""
        active = summary.get('active_agents', 0)
        total = summary.get('total_agents', 0)
        
        response = f"🤖 **Live Agent Analysis** ({active}/{total} active)\n\n"
        
        # Agent state breakdown
        agent_states = {}
        agent_types = {}
        
        for agent in agents:
            state = agent['state']
            agent_type = agent['agent_type']
            agent_states[state] = agent_states.get(state, 0) + 1
            agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
        
        response += "**📊 Agent States:**\n"
        for state, count in agent_states.items():
            emoji = "🟢" if state == 'active' else "🔴" if state == 'inactive' else "🟡"
            response += f"   {emoji} {state.title()}: {count} agents\n"
        
        response += "\n**🔧 Agent Types:**\n"
        for agent_type, count in agent_types.items():
            response += f"   • {agent_type}: {count} instances\n"
        
        # Recent agents analysis
        response += "\n**⏰ Recent Agents** (by creation time):\n"
        sorted_agents = sorted(agents, key=lambda x: x.get('created_at', ''), reverse=True)
        for agent in sorted_agents[:5]:
            status_emoji = "🟢" if agent['state'] == 'active' else "🔴"
            response += f"   {status_emoji} {agent['agent_id']} ({agent['agent_type']})\n"
        
        # Dynamic insights
        if active == total:
            response += "\n✅ **Excellent**: All agents are operational!"
        elif active > total * 0.8:
            response += f"\n💚 **Good**: Most agents active, {total-active} need attention"
        else:
            response += f"\n⚠️ **Attention**: {total-active} agents offline - investigate issues"
        
        # Context-specific advice
        if 'down' in query.lower() or 'inactive' in query.lower():
            inactive_agents = [a for a in agents if a['state'] != 'active']
            if inactive_agents:
                response += f"\n🔍 **Inactive Agents Details**:\n"
                for agent in inactive_agents:
                    response += f"   • {agent['agent_id']}: {agent['state']} (Type: {agent['agent_type']})\n"
        
        return response
    
    def _generate_dynamic_performance_response(self, metrics: List, summary: Dict, query: str) -> str:
        """Generate dynamic performance response with real-time metrics analysis"""
        recent_count = summary.get('recent_metrics', 0)
        total_count = len(metrics)
        
        response = f"📊 **Live Performance Analysis**\n\n"
        response += f"**📈 Activity**: {recent_count} metrics collected in the last hour\n"
        response += f"**💾 Total Data**: {total_count} metrics available for analysis\n\n"
        
        if metrics:
            # Analyze metric types and values
            metric_analysis = {}
            recent_metrics = []
            
            for metric in metrics:
                metric_name = metric['metric_name']
                if metric_name not in metric_analysis:
                    metric_analysis[metric_name] = {
                        'count': 0,
                        'values': [],
                        'latest': None
                    }
                metric_analysis[metric_name]['count'] += 1
                if metric['metric_value'] is not None:
                    try:
                        metric_analysis[metric_name]['values'].append(float(metric['metric_value']))
                        metric_analysis[metric_name]['latest'] = metric['metric_value']
                    except (ValueError, TypeError):
                        pass  # Skip non-numeric values
                
                # Track recent metrics (assuming timestamp-based)
                if len(recent_metrics) < 5:
                    recent_metrics.append(metric)
            
            response += "**🔍 Top Metrics Being Tracked**:\n"
            sorted_metrics = sorted(metric_analysis.items(), key=lambda x: x[1]['count'], reverse=True)
            for metric_name, data in sorted_metrics[:5]:
                avg_value = sum(data['values']) / len(data['values']) if data['values'] else 0
                response += f"   • **{metric_name}**: {data['count']} measurements"
                if data['values']:
                    response += f" (avg: {avg_value:.2f})"
                response += "\n"
            
            # Performance insights
            response += "\n**💡 Performance Insights**:\n"
            if recent_count > 1000:
                response += "   🚀 High data collection rate - system very active\n"
            elif recent_count > 100:
                response += "   📈 Normal data collection rate - healthy activity\n"
            else:
                response += "   📉 Low data collection rate - check agent activity\n"
            
            # Latest activity
            if recent_metrics:
                response += "\n**⚡ Latest Metrics**:\n"
                for metric in recent_metrics[:3]:
                    response += f"   • {metric['metric_name']}: {metric['metric_value']} {metric.get('metric_unit', '')}\n"
        else:
            response += "⚠️ **No performance metrics available** - check data collection agents\n"
        
        # Context-specific analysis
        if 'cpu' in query.lower():
            cpu_metrics = [m for m in metrics if 'cpu' in m['metric_name'].lower()]
            if cpu_metrics:
                response += f"\n🖥️ **CPU-Related**: Found {len(cpu_metrics)} CPU measurements"
        elif 'memory' in query.lower():
            memory_metrics = [m for m in metrics if 'memory' in m['metric_name'].lower()]
            if memory_metrics:
                response += f"\n💾 **Memory-Related**: Found {len(memory_metrics)} memory measurements"
        
        return response
    
    def _generate_dynamic_issues_response(self, events: List, agents: List, summary: Dict, query: str) -> str:
        """Generate dynamic issues response with real-time problem analysis"""
        active = summary.get('active_agents', 0)
        total = summary.get('total_agents', 0)
        health = summary.get('system_health', 0)
        
        response = f"🔍 **Live Issue Analysis**\n\n"
        
        # Critical issues assessment
        critical_issues = []
        
        # Agent issues
        inactive_agents = [a for a in agents if a['state'] != 'active']
        if inactive_agents:
            critical_issues.append(f"{len(inactive_agents)} agents offline")
        
        # Event-based issues
        error_events = [e for e in events if e.get('severity') in ['ERROR', 'CRITICAL']]
        warning_events = [e for e in events if e.get('severity') == 'WARNING']
        
        if error_events:
            critical_issues.append(f"{len(error_events)} error events")
        
        # Overall assessment
        if not critical_issues and health >= 80:
            response += "✅ **No Critical Issues Detected!**\n\n"
            response += f"🎉 System health is excellent at {health}%\n"
            response += f"🤖 All {total} agents are operational\n"
            response += f"📊 {summary.get('recent_events', 0)} normal events in the last hour\n\n"
            response += "**💡 Preventive Monitoring**: Keep watching for:\n"
            response += "   • Performance trends\n   • Unusual event patterns\n   • Agent response times"
        else:
            response += f"⚠️ **Issues Found**: {', '.join(critical_issues)}\n\n"
            
            # Detailed problem breakdown
            if inactive_agents:
                response += "🔴 **Offline Agents**:\n"
                for agent in inactive_agents:
                    last_seen = agent.get('last_seen', 'Unknown')
                    response += f"   • {agent['agent_id']} - {agent['state']} (Last seen: {last_seen})\n"
                response += "\n"
            
            if error_events:
                response += "🚨 **Recent Errors**:\n"
                for event in error_events[:3]:
                    response += f"   • {event['event_type']} - {event.get('severity', 'ERROR')}\n"
                if len(error_events) > 3:
                    response += f"   ... and {len(error_events) - 3} more errors\n"
                response += "\n"
            
            if warning_events:
                response += f"🟡 **Warnings**: {len(warning_events)} warning events detected\n\n"
            
            # Action recommendations
            response += "🔧 **Recommended Actions**:\n"
            if inactive_agents:
                response += "   1. Restart offline agents\n"
                response += "   2. Check agent logs for error details\n"
            if error_events:
                response += "   3. Investigate recent error events\n"
                response += "   4. Review system resource usage\n"
            response += "   5. Monitor system for additional issues"
        
        return response
    
    def _generate_dynamic_events_response(self, events: List, summary: Dict, query: str) -> str:
        """Generate dynamic events response with real-time activity analysis"""
        recent_count = summary.get('recent_events', 0)
        total_count = len(events)
        
        response = f"📝 **Live Activity Analysis**\n\n"
        response += f"**⚡ Recent Activity**: {recent_count} events in the last hour\n"
        response += f"**📚 Total Events**: {total_count} events available\n\n"
        
        if events:
            # Event analysis
            event_types = {}
            severity_counts = {}
            latest_events = events[:5]
            
            for event in events:
                event_type = event['event_type']
                severity = event.get('severity', 'INFO')
                
                event_types[event_type] = event_types.get(event_type, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Event type breakdown
            response += "**📊 Event Types** (most frequent):\n"
            sorted_types = sorted(event_types.items(), key=lambda x: x[1], reverse=True)
            for event_type, count in sorted_types[:5]:
                response += f"   • {event_type}: {count} events\n"
            
            # Severity analysis
            response += "\n**🚨 Severity Breakdown**:\n"
            for severity in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
                if severity in severity_counts:
                    emoji = {"CRITICAL": "🔴", "ERROR": "🟠", "WARNING": "🟡", "INFO": "🔵", "DEBUG": "⚪"}.get(severity, "⚪")
                    response += f"   {emoji} {severity}: {severity_counts[severity]} events\n"
            
            # Latest activity
            response += "\n**⏰ Latest Events**:\n"
            for event in latest_events:
                severity = event.get('severity', 'INFO')
                emoji = {"CRITICAL": "🔴", "ERROR": "🟠", "WARNING": "🟡", "INFO": "🔵", "DEBUG": "⚪"}.get(severity, "🔵")
                timestamp = str(event['timestamp'])[:19] if event.get('timestamp') else 'Unknown'
                response += f"   {emoji} {event['event_type']} - {timestamp}\n"
            
            # Activity insights
            response += "\n**💡 Activity Insights**:\n"
            if recent_count > 100:
                response += "   🚀 High activity - system very busy\n"
            elif recent_count > 20:
                response += "   📈 Normal activity level\n"
            else:
                response += "   📉 Low activity - system quiet\n"
            
            # Error analysis
            error_count = severity_counts.get('ERROR', 0) + severity_counts.get('CRITICAL', 0)
            if error_count > 0:
                response += f"   ⚠️ {error_count} errors need attention\n"
            else:
                response += "   ✅ No errors detected in recent events\n"
        else:
            response += "⚠️ **No events available** - check event logging configuration\n"
        
        return response

@st.cache_resource
def get_ai_help_agent():
    """Get cached AI Help Agent instance with persistent conversation memory"""
    return StreamlitAIHelpAgent()

def init_session_state():
    """Initialize session state for conversation continuity"""
    if 'conversation_initialized' not in st.session_state:
        st.session_state.conversation_initialized = True

def main():
    """Main Streamlit application"""
    
    # Initialize session state
    init_session_state()
    
    # Title and header
    st.title("🤖 AI Help Agent")
    st.markdown("*Your intelligent assistant for background agents system monitoring*")
    
    # Initialize AI Help Agent
    try:
        ai_agent = get_ai_help_agent()
        
        # Check LLM availability
        if ai_agent.llm_generator.llm_available:
            st.success("✅ AI Help Agent connected to system database with LLM intelligence")
            st.info("🧠 **Enhanced Mode**: Full AI analysis with GPT-4 powered insights")
        else:
            st.success("✅ AI Help Agent connected to system database")
            st.warning("⚠️ **Basic Mode**: Set OPENAI_API_KEY in environment for full LLM analysis")
            
    except Exception as e:
        st.error(f"❌ Failed to initialize AI Help Agent: {e}")
        return
    
    # Sidebar with system info
    with st.sidebar:
        st.header("🖥️ System Info")
        
        try:
            summary = ai_agent.db_client.get_system_summary()
            if summary:
                st.metric("System Health", f"{summary.get('system_health', 0)}%")
                st.metric("Active Agents", f"{summary.get('active_agents', 0)}/{summary.get('total_agents', 0)}")
                st.metric("Recent Metrics", summary.get('recent_metrics', 0))
                st.metric("Recent Events", summary.get('recent_events', 0))
            else:
                st.warning("Unable to fetch system summary")
        except Exception as e:
            st.error(f"Error loading system info: {e}")
        
        # Enhanced RAG System Status
        st.markdown("---")
        st.header("🧠 Enhanced RAG System")
        try:
            rag_status = ai_agent.get_enhanced_rag_status()
            
            if rag_status['enhanced_rag_available']:
                st.success("✅ Enhanced RAG Active")
                st.metric("System Status", rag_status['rag_status']['system_status'].title())
                st.metric("Documents Indexed", rag_status['rag_status']['documents_indexed'])
                
                if rag_status['rag_status']['semantic_accuracy'] > 0:
                    st.metric("Semantic Accuracy", f"{rag_status['rag_status']['semantic_accuracy']:.1f}%")
                
                # RAG capabilities indicator
                st.markdown("**🎯 Enhanced Capabilities:**")
                st.markdown("• Vector-based semantic search")
                st.markdown("• Document chunking & indexing")
                st.markdown("• Context-aware retrieval")
                st.markdown("• Conversation learning")
                
            else:
                st.warning("⚠️ Basic RAG Mode")
                st.info("Enhanced vector search not available")
                st.markdown("**📝 Current Capabilities:**")
                st.markdown("• Keyword-based search")
                st.markdown("• Basic code analysis")
                st.markdown("• System data integration")
                
                if rag_status['rag_status'].get('error'):
                    st.error(f"Error: {rag_status['rag_status']['error']}")
                    
        except Exception as e:
            st.warning(f"RAG status error: {e}")
        
        # Codebase Info
        st.markdown("---")
        st.header("📁 Codebase Info")
        try:
            # Get codebase analysis (lightweight check)
            if ai_agent._codebase_analysis is None:
                with st.spinner("Analyzing codebase..."):
                    ai_agent._get_codebase_analysis()
            
            codebase = ai_agent._codebase_analysis
            if codebase and not codebase.get('error'):
                st.metric("Total Files", codebase.get('total_files', 0))
                st.metric("Lines of Code", codebase.get('total_lines', 0))
                
                # Show primary language
                languages = codebase.get('languages', {})
                if languages:
                    primary_lang = max(languages.items(), key=lambda x: x[1]['lines'])
                    st.metric("Primary Language", primary_lang[0])
                    
                # Enhanced RAG integration status
                try:
                    rag_status = ai_agent.get_enhanced_rag_status()
                    if rag_status['enhanced_rag_available']:
                        st.success("🔗 Vector indexing available")
                    else:
                        st.info("📄 Static analysis only")
                except Exception:
                    st.info("📄 Static analysis only")
                
                # Add refresh button for codebase analysis
                if st.button("🔄 Refresh Codebase", help="Force refresh codebase analysis to include new files"):
                    ai_agent.force_refresh_codebase_analysis()
                    st.success("Codebase analysis refreshed!")
                    st.rerun()
            else:
                st.warning("Codebase analysis unavailable")
        except Exception as e:
            st.warning(f"Codebase analysis error: {e}")
        
        st.markdown("---")
        st.markdown("**Quick Commands:**")
        
        # System commands
        st.markdown("*System Status:*")
        system_commands = [
            "What's the system status?",
            "How many agents are running?", 
            "Are there any issues?",
            "Show me recent activity"
        ]
        
        for cmd in system_commands:
            if st.button(cmd, key=f"quick_{hash(cmd)}"):
                st.session_state['user_question'] = cmd
        
        # Code commands
        st.markdown("*Code Analysis:*")
        code_commands = [
            "Show me the codebase structure",
            "What agents are implemented?",
            "Where is the health monitoring code?",
            "Point me to the main agent files"
        ]
        
        for cmd in code_commands:
            if st.button(cmd, key=f"code_{hash(cmd)}"):
                st.session_state['user_question'] = cmd
        
        # Conversation Memory Section
        st.markdown("---")
        st.header("💭 Conversation Memory")
        try:
            conv_summary = ai_agent.conversation_memory.get_conversation_summary()
            if conv_summary['total_exchanges'] > 0:
                st.metric("Total Exchanges", conv_summary['total_exchanges'])
                
                # Show recent questions
                if conv_summary['recent_questions']:
                    st.markdown("**Recent Questions:**")
                    for q in conv_summary['recent_questions']:
                        st.markdown(f"• {q[:50]}..." if len(q) > 50 else f"• {q}")
                
                # Conversation management buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 Export Chat", key="export_conv"):
                        st.session_state['show_export'] = True
                with col2:
                    if st.button("🗑️ Clear Memory", key="clear_conv"):
                        ai_agent.conversation_memory.clear_memory()
                        st.success("Conversation memory cleared!")
                        st.rerun()
            else:
                st.info("No conversation history yet")
        except Exception as e:
            st.warning(f"Memory error: {e}")
    
    # Main chat interface
    st.header("💬 Ask Me Anything")
    
    # Question input
    user_question = st.text_input(
        "What would you like to know about your system?",
        placeholder="e.g., What's the current system status?",
        key="question_input",
        value=st.session_state.get('user_question', '')
    )
    
    # Clear the session state after using it
    if 'user_question' in st.session_state:
        del st.session_state['user_question']
    
    # Show export dialog if requested
    if st.session_state.get('show_export', False):
        with st.expander("📋 Conversation Export", expanded=True):
            exported_text = ai_agent.conversation_memory.export_conversation()
            st.text_area("Conversation History", exported_text, height=300)
            if st.button("Close Export"):
                st.session_state['show_export'] = False
                st.rerun()
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        ask_button = st.button("🤖 Ask", type="primary")
    
    with col2:
        clear_button = st.button("🧹 Clear")
    
    if clear_button:
        st.session_state.clear()
        st.rerun()
    
    # Process question
    if ask_button and user_question:
        with st.spinner("🔍 Analyzing your system..."):
            try:
                # Process the help request
                result = ai_agent.process_help_request(user_question)
                
                if result['success']:
                    # Display response
                    st.markdown("### 🤖 AI Assistant Response")
                    st.markdown(result['response'])
                    
                    # Display metadata
                    with st.expander("📊 Response Details"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Processing Time", f"{result['processing_time']:.2f}s")
                        with col2:
                            st.metric("System Health", f"{result.get('system_health', 0)}%")
                        with col3:
                            st.metric("Data Sources", 
                                    f"{result['data_sources']['agents_count']} agents, "
                                    f"{result['data_sources']['metrics_count']} metrics")
                        
                        # Show conversation context info
                        conv_summary = result.get('conversation_summary', {})
                        if conv_summary.get('total_exchanges', 0) > 1:
                            st.markdown("**🧠 Learning Context:**")
                            st.markdown(f"• Building on {conv_summary['total_exchanges']} previous exchanges")
                            topics = conv_summary.get('topics_discussed', [])
                            if topics:
                                st.markdown(f"• Learned topics: {', '.join(topics[:3])}")
                        
                        st.json(result['data_sources'])
                
                else:
                    st.error(f"❌ Error: {result['error']}")
                    st.markdown(result['response'])
                
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
    
    elif ask_button and not user_question:
        st.warning("⚠️ Please enter a question first!")
    
    # Display conversation history
    conv_history = ai_agent.conversation_memory.conversation_history
    if len(conv_history) > 1:  # Show history only if there's more than current exchange
        st.markdown("---")
        st.markdown("### 💭 Conversation History")
        
        # Show conversation in reverse order (most recent first, excluding current)
        for i, exchange in enumerate(reversed(conv_history[:-1])):  # Exclude the most recent (current) exchange
            with st.expander(f"🔄 Exchange {len(conv_history) - i - 1}: {exchange['question'][:60]}...", expanded=False):
                timestamp = datetime.fromisoformat(exchange['timestamp']).strftime('%H:%M:%S')
                st.markdown(f"**⏰ Time:** {timestamp}")
                st.markdown(f"**❓ Question:** {exchange['question']}")
                st.markdown(f"**🤖 Response:** {exchange['response']}")
                
                # Show metadata if available
                metadata = exchange.get('metadata', {})
                if metadata:
                    st.markdown("**📊 Context:**")
                    if metadata.get('system_health'):
                        st.markdown(f"• System Health: {metadata['system_health']}%")
                    if metadata.get('codebase_analyzed'):
                        st.markdown(f"• Codebase: {metadata.get('total_files', 0)} files analyzed")
    
    # Footer
    st.markdown("---")
    st.markdown("*AI Help Agent - Powered by your background agents system data with conversation memory*")

if __name__ == "__main__":
    main() 