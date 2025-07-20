# Real-Time Orchestrator Component

## 🎯 **Overview**

The Real-Time Orchestrator is the central coordination component of the Cloud-Dedicated Real-Time Repository Processing System. It manages the entire repository processing pipeline, provides real-time progress updates, and ensures fault-tolerant, scalable processing across distributed resources.

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Real-Time Orchestrator                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Stage       │  │ Progress    │  │ Event       │         │
│  │ Manager     │  │ Tracker     │  │ Publisher   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Task        │  │ Error       │  │ Resource    │         │
│  │ Scheduler   │  │ Handler     │  │ Manager     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│  Initialization → Metadata → Structure → Code → RAG → Ready │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **Core Components**

### **1. Stage Manager**

The Stage Manager coordinates the processing stages and ensures proper transitions between them.

```python
class StageManager:
    """Manages processing stages and transitions"""
    
    def __init__(self):
        self.stages = [
            ProcessingStage("initialization", "Repository Initialization"),
            ProcessingStage("metadata", "Metadata Extraction"),
            ProcessingStage("structure", "File Structure Analysis"),
            ProcessingStage("code_analysis", "Code Analysis & RAG Indexing"),
            ProcessingStage("ready", "AI Assistant Ready")
        ]
        self.current_stage = 0
        self.stage_results = {}
    
    async def start_stage(self, stage_index: int, repository_id: str):
        """Start a processing stage"""
        if stage_index >= len(self.stages):
            raise ValueError(f"Invalid stage index: {stage_index}")
        
        stage = self.stages[stage_index]
        stage.start_time = datetime.now()
        stage.status = "running"
        
        await self.publish_stage_event(repository_id, "started", stage)
        
        return stage
    
    async def complete_stage(self, stage_index: int, repository_id: str, result: Dict):
        """Complete a processing stage"""
        stage = self.stages[stage_index]
        stage.end_time = datetime.now()
        stage.duration = stage.end_time - stage.start_time
        stage.status = "completed"
        stage.result = result
        
        self.stage_results[stage_index] = result
        
        await self.publish_stage_event(repository_id, "completed", stage)
        
        return stage
    
    async def fail_stage(self, stage_index: int, repository_id: str, error: Exception):
        """Mark a stage as failed"""
        stage = self.stages[stage_index]
        stage.end_time = datetime.now()
        stage.duration = stage.end_time - stage.start_time
        stage.status = "failed"
        stage.error = str(error)
        
        await self.publish_stage_event(repository_id, "failed", stage)
        
        return stage
```

### **2. Progress Tracker**

The Progress Tracker monitors and reports real-time progress within each stage.

```python
class ProgressTracker:
    """Tracks and reports processing progress"""
    
    def __init__(self):
        self.progress_callbacks = []
        self.current_progress = 0.0
        self.stage_progress = {}
    
    async def update_progress(self, stage_index: int, progress: float, 
                            message: str = None, details: Dict = None):
        """Update progress for a specific stage"""
        self.stage_progress[stage_index] = {
            'progress': progress,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate overall progress
        total_progress = sum(p['progress'] for p in self.stage_progress.values())
        overall_progress = total_progress / len(self.stage_progress)
        
        await self.broadcast_progress_update(stage_index, overall_progress, message, details)
    
    async def broadcast_progress_update(self, stage_index: int, overall_progress: float,
                                      message: str, details: Dict):
        """Broadcast progress update to all registered callbacks"""
        update = {
            'type': 'progress_update',
            'stage_index': stage_index,
            'stage_progress': self.stage_progress[stage_index],
            'overall_progress': overall_progress,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        for callback in self.progress_callbacks:
            try:
                await callback(update)
            except Exception as e:
                logging.error(f"Progress callback error: {e}")
    
    def register_callback(self, callback: Callable):
        """Register a progress update callback"""
        self.progress_callbacks.append(callback)
```

### **3. Event Publisher**

The Event Publisher manages real-time event distribution to connected clients.

