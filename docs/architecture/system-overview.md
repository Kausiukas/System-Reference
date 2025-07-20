# System Architecture Overview

## 🏗️ **High-Level Architecture**

The Cloud-Dedicated Real-Time Repository Processing System is designed as a microservices-based, event-driven architecture that provides scalable, fault-tolerant repository analysis and AI-powered assistance.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Cloud Infrastructure Layer                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Kubernetes Cluster │ Load Balancers │ Auto-scaling │ Cloud Storage        │
│  (EKS/GKE/AKS)     │ (ALB/CLB/SLB)  │ Groups       │ (S3/GCS/Azure Blob)  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Application Gateway Layer                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  API Gateway │ Rate Limiting │ Authentication │ SSL Termination            │
│  (Kong/Envoy)│ (Redis)       │ (OAuth/JWT)    │ (Cert Manager)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Application Layer                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Web UI │ Real-time │ Repository │ AI Engine │ RAG Index │ Monitoring      │
│  (Streamlit) │ Orchestrator │ Processor │ (LLM/RAG) │ Manager │ (Prometheus) │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Layer                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Primary DB │ Vector DB │ Cache │ Message │ File │ Log │ Metrics           │
│  (PostgreSQL)│ (ChromaDB)│ (Redis)│ Queue │ Storage│ (ELK)│ (Prometheus)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 **Data Flow Architecture**

### **Repository Processing Flow**

```
1. User Input
   ┌─────────────┐
   │ Repository  │
   │ URL/Upload  │
   └─────────────┘
           │
           ▼
2. Validation & Initialization
   ┌─────────────┐
   │ URL Validator│
   │ Access Check │
   │ Clone Repo  │
   └─────────────┘
           │
           ▼
3. Metadata Extraction
   ┌─────────────┐
   │ README Parser│
   │ Config Files │
   │ Dependencies │
   └─────────────┘
           │
           ▼
4. File Structure Analysis
   ┌─────────────┐
   │ Directory   │
   │ Scanner     │
   │ File Types  │
   └─────────────┘
           │
           ▼
5. Code Analysis
   ┌─────────────┐
   │ AST Parser  │
   │ Function    │
   │ Extractor   │
   └─────────────┘
           │
           ▼
6. RAG Index Building
   ┌─────────────┐
   │ Embeddings  │
   │ Generator   │
   │ Vector Index│
   └─────────────┘
           │
           ▼
7. AI Assistant Ready
   ┌─────────────┐
   │ Query       │
   │ Processor   │
   │ Response    │
   └─────────────┘
```

## 🏢 **Service Architecture**

### **Core Services**

#### **1. Web UI Service (Streamlit)**
```yaml
Service: web-ui
Port: 8501
Replicas: 2-10 (auto-scaling)
Resources:
  CPU: 500m-2000m
  Memory: 1Gi-4Gi
Dependencies:
  - api-gateway
  - websocket-service
```

#### **2. Real-Time Orchestrator**
```yaml
Service: real-time-orchestrator
Port: 8001
Replicas: 1-5 (auto-scaling)
Resources:
  CPU: 1000m-4000m
  Memory: 2Gi-8Gi
Dependencies:
  - message-queue
  - progress-tracker
  - event-bus
```

#### **3. Repository Processor**
```yaml
Service: repository-processor
Port: 8002
Replicas: 3-20 (auto-scaling)
Resources:
  CPU: 2000m-8000m
  Memory: 4Gi-16Gi
Dependencies:
  - git-service
  - file-analyzer
  - code-parser
```

#### **4. AI Engine**
```yaml
Service: ai-engine
Port: 8003
Replicas: 2-10 (auto-scaling)
Resources:
  CPU: 1000m-4000m
  Memory: 2Gi-8Gi
Dependencies:
  - llm-service
  - rag-index
  - embedding-service
```

#### **5. RAG Index Manager**
```yaml
Service: rag-index-manager
Port: 8004
Replicas: 1-3 (auto-scaling)
Resources:
  CPU: 1000m-4000m
  Memory: 2Gi-8Gi
Dependencies:
  - vector-database
  - embedding-service
  - document-store
```

