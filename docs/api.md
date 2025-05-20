# API Documentation

## BusinessCaseAgent

The core agent class for business case analysis.

### Initialization

```python
agent = BusinessCaseAgent()
```

Initializes the agent with all necessary components:
- AI Assistant for LLM interactions
- Vector DB connections
- Task memory system
- Metrics tracker
- Priority evaluator

### Methods

#### load_document

```python
def load_document(self, filepath: str) -> str:
    """
    Load and validate a document from the given filepath.
    
    Args:
        filepath (str): Path to the document file
        
    Returns:
        str: Document content
        
    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file does not exist
    """
```

#### enrich_with_vectorstore

```python
def enrich_with_vectorstore(self, query: str) -> str:
    """
    Enrich context using vector store search.
    
    Args:
        query (str): Search query
        
    Returns:
        str: Combined search results from main and local stores
    """
```

#### enrich_with_web

```python
def enrich_with_web(self, query: str) -> str:
    """
    Enrich context using web search.
    
    Args:
        query (str): Search query
        
    Returns:
        str: Web search results
        
    Note:
        Implements rate limiting and caching
    """
```

#### analyze

```python
def analyze(self, content: str) -> dict:
    """
    Analyze document content through multiple steps.
    
    Args:
        content (str): Document content to analyze
        
    Returns:
        dict: Analysis results for each step:
            - summarize_document
            - identify_parties
            - describe_situation
            - describe_problem
            - recommend_solution
    """
```

#### build_case

```python
def build_case(self, filepath: str) -> dict:
    """
    Execute the full business case analysis pipeline.
    
    Args:
        filepath (str): Path to the business case document
        
    Returns:
        dict: Complete analysis results including:
            - document_content
            - vector_context
            - web_context
            - analysis
            - checklist_items
            - metrics
    """
```

#### track_performance_metrics

```python
def track_performance_metrics(self, operation: str, metrics: dict) -> None:
    """
    Track performance metrics for an operation.
    
    Args:
        operation (str): Operation name
        metrics (dict): Metrics to track:
            - duration
            - content_length
            - memory_usage
            - cpu_usage
            - accuracy_score
            - error_count
    """
```

#### evaluate_analysis_quality

```python
def evaluate_analysis_quality(self, analysis_results: dict) -> dict:
    """
    Evaluate the quality of analysis results.
    
    Args:
        analysis_results (dict): Results to evaluate
        
    Returns:
        dict: Quality metrics:
            - completeness
            - consistency
            - relevance
            - actionability
    """
```

#### get_performance_report

```python
def get_performance_report(self) -> dict:
    """
    Generate a comprehensive performance report.
    
    Returns:
        dict: Performance statistics:
            - analysis_performance
            - resource_usage
            - quality_metrics
            - error_statistics
    """
```

## AIAssistant

Manages AI model interactions and prompt processing.

### Methods

#### analyze

```python
def analyze(self, content: str, step: str) -> dict:
    """
    Analyze content using AI model.
    
    Args:
        content (str): Content to analyze
        step (str): Analysis step name
        
    Returns:
        dict: Analysis results with metrics
    """
```

## LocalKnowledgeBase

Handles vector store operations and document storage.

### Methods

#### search_main_store

```python
def search_main_store(self, query: str) -> List[dict]:
    """
    Search the main vector store.
    
    Args:
        query (str): Search query
        
    Returns:
        List[dict]: Search results with scores
    """
```

#### search_local_store

```python
def search_local_store(self, query: str) -> List[dict]:
    """
    Search the local vector store.
    
    Args:
        query (str): Search query
        
    Returns:
        List[dict]: Search results with scores
    """
```

## MetricsTracker

Tracks performance and quality metrics.

### Methods

#### track_metric

```python
def track_metric(self, name: str, value: float) -> None:
    """
    Track a metric value.
    
    Args:
        name (str): Metric name
        value (float): Metric value
    """
```

#### get_metrics

```python
def get_metrics(self) -> dict:
    """
    Get all tracked metrics.
    
    Returns:
        dict: Metric values by name
    """
```

## PriorityEvaluator

Evaluates task priorities and dependencies.

### Methods

#### evaluate_priority

```python
def evaluate_priority(self, task: dict) -> str:
    """
    Evaluate task priority.
    
    Args:
        task (dict): Task to evaluate
        
    Returns:
        str: Priority level (high/medium/low)
    """
```

#### analyze_dependencies

```python
def analyze_dependencies(self, tasks: List[dict]) -> List[dict]:
    """
    Analyze task dependencies.
    
    Args:
        tasks (List[dict]): Tasks to analyze
        
    Returns:
        List[dict]: Tasks with dependency information
    """
``` 