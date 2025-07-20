"""
Advanced Query System for AI Help Agent
Implements intelligent search capabilities with context-aware query expansion,
multi-modal search, semantic similarity ranking, and cross-reference linking.
"""

import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class QueryContext:
    """Context information for query processing"""
    user_id: str
    conversation_history: List[Dict]
    system_state: Dict
    query_category: str
    query_intent: str
    technical_level: str  # beginner, intermediate, expert
    focus_areas: List[str]  # code, architecture, debugging, etc.

@dataclass
class SearchResult:
    """Enhanced search result with metadata"""
    content: str
    source: str
    file_path: Optional[str]
    relevance_score: float
    content_type: str  # code, documentation, conversation, config
    metadata: Dict
    cross_references: List[str]
    confidence: float

class IntelligentQueryProcessor:
    """
    Advanced query processing with context-aware expansion and intent recognition
    """
    
    def __init__(self):
        self.query_patterns = {
            'code_search': [
                r'function\s+\w+', r'class\s+\w+', r'def\s+\w+',
                r'where\s+is\s+\w+', r'find\s+\w+', r'search\s+for\s+\w+'
            ],
            'architecture': [
                r'architecture', r'structure', r'design', r'pattern',
                r'how\s+does\s+it\s+work', r'flow', r'data\s+flow'
            ],
            'debugging': [
                r'error', r'bug', r'issue', r'problem', r'fix',
                r'why\s+is\s+it\s+failing', r'troubleshoot', r'debug'
            ],
            'performance': [
                r'slow', r'performance', r'optimization', r'efficiency',
                r'how\s+to\s+improve', r'better', r'faster'
            ]
        }
        
        self.technical_terms = {
            'database': ['postgresql', 'sql', 'db', 'connection', 'query', 'schema'],
            'api': ['endpoint', 'route', 'http', 'rest', 'graphql', 'service'],
            'frontend': ['ui', 'interface', 'component', 'react', 'vue', 'angular'],
            'backend': ['server', 'api', 'service', 'controller', 'model'],
            'deployment': ['docker', 'kubernetes', 'aws', 'cloud', 'ci/cd'],
            'monitoring': ['metrics', 'logging', 'health', 'alert', 'dashboard'],
            'security': ['auth', 'authentication', 'authorization', 'encryption', 'ssl']
        }
        
        self.query_expansion_cache = {}
        
    def analyze_query_intent(self, query: str, context: QueryContext) -> Dict[str, Any]:
        """Analyze query intent and extract key information"""
        
        query_lower = query.lower()
        intent_analysis = {
            'primary_intent': 'general',
            'confidence': 0.5,
            'technical_terms': [],
            'code_elements': [],
            'context_boosters': [],
            'suggested_expansions': []
        }
        
        # Detect primary intent
        for intent, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    intent_analysis['primary_intent'] = intent
                    intent_analysis['confidence'] = 0.8
                    break
        
        # Extract technical terms
        for category, terms in self.technical_terms.items():
            for term in terms:
                if term in query_lower:
                    intent_analysis['technical_terms'].append({
                        'term': term,
                        'category': category
                    })
        
        # Extract code elements (functions, classes, variables)
        code_patterns = [
            r'\b\w+\(\)',  # function calls
            r'\b[A-Z][a-zA-Z]*\b',  # potential class names
            r'\b\w+\.\w+\b',  # method calls
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, query)
            intent_analysis['code_elements'].extend(matches)
        
        # Context boosters from conversation history
        if context.conversation_history:
            recent_topics = self._extract_recent_topics(context.conversation_history)
            intent_analysis['context_boosters'] = recent_topics
        
        return intent_analysis
    
    def expand_query(self, query: str, context: QueryContext) -> List[str]:
        """Expand query with related terms and context"""
        
        cache_key = f"{query}_{context.user_id}_{hash(str(context.system_state))}"
        if cache_key in self.query_expansion_cache:
            return self.query_expansion_cache[cache_key]
        
        expanded_queries = [query]
        
        # Intent-based expansion
        intent_analysis = self.analyze_query_intent(query, context)
        
        # Add technical term expansions
        for term_info in intent_analysis['technical_terms']:
            category = term_info['category']
            if category in self.technical_terms:
                related_terms = self.technical_terms[category]
                for related_term in related_terms[:3]:  # Top 3 related terms
                    expanded_query = query.replace(term_info['term'], related_term)
                    if expanded_query != query:
                        expanded_queries.append(expanded_query)
        
        # Add code element expansions
        for code_element in intent_analysis['code_elements']:
            # Add variations (e.g., "get_user" -> "get_user_by_id", "get_user_profile")
            variations = self._generate_code_variations(code_element)
            for variation in variations:
                expanded_query = query.replace(code_element, variation)
                if expanded_query != query:
                    expanded_queries.append(expanded_query)
        
        # Add context-based expansions
        if context.conversation_history:
            recent_context = self._extract_query_context(context.conversation_history)
            for context_term in recent_context[:2]:  # Top 2 context terms
                if context_term not in query.lower():
                    expanded_query = f"{query} {context_term}"
                    expanded_queries.append(expanded_query)
        
        # Remove duplicates and limit results
        unique_queries = list(set(expanded_queries))[:5]  # Max 5 expanded queries
        
        self.query_expansion_cache[cache_key] = unique_queries
        return unique_queries
    
    def _extract_recent_topics(self, conversation_history: List[Dict]) -> List[str]:
        """Extract recent topics from conversation history"""
        topics = []
        recent_messages = conversation_history[-5:]  # Last 5 messages
        
        for message in recent_messages:
            content = message.get('content', '').lower()
            
            # Extract technical terms from recent conversations
            for category, terms in self.technical_terms.items():
                for term in terms:
                    if term in content and term not in topics:
                        topics.append(term)
        
        return topics[:5]  # Top 5 recent topics
    
    def _extract_query_context(self, conversation_history: List[Dict]) -> List[str]:
        """Extract context terms for query expansion"""
        context_terms = []
        
        # Analyze recent queries for context
        for message in conversation_history[-3:]:  # Last 3 messages
            if message.get('type') == 'user_query':
                query = message.get('content', '').lower()
                
                # Extract nouns and technical terms
                words = re.findall(r'\b\w+\b', query)
                for word in words:
                    if len(word) > 3 and word not in context_terms:
                        context_terms.append(word)
        
        return context_terms
    
    def _generate_code_variations(self, code_element: str) -> List[str]:
        """Generate variations of code elements for expansion"""
        variations = []
        
        # Remove parentheses for function calls
        if code_element.endswith('()'):
            base_name = code_element[:-2]
            variations.extend([
                f"{base_name}_by_id",
                f"{base_name}_by_name", 
                f"{base_name}_profile",
                f"get_{base_name}",
                f"create_{base_name}",
                f"update_{base_name}"
            ])
        
        # Add common prefixes/suffixes for class names
        elif code_element[0].isupper():
            variations.extend([
                f"{code_element}Manager",
                f"{code_element}Service",
                f"{code_element}Controller",
                f"{code_element}Model",
                f"{code_element}Repository"
            ])
        
        return variations[:3]  # Limit to 3 variations