```python
class EventPublisher:
    """Publishes real-time events to connected clients"""
    
    def __init__(self):
        self.websocket_connections = {}
        self.event_queue = asyncio.Queue()
        self.publisher_task = None
    
    async def start(self):
        """Start the event publisher"""
        self.publisher_task = asyncio.create_task(self._publish_events())
    
    async def stop(self):
        """Stop the event publisher"""
        if self.publisher_task:
            self.publisher_task.cancel()
            try:
                await self.publisher_task
            except asyncio.CancelledError:
                pass
    
    async def publish_event(self, repository_id: str, event_type: str, data: Dict):
        """Publish an event for a specific repository"""
        event = {
            'repository_id': repository_id,
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.event_queue.put(event)
    
    async def _publish_events(self):
        """Background task to publish events"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._broadcast_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Event publishing error: {e}")
    
    async def _broadcast_event(self, event: Dict):
        """Broadcast event to all connected clients"""
        if event['repository_id'] in self.websocket_connections:
            connections = self.websocket_connections[event['repository_id']]
            dead_connections = []
            
            for connection in connections:
                try:
                    await connection.send_json(event)
                except Exception as e:
                    logging.error(f"Failed to send event: {e}")
                    dead_connections.append(connection)
            
            # Remove dead connections
            for dead_connection in dead_connections:
                connections.remove(dead_connection)
```

### **4. Task Scheduler**

The Task Scheduler manages the distribution of processing tasks across available workers.

```python
class TaskScheduler:
    """Schedules and distributes processing tasks"""
    
    def __init__(self):
        self.worker_pool = []
        self.task_queue = asyncio.Queue()
        self.scheduler_task = None
    
    async def start(self):
        """Start the task scheduler"""
        self.scheduler_task = asyncio.create_task(self._schedule_tasks())
    
    async def stop(self):
        """Stop the task scheduler"""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
    
    async def schedule_task(self, task: ProcessingTask):
        """Schedule a processing task"""
        await self.task_queue.put(task)
    
    async def _schedule_tasks(self):
        """Background task to schedule and distribute tasks"""
        while True:
            try:
                task = await self.task_queue.get()
                worker = await self._get_available_worker()
                
                if worker:
                    await worker.process_task(task)
                else:
                    # No available workers, wait and retry
                    await asyncio.sleep(1)
                    await self.task_queue.put(task)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Task scheduling error: {e}")
    
    async def _get_available_worker(self) -> Optional[Worker]:
        """Get an available worker from the pool"""
        for worker in self.worker_pool:
            if worker.is_available():
                return worker
        return None
```

## 🔄 **Processing Pipeline**

### **Stage 1: Repository Initialization**

```python
class RepositoryInitializer:
    """Handles repository initialization stage"""
    
    async def process(self, repository_id: str, repo_url: str) -> Dict:
        """Process repository initialization"""
        try:
            # Validate repository URL
            if not self._is_valid_repo_url(repo_url):
                raise ValueError(f"Invalid repository URL: {repo_url}")
            
            # Check repository access
            await self._check_repository_access(repo_url)
            
            # Clone repository
            repo_path = await self._clone_repository(repo_url)
            
            # Extract basic information
            basic_info = await self._extract_basic_info(repo_path, repo_url)
            
            return {
                'status': 'success',
                'repository_path': repo_path,
                'basic_info': basic_info
            }
            
        except Exception as e:
            logging.error(f"Repository initialization failed: {e}")
            raise
    
    async def _clone_repository(self, repo_url: str) -> str:
        """Clone repository to temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix=f"repo_analysis_{uuid.uuid4().hex[:8]}_")
        
        try:
            # Clone with progress callback
            await self._git_clone_with_progress(repo_url, temp_dir)
            return temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    async def _git_clone_with_progress(self, repo_url: str, target_path: str):
        """Clone repository with progress reporting"""
        process = await asyncio.create_subprocess_exec(
            'git', 'clone', repo_url, target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Git clone failed: {stderr.decode()}")
```

### **Stage 2: Metadata Extraction**