### **Supporting Services**

#### **6. Message Queue (Redis)**
```yaml
Service: message-queue
Port: 6379
Replicas: 3 (cluster)
Resources:
  CPU: 500m-2000m
  Memory: 1Gi-4Gi
Persistence: Yes
```

#### **7. Primary Database (PostgreSQL)**
```yaml
Service: primary-database
Port: 5432
Replicas: 1 primary + 2 read replicas
Resources:
  CPU: 2000m-8000m
  Memory: 4Gi-16Gi
Persistence: Yes
Backup: Automated
```

#### **8. Vector Database (ChromaDB)**
```yaml
Service: vector-database
Port: 8000
Replicas: 1-3 (auto-scaling)
Resources:
  CPU: 1000m-4000m
  Memory: 2Gi-8Gi
Persistence: Yes
```

## 🔄 **Event-Driven Architecture**

### **Event Types**

#### **Repository Events**
```json
{
  "event_type": "repository.processing.started",
  "repository_id": "uuid",
  "user_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "url": "https://github.com/user/repo",
    "size": 1024000,
    "file_count": 150
  }
}
```

#### **Processing Events**
```json
{
  "event_type": "processing.stage.completed",
  "repository_id": "uuid",
  "stage": "metadata_extraction",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "duration": 5.2,
    "files_processed": 10,
    "metadata_extracted": {
      "readme_found": true,
      "dependencies_found": 15,
      "config_files": 3
    }
  }
}
```

#### **AI Events**
```json
{
  "event_type": "ai.query.processed",
  "repository_id": "uuid",
  "user_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "query": "What does this project do?",
    "response_time": 1.2,
    "rag_hits": 5,
    "confidence": 0.85
  }
}
```

### **Event Flow**

```
User Action → Event Publisher → Message Queue → Event Consumer → Service Action
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
Repository    Orchestrator    Redis Stream    Processor    Database
Upload        Publishes       Stores Event    Consumes     Update
```

## 🔐 **Security Architecture**

### **Authentication & Authorization**

#### **OAuth 2.0 Flow**
```
1. User clicks "Login with GitHub"
2. Redirect to GitHub OAuth
3. GitHub redirects with authorization code
4. Backend exchanges code for access token
5. Backend creates JWT session token
6. Frontend stores JWT for API calls
```

#### **JWT Token Structure**
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid",
    "iss": "system-reference",
    "aud": "api",
    "exp": 1640995200,
    "iat": 1640908800,
    "scope": ["read:repositories", "write:analysis"],
    "github_id": "12345"
  }
}
```

### **Data Encryption**

#### **At Rest**
- **Database**: AES-256 encryption
- **File Storage**: Server-side encryption
- **Backups**: Encrypted backups with rotation

#### **In Transit**
- **TLS 1.3**: All communications
- **Certificate Management**: Automatic renewal
- **HSTS**: HTTP Strict Transport Security

## 📊 **Monitoring & Observability**

### **Metrics Collection**

#### **Application Metrics**
```yaml
Metrics:
  - repository_processing_duration
  - repository_processing_success_rate
  - ai_query_response_time
  - ai_query_success_rate
  - rag_index_build_time
  - rag_search_hit_rate
```

#### **Infrastructure Metrics**
```yaml
Metrics:
  - cpu_usage_percentage
  - memory_usage_percentage
  - disk_usage_percentage
  - network_throughput
  - container_restart_count
  - pod_availability
```

### **Logging Strategy**

#### **Structured Logging**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "service": "repository-processor",
  "correlation_id": "uuid",
  "user_id": "uuid",
  "repository_id": "uuid",
  "message": "Processing repository started",
  "metadata": {
    "url": "https://github.com/user/repo",
    "stage": "initialization"
  }
}
```

#### **Log Aggregation**
- **Fluentd**: Log collection and forwarding
- **Elasticsearch**: Log storage and indexing
- **Kibana**: Log visualization and search
- **Log Retention**: 30 days for application logs, 90 days for audit logs