class MultiModalSearchEngine:
    """
    Multi-modal search engine that searches across code, documentation, 
    conversations, and configuration files with intelligent ranking
    """
    
    def __init__(self, enhanced_rag_system):
        self.rag_system = enhanced_rag_system
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.search_history = defaultdict(list)

    def _detect_cross_reference_query(self, query: str) -> Optional[Dict]:
        """Detect if the query is a cross-reference query and extract the type and target."""
        import re
        # Where is foo used?
        m = re.match(r'where is ([\w\.]+) used', query.lower())
        if m:
            return {'type': 'calls', 'target': m.group(1)}
        # Subclasses of Y
        m = re.match(r'(show me )?all subclasses of ([\w\.]+)', query.lower())
        if m:
            return {'type': 'inherits', 'target': m.group(2)}
        # What modules does this file import?
        m = re.match(r'what modules does (.+) import', query.lower())
        if m:
            return {'type': 'imports', 'target': m.group(1)}
        return None

    def _filter_by_cross_reference(self, results: List[SearchResult], ref_type: str, target: str) -> List[SearchResult]:
        """Filter or boost results based on cross-reference metadata (case-insensitive)."""
        filtered = []
        target_lc = target.lower()
        for result in results:
            meta_val = result.metadata.get(ref_type, '')
            if meta_val:
                # Split comma-separated list and strip whitespace
                items = [x.strip() for x in meta_val.split(',') if x.strip()]
                # Compare lowercased
                if any(target_lc == item.lower() for item in items):
                    filtered.append(result)
        return filtered if filtered else results  # fallback to all if none found

    async def search(self, query: str, context: QueryContext, 
                    top_k: int = 10) -> List[SearchResult]:
        """Perform multi-modal search with intelligent ranking"""
        start_time = time.time()
        query_processor = IntelligentQueryProcessor()
        expanded_queries = query_processor.expand_query(query, context)
        all_results = []
        for expanded_query in expanded_queries:
            vector_results = await self._vector_search(expanded_query, context, top_k)
            all_results.extend(vector_results)
            if self._is_code_query(expanded_query):
                keyword_results = await self._keyword_search(expanded_query, context, top_k)
                all_results.extend(keyword_results)
        # Cross-reference filtering
        cross_ref = self._detect_cross_reference_query(query)
        if cross_ref:
            all_results = self._filter_by_cross_reference(all_results, cross_ref['type'], cross_ref['target'])
        unique_results = self._deduplicate_results(all_results)
        ranked_results = await self._rank_results(unique_results, query, context)
        enhanced_results = await self._add_cross_references(ranked_results)
        search_time = time.time() - start_time
        self._log_search_performance(query, len(enhanced_results), search_time)
        return enhanced_results[:top_k]
    
    async def _vector_search(self, query: str, context: QueryContext, 
                           top_k: int) -> List[SearchResult]:
        """Perform vector-based semantic search"""
        try:
            # Use Enhanced RAG system for vector search
            documents = await self.rag_system.retrieve_relevant_content(
                query, context.system_state, top_k
            )
            
            results = []
            for doc in documents:
                result = SearchResult(
                    content=doc.content,
                    source=doc.source,
                    file_path=doc.metadata.get('file_path'),
                    relevance_score=doc.relevance_score,
                    content_type=self._classify_content_type(doc),
                    metadata=doc.metadata,
                    cross_references=[],
                    confidence=doc.relevance_score
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logging.error(f"Vector search failed: {e}")
            return []
    
    async def _keyword_search(self, query: str, context: QueryContext, 
                            top_k: int) -> List[SearchResult]:
        """Perform keyword-based search for code-specific queries"""
        # This would integrate with codebase analyzer for keyword search
        # For now, return empty list as vector search handles most cases
        return []
    
    def _is_code_query(self, query: str) -> bool:
        """Determine if query is code-specific"""
        code_indicators = [
            'function', 'class', 'method', 'def', 'import',
            'file', 'code', 'implementation', 'source'
        ]
        return any(indicator in query.lower() for indicator in code_indicators)
    
    def _classify_content_type(self, document) -> str:
        """Classify document content type"""
        metadata = document.metadata
        source = document.source
        
        if source == 'codebase':
            file_path = metadata.get('file_path', '')
            if file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp')):
                return 'code'
            elif file_path.endswith(('.md', '.txt', '.rst')):
                return 'documentation'
            elif file_path.endswith(('.yml', '.yaml', '.json', '.toml')):
                return 'config'
        elif source == 'conversation':
            return 'conversation'
        elif source == 'documentation':
            return 'documentation'
        
        return 'general'
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content similarity"""
        unique_results = []
        seen_content = set()
        
        for result in results:
            # Create a content hash for deduplication
            content_hash = hash(result.content[:100])  # First 100 chars
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    async def _rank_results(self, results: List[SearchResult], 
                          original_query: str, context: QueryContext) -> List[SearchResult]:
        """Intelligently rank search results"""
        
        for result in results:
            # Base score from vector similarity
            base_score = result.relevance_score
            
            # Content type boost
            type_boost = self._get_content_type_boost(result.content_type, context)
            
            # Recency boost for conversations
            recency_boost = self._get_recency_boost(result)
            
            # Context relevance boost
            context_boost = self._get_context_boost(result, context)
            
            # Technical level boost
            technical_boost = self._get_technical_level_boost(result, context)
            
            # Calculate final score
            final_score = base_score * type_boost * recency_boost * context_boost * technical_boost
            result.relevance_score = min(final_score, 1.0)  # Cap at 1.0
        
        # Sort by final relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results
    
    def _get_content_type_boost(self, content_type: str, context: QueryContext) -> float:
        """Get boost based on content type and user focus"""
        base_boosts = {
            'code': 1.2,
            'documentation': 1.0,
            'conversation': 0.9,
            'config': 0.8,
            'general': 1.0
        }
        
        boost = base_boosts.get(content_type, 1.0)
        
        # Adjust based on user focus areas
        if content_type == 'code' and 'code' in context.focus_areas:
            boost *= 1.1
        elif content_type == 'documentation' and 'architecture' in context.focus_areas:
            boost *= 1.1
        
        return boost
    
    def _get_recency_boost(self, result: SearchResult) -> float:
        """Get boost based on content recency"""
        if result.content_type == 'conversation':
            timestamp = result.metadata.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    
                    hours_old = (datetime.now() - timestamp).total_seconds() / 3600
                    if hours_old < 24:  # Recent conversations
                        return 1.2
                    elif hours_old < 168:  # Within a week
                        return 1.1
                except:
                    pass
        
        return 1.0
    
    def _get_context_boost(self, result: SearchResult, context: QueryContext) -> float:
        """Get boost based on context relevance"""
        boost = 1.0
        
        # Check if result content matches recent conversation topics
        if context.conversation_history:
            recent_topics = self._extract_recent_topics(context.conversation_history)
            content_lower = result.content.lower()
            
            for topic in recent_topics:
                if topic in content_lower:
                    boost *= 1.05  # Small boost for context relevance
        
        return boost
    
    def _get_technical_level_boost(self, result: SearchResult, context: QueryContext) -> float:
        """Get boost based on technical level match"""
        if context.technical_level == 'beginner':
            # Boost simpler, more explanatory content
            if 'documentation' in result.content_type or 'conversation' in result.content_type:
                return 1.1
        elif context.technical_level == 'expert':
            # Boost technical, code-heavy content
            if 'code' in result.content_type:
                return 1.1
        
        return 1.0
    
    async def _add_cross_references(self, results: List[SearchResult]) -> List[SearchResult]:
        """Add cross-references between related results"""
        
        for i, result in enumerate(results):
            cross_refs = []
            
            # Find related results based on content similarity
            for j, other_result in enumerate(results):
                if i != j:
                    similarity = self._calculate_content_similarity(result, other_result)
                    if similarity > 0.3:  # Threshold for cross-reference
                        cross_refs.append({
                            'content': other_result.content[:100] + "...",
                            'source': other_result.source,
                            'similarity': similarity
                        })
            
            # Sort cross-references by similarity
            cross_refs.sort(key=lambda x: x['similarity'], reverse=True)
            result.cross_references = [ref['content'] for ref in cross_refs[:3]]  # Top 3
        
        return results
    
    def _calculate_content_similarity(self, result1: SearchResult, result2: SearchResult) -> float:
        """Calculate similarity between two results"""
        try:
            # Simple TF-IDF similarity
            texts = [result1.content, result2.content]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.0
    
    def _extract_recent_topics(self, conversation_history: List[Dict]) -> List[str]:
        """Extract recent topics from conversation history"""
        topics = []
        recent_messages = conversation_history[-5:]  # Last 5 messages
        
        for message in recent_messages:
            content = message.get('content', '').lower()
            
            # Extract technical terms
            technical_terms = [
                'database', 'api', 'frontend', 'backend', 'deployment',
                'monitoring', 'security', 'performance', 'error', 'bug'
            ]
            
            for term in technical_terms:
                if term in content and term not in topics:
                    topics.append(term)
        
        return topics[:5]
    
    def _log_search_performance(self, query: str, result_count: int, search_time: float):
        """Log search performance metrics"""
        self.search_history[query].append({
            'timestamp': datetime.now(),
            'result_count': result_count,
            'search_time': search_time
        })
        
        # Keep only recent history
        if len(self.search_history[query]) > 10:
            self.search_history[query] = self.search_history[query][-10:]

class CodeAnalysisEngine:
    """
    Advanced code analysis engine for function/class extraction and dependency mapping
    """
    
    def __init__(self):
        self.code_patterns = {
            'python': {
                'function': r'def\s+(\w+)\s*\(',
                'class': r'class\s+(\w+)',
                'import': r'(?:from|import)\s+(\w+)',
                'method': r'def\s+(\w+)\s*\(self',
            },
            'javascript': {
                'function': r'(?:function\s+)?(\w+)\s*\([^)]*\)\s*{',
                'class': r'class\s+(\w+)',
                'import': r'(?:import|from)\s+[\'"]([^\'"]+)[\'"]',
                'method': r'(\w+)\s*\([^)]*\)\s*{',
            }
        }
        
    def extract_code_elements(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extract functions, classes, and dependencies from code"""
        
        file_extension = file_path.split('.')[-1].lower()
        language_patterns = self.code_patterns.get(file_extension, {})
        
        elements = {
            'functions': [],
            'classes': [],
            'imports': [],
            'dependencies': [],
            'file_path': file_path,
            'language': file_extension
        }
        
        if not language_patterns:
            return elements
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract functions
            if 'function' in language_patterns:
                func_matches = re.findall(language_patterns['function'], line)
                for func_name in func_matches:
                    elements['functions'].append({
                        'name': func_name,
                        'line': line_num,
                        'type': 'function'
                    })
            
            # Extract classes
            if 'class' in language_patterns:
                class_matches = re.findall(language_patterns['class'], line)
                for class_name in class_matches:
                    elements['classes'].append({
                        'name': class_name,
                        'line': line_num,
                        'type': 'class'
                    })
            
            # Extract imports
            if 'import' in language_patterns:
                import_matches = re.findall(language_patterns['import'], line)
                for import_name in import_matches:
                    elements['imports'].append({
                        'name': import_name,
                        'line': line_num,
                        'type': 'import'
                    })
        
        # Extract dependencies from imports
        elements['dependencies'] = self._extract_dependencies(elements['imports'])
        
        return elements
    
    def _extract_dependencies(self, imports: List[Dict]) -> List[str]:
        """Extract dependency names from imports"""
        dependencies = []
        
        for imp in imports:
            import_name = imp['name']
            
            # Handle different import formats
            if '.' in import_name:
                # Handle "from package import module" or "package.module"
                base_package = import_name.split('.')[0]
                dependencies.append(base_package)
            else:
                dependencies.append(import_name)
        
        return list(set(dependencies))  # Remove duplicates
    
    def generate_dependency_map(self, codebase_elements: List[Dict]) -> Dict[str, Any]:
        """Generate dependency mapping for codebase"""
        
        dependency_map = {
            'files': {},
            'dependencies': {},
            'relationships': []
        }
        
        # Build file-level dependency map
        for element in codebase_elements:
            file_path = element['file_path']
            dependency_map['files'][file_path] = {
                'dependencies': element['dependencies'],
                'functions': len(element['functions']),
                'classes': len(element['classes']),
                'imports': len(element['imports'])
            }
        
        # Build global dependency map
        all_dependencies = set()
        for element in codebase_elements:
            all_dependencies.update(element['dependencies'])
        
        for dep in all_dependencies:
            dependency_map['dependencies'][dep] = {
                'used_by': [],
                'usage_count': 0
            }
        
        # Find relationships
        for element in codebase_elements:
            file_path = element['file_path']
            for dep in element['dependencies']:
                if dep in dependency_map['dependencies']:
                    dependency_map['dependencies'][dep]['used_by'].append(file_path)
                    dependency_map['dependencies'][dep]['usage_count'] += 1
        
        # Generate relationship graph
        for element in codebase_elements:
            file_path = element['file_path']
            for dep in element['dependencies']:
                dependency_map['relationships'].append({
                    'from': file_path,
                    'to': dep,
                    'type': 'imports'
                })
        
        return dependency_map
    
    def suggest_code_improvements(self, codebase_elements: List[Dict]) -> List[Dict]:
        """Suggest code improvements based on analysis"""
        
        suggestions = []
        
        # Analyze function complexity
        for element in codebase_elements:
            if len(element['functions']) > 20:
                suggestions.append({
                    'type': 'complexity',
                    'file': element['file_path'],
                    'issue': 'High function count',
                    'suggestion': 'Consider breaking into smaller modules',
                    'severity': 'medium'
                })
        
        # Analyze dependency usage
        dependency_usage = defaultdict(int)
        for element in codebase_elements:
            for dep in element['dependencies']:
                dependency_usage[dep] += 1
        
        # Find unused or overused dependencies
        for dep, count in dependency_usage.items():
            if count == 1:
                suggestions.append({
                    'type': 'dependency',
                    'dependency': dep,
                    'issue': 'Single usage dependency',
                    'suggestion': 'Consider if this dependency is necessary',
                    'severity': 'low'
                })
            elif count > 10:
                suggestions.append({
                    'type': 'dependency',
                    'dependency': dep,
                    'issue': 'Heavily used dependency',
                    'suggestion': 'Consider creating a wrapper or abstraction',
                    'severity': 'medium'
                })
        
        return suggestions

class AdvancedQuerySystem:
    """
    Main interface for advanced query capabilities
    """
    
    def __init__(self, enhanced_rag_system):
        self.query_processor = IntelligentQueryProcessor()
        self.search_engine = MultiModalSearchEngine(enhanced_rag_system)
        self.code_analyzer = CodeAnalysisEngine()
        
    async def process_advanced_query(self, query: str, user_id: str, 
                                   conversation_history: List[Dict],
                                   system_state: Dict) -> Dict[str, Any]:
        """Process query with advanced capabilities"""
        # Create query context
        context = QueryContext(
            user_id=user_id,
            conversation_history=conversation_history,
            system_state=system_state,
            query_category=self._categorize_query(query),
            query_intent='general',
            technical_level=self._assess_technical_level(conversation_history),
            focus_areas=self._extract_focus_areas(conversation_history)
        )
        # Analyze query intent
        intent_analysis = self.query_processor.analyze_query_intent(query, context)
        context.query_intent = intent_analysis['primary_intent']
        # Perform multi-modal search
        search_results = await self.search_engine.search(query, context, top_k=20)
        # Check for cross-reference query and format response
        cross_ref = self.search_engine._detect_cross_reference_query(query)
        if cross_ref and search_results:
            # Format a list of matching code elements
            ref_type = cross_ref['type']
            target = cross_ref['target']
            matches = []
            for result in search_results:
                # For subclasses, show class name and file path
                if ref_type == 'inherits':
                    classes_field = result.metadata.get('classes', '').strip()
                    if classes_field:
                        if ',' in classes_field:
                            class_names = [c.strip() for c in classes_field.split(',') if c.strip() and c.strip() not in ['{', '}'] and len(c.strip()) > 1]
                        else:
                            class_names = [classes_field] if classes_field not in ['{', '}'] and len(classes_field) > 1 else []
                        for class_name in class_names:
                            matches.append(f"- {class_name} ({result.file_path})")
                # For calls, show function/method and file path
                elif ref_type == 'calls':
                    functions_field = result.metadata.get('functions', '').strip()
                    if functions_field:
                        if ',' in functions_field:
                            func_names = [f.strip() for f in functions_field.split(',') if f.strip() and f.strip() not in ['{', '}'] and len(f.strip()) > 1]
                        else:
                            func_names = [functions_field] if functions_field not in ['{', '}'] and len(functions_field) > 1 else []
                        for func_name in func_names:
                            matches.append(f"- {func_name} ({result.file_path})")
                # For imports, show file path and imported modules
                elif ref_type == 'imports':
                    imports = result.metadata.get('imports', '')
                    if imports:
                        matches.append(f"- {result.file_path}: {imports}")
            if matches:
                response_text = f"**{ref_type.capitalize()} of `{target}` found in your codebase:**\n" + '\n'.join(matches)
            else:
                response_text = f"No {ref_type} of `{target}` found in your codebase."
        else:
            # Fallback: previous behavior
            response_text = None
            if search_results:
                response_text = '\n'.join([
                    result.content[:200] + "..." if len(result.content) > 200 else result.content
                    for result in search_results[:3]
                ])
            if not response_text:
                response_text = "I could not find relevant information in the current knowledge base."
        response = {
            'query': query,
            'intent_analysis': intent_analysis,
            'search_results': [
                {
                    'content': result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    'source': result.source,
                    'file_path': result.file_path,
                    'relevance_score': result.relevance_score,
                    'content_type': result.content_type,
                    'cross_references': result.cross_references
                }
                for result in search_results
            ],
            'total_results': len(search_results),
            'query_expansions': self.query_processor.expand_query(query, context),
            'context': {
                'technical_level': context.technical_level,
                'focus_areas': context.focus_areas,
                'query_category': context.query_category
            },
            'response_text': response_text
        }
        return response
    
    def _categorize_query(self, query: str) -> str:
        """Categorize query type"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['function', 'class', 'method', 'code']):
            return 'code_search'
        elif any(word in query_lower for word in ['error', 'bug', 'issue', 'problem']):
            return 'debugging'
        elif any(word in query_lower for word in ['performance', 'slow', 'optimize']):
            return 'performance'
        elif any(word in query_lower for word in ['architecture', 'design', 'structure']):
            return 'architecture'
        else:
            return 'general'
    
    def _assess_technical_level(self, conversation_history: List[Dict]) -> str:
        """Assess user's technical level based on conversation history"""
        if not conversation_history:
            return 'intermediate'
        
        technical_terms = 0
        total_messages = len(conversation_history)
        
        for message in conversation_history:
            content = message.get('content', '').lower()
            if any(term in content for term in ['function', 'class', 'api', 'database', 'architecture']):
                technical_terms += 1
        
        technical_ratio = technical_terms / total_messages if total_messages > 0 else 0
        
        if technical_ratio > 0.7:
            return 'expert'
        elif technical_ratio > 0.3:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _extract_focus_areas(self, conversation_history: List[Dict]) -> List[str]:
        """Extract user's focus areas from conversation history"""
        focus_areas = []
        
        if not conversation_history:
            return ['general']
        
        # Analyze recent conversations for focus areas
        recent_content = ' '.join([
            msg.get('content', '') for msg in conversation_history[-5:]
        ]).lower()
        
        area_keywords = {
            'code': ['function', 'class', 'method', 'implementation', 'code'],
            'architecture': ['design', 'structure', 'pattern', 'architecture'],
            'debugging': ['error', 'bug', 'issue', 'problem', 'fix'],
            'performance': ['slow', 'performance', 'optimize', 'efficiency'],
            'deployment': ['deploy', 'docker', 'kubernetes', 'aws', 'cloud']
        }
        
        for area, keywords in area_keywords.items():
            if any(keyword in recent_content for keyword in keywords):
                focus_areas.append(area)
        
        return focus_areas if focus_areas else ['general'] 