```python
class MetadataExtractor:
    """Handles metadata extraction stage"""
    
    async def process(self, repository_id: str, repo_path: str) -> Dict:
        """Extract repository metadata"""
        try:
            metadata = {
                'readme': await self._extract_readme(repo_path),
                'dependencies': await self._extract_dependencies(repo_path),
                'config_files': await self._extract_config_files(repo_path),
                'license': await self._extract_license(repo_path),
                'git_info': await self._extract_git_info(repo_path)
            }
            
            return {
                'status': 'success',
                'metadata': metadata
            }
            
        except Exception as e:
            logging.error(f"Metadata extraction failed: {e}")
            raise
    
    async def _extract_readme(self, repo_path: str) -> Optional[Dict]:
        """Extract and parse README files"""
        readme_files = [
            'README.md', 'README.txt', 'README.rst',
            'readme.md', 'readme.txt', 'readme.rst'
        ]
        
        for readme_file in readme_files:
            readme_path = os.path.join(repo_path, readme_file)
            if os.path.exists(readme_path):
                content = await self._read_file_content(readme_path)
                return {
                    'filename': readme_file,
                    'content': content,
                    'sections': self._parse_readme_sections(content),
                    'size': len(content)
                }
        
        return None
```

### **Stage 3: File Structure Analysis**

```python
class FileStructureAnalyzer:
    """Handles file structure analysis stage"""
    
    async def process(self, repository_id: str, repo_path: str) -> Dict:
        """Analyze repository file structure"""
        try:
            structure = {
                'directories': await self._scan_directories(repo_path),
                'files': await self._scan_files(repo_path),
                'file_types': await self._analyze_file_types(repo_path),
                'key_directories': await self._identify_key_directories(repo_path)
            }
            
            return {
                'status': 'success',
                'structure': structure
            }
            
        except Exception as e:
            logging.error(f"File structure analysis failed: {e}")
            raise
    
    async def _scan_directories(self, repo_path: str) -> List[Dict]:
        """Scan and analyze directory structure"""
        directories = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in root:
                continue
            
            rel_path = os.path.relpath(root, repo_path)
            
            if rel_path != '.':
                directories.append({
                    'path': rel_path,
                    'file_count': len(files),
                    'subdirectories': len(dirs),
                    'size': self._calculate_directory_size(root)
                })
        
        return directories
```

### **Stage 4: Code Analysis**

```python
class CodeAnalyzer:
    """Handles code analysis stage"""
    
    async def process(self, repository_id: str, repo_path: str) -> Dict:
        """Analyze code files"""
        try:
            code_files = await self._get_code_files(repo_path)
            
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
            
            for file_path in code_files:
                file_analysis = await self._analyze_code_file(file_path)
                analysis['files'][file_path] = file_analysis
                
                # Aggregate statistics
                analysis['statistics']['total_functions'] += len(file_analysis['functions'])
                analysis['statistics']['total_classes'] += len(file_analysis['classes'])
                analysis['statistics']['total_lines'] += file_analysis['line_count']
            
            return {
                'status': 'success',
                'analysis': analysis
            }
            
        except Exception as e:
            logging.error(f"Code analysis failed: {e}")
            raise
```

### **Stage 5: RAG Index Building**

```python
class RAGIndexBuilder:
    """Handles RAG index building stage"""
    
    async def process(self, repository_id: str, metadata: Dict, 
                     structure: Dict, code_analysis: Dict) -> Dict:
        """Build RAG index from repository data"""
        try:
            documents = []
            
            # Add README content
            if metadata.get('readme'):
                documents.extend(self._create_readme_documents(metadata['readme']))
            
            # Add code documentation
            documents.extend(self._create_code_documents(code_analysis))
            
            # Add file structure information
            documents.extend(self._create_structure_documents(structure))
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(documents)
            
            # Build vector index
            vector_index = await self._build_vector_index(documents, embeddings)
            
            return {
                'status': 'success',
                'index_info': {
                    'total_documents': len(documents),
                    'total_embeddings': len(embeddings),
                    'index_size': len(vector_index)
                }
            }
            
        except Exception as e:
            logging.error(f"RAG index building failed: {e}")
            raise
```

## 🔧 **Configuration**

### **Orchestrator Configuration**