### **Alerting**

#### **Critical Alerts**
```yaml
Alerts:
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    duration: "5m"
    severity: "critical"
  
  - name: "High Response Time"
    condition: "p95_response_time > 2s"
    duration: "5m"
    severity: "warning"
  
  - name: "Service Down"
    condition: "service_health == 0"
    duration: "1m"
    severity: "critical"
```

## 🔄 **Scalability Patterns**

### **Horizontal Scaling**

#### **Auto-scaling Rules**
```yaml
AutoScaling:
  - metric: "cpu_utilization"
    threshold: 70%
    scale_up: "add 1 replica"
    scale_down: "remove 1 replica"
    cooldown: "300s"
  
  - metric: "memory_utilization"
    threshold: 80%
    scale_up: "add 1 replica"
    scale_down: "remove 1 replica"
    cooldown: "300s"
  
  - metric: "queue_length"
    threshold: 100
    scale_up: "add 2 replicas"
    scale_down: "remove 1 replica"
    cooldown: "60s"
```

### **Database Scaling**

#### **Read Replicas**
```yaml
Database:
  Primary:
    - instance: "db-primary"
      size: "db.r5.2xlarge"
      storage: "1000Gi"
  
  ReadReplicas:
    - instance: "db-replica-1"
      size: "db.r5.xlarge"
      storage: "500Gi"
    - instance: "db-replica-2"
      size: "db.r5.xlarge"
      storage: "500Gi"
```

### **Caching Strategy**

#### **Multi-Level Caching**
```yaml
Caching:
  L1: "Application Memory Cache"
    - size: "1GB per pod"
    - ttl: "5 minutes"
    - eviction: "LRU"
  
  L2: "Redis Cluster"
    - size: "10GB total"
    - ttl: "1 hour"
    - eviction: "LRU"
  
  L3: "CDN Cache"
    - size: "unlimited"
    - ttl: "24 hours"
    - eviction: "TTL"
```

## 🚀 **Deployment Architecture**

### **Kubernetes Deployment**

#### **Namespace Structure**
```yaml
Namespaces:
  - system-reference:
      - web-ui
      - api-gateway
      - real-time-orchestrator
  
  - system-reference-processing:
      - repository-processor
      - ai-engine
      - rag-index-manager
  
  - system-reference-data:
      - primary-database
      - vector-database
      - message-queue
  
  - system-reference-monitoring:
      - prometheus
      - grafana
      - elasticsearch
      - kibana
```

#### **Resource Quotas**
```yaml
ResourceQuotas:
  system-reference:
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
  
  system-reference-processing:
    requests.cpu: "8"
    requests.memory: "16Gi"
    limits.cpu: "16"
    limits.memory: "32Gi"
```

### **CI/CD Pipeline**

#### **Deployment Stages**
```yaml
Stages:
  1. Build:
     - docker build
     - security scan
     - unit tests
  
  2. Test:
     - integration tests
     - performance tests
     - security tests
  
  3. Staging:
     - deploy to staging
     - smoke tests
     - user acceptance tests
  
  4. Production:
     - blue-green deployment
     - health checks
     - monitoring verification
```

## 🔧 **Configuration Management**

### **Environment-Specific Configs**

#### **Development**
```yaml
Environment: development
Database:
  host: "localhost"
  port: 5432
  name: "system_reference_dev"
  ssl: false

AI:
  model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 1000

Processing:
  max_concurrent: 5
  timeout: 300
```

#### **Production**
```yaml
Environment: production
Database:
  host: "db-primary.system-reference-data.svc.cluster.local"
  port: 5432
  name: "system_reference_prod"
  ssl: true

AI:
  model: "gpt-4"
  temperature: 0.3
  max_tokens: 2000

Processing:
  max_concurrent: 50
  timeout: 600
```

This architecture provides a robust, scalable, and maintainable foundation for the Cloud-Dedicated Real-Time Repository Processing System, ensuring high availability, performance, and security in production environments. 