```yaml
orchestrator:
  # Stage configuration
  stages:
    initialization:
      timeout: 300  # 5 minutes
      retries: 3
      max_concurrent: 10
    
    metadata:
      timeout: 180  # 3 minutes
      retries: 2
      max_concurrent: 20
    
    structure:
      timeout: 240  # 4 minutes
      retries: 2
      max_concurrent: 15
    
    code_analysis:
      timeout: 600  # 10 minutes
      retries: 3
      max_concurrent: 5
    
    rag_indexing:
      timeout: 300  # 5 minutes
      retries: 2
      max_concurrent: 3
  
  # Progress tracking
  progress:
    update_interval: 1.0  # seconds
    batch_size: 10
    max_callbacks: 100
  
  # Event publishing
  events:
    queue_size: 1000
    batch_size: 50
    publish_interval: 0.1  # seconds
  
  # Error handling
  error_handling:
    max_retries: 3
    retry_delay: 5  # seconds
    exponential_backoff: true
```

### **Worker Configuration**

```yaml
workers:
  # Worker pool configuration
  pool:
    min_workers: 3
    max_workers: 20
    scale_up_threshold: 0.8
    scale_down_threshold: 0.2
  
  # Task configuration
  tasks:
    timeout: 1800  # 30 minutes
    max_memory: "4Gi"
    max_cpu: "2000m"
  
  # Health checks
  health:
    check_interval: 30  # seconds
    timeout: 10  # seconds
    failure_threshold: 3
```

## 📊 **Monitoring & Metrics**

### **Key Metrics**

```python
class OrchestratorMetrics:
    """Metrics collection for the orchestrator"""
    
    def __init__(self):
        self.metrics = {
            'processing_duration': Histogram('processing_duration_seconds'),
            'stage_duration': Histogram('stage_duration_seconds'),
            'success_rate': Counter('processing_success_total'),
            'error_rate': Counter('processing_error_total'),
            'active_repositories': Gauge('active_repositories'),
            'queue_size': Gauge('task_queue_size'),
            'worker_count': Gauge('active_workers')
        }
    
    def record_processing_duration(self, duration: float):
        """Record total processing duration"""
        self.metrics['processing_duration'].observe(duration)
    
    def record_stage_duration(self, stage: str, duration: float):
        """Record stage processing duration"""
        self.metrics['stage_duration'].observe(duration, {'stage': stage})
    
    def record_success(self, repository_id: str):
        """Record successful processing"""
        self.metrics['success_rate'].inc({'repository_id': repository_id})
    
    def record_error(self, repository_id: str, error_type: str):
        """Record processing error"""
        self.metrics['error_rate'].inc({
            'repository_id': repository_id,
            'error_type': error_type
        })
```

### **Health Checks**

```python
class OrchestratorHealthCheck:
    """Health check for the orchestrator"""
    
    async def check_health(self) -> Dict:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Check stage manager
        health_status['checks']['stage_manager'] = await self._check_stage_manager()
        
        # Check progress tracker
        health_status['checks']['progress_tracker'] = await self._check_progress_tracker()
        
        # Check event publisher
        health_status['checks']['event_publisher'] = await self._check_event_publisher()
        
        # Check task scheduler
        health_status['checks']['task_scheduler'] = await self._check_task_scheduler()
        
        # Overall status
        all_healthy = all(check['status'] == 'healthy' 
                         for check in health_status['checks'].values())
        
        health_status['status'] = 'healthy' if all_healthy else 'unhealthy'
        
        return health_status
```

## 🚀 **Deployment**

### **Kubernetes Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: real-time-orchestrator
  namespace: system-reference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: real-time-orchestrator
  template:
    metadata:
      labels:
        app: real-time-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: system-reference/orchestrator:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

### **Service Configuration**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: real-time-orchestrator-service
  namespace: system-reference
spec:
  selector:
    app: real-time-orchestrator
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: ClusterIP
```

This comprehensive documentation provides a complete guide to implementing and deploying the Real-Time Orchestrator component, ensuring reliable, scalable, and maintainable repository processing capabilities. 