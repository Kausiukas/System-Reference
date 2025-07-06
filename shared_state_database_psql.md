# Shared State Database (PostgreSQL) Architecture

## Overview

This document provides a comprehensive overview of the PostgreSQL-based shared state database system used by the background agents monitoring platform. The system has migrated from SQLite to PostgreSQL to provide better concurrency, performance, and scalability for multi-agent environments.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Agent Connection Patterns](#agent-connection-patterns)
4. [Connection Procedures](#connection-procedures)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Migration Guide](#migration-guide)
7. [Performance Monitoring](#performance-monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

The PostgreSQL-based shared state system provides a centralized database for agent coordination, performance monitoring, and state management. The architecture consists of:

### Core Components

- **PostgreSQL Database**: Primary data storage with connection pooling
- **PostgreSQL Adapter**: Abstraction layer for database operations
- **SharedState Class**: High-level interface for agent interactions
- **Agent Coordinator**: Central orchestration system
- **Background Agents**: Individual monitoring and processing agents

### Key Features

- **Connection Pooling**: Efficient resource management with asyncpg
- **Async Operations**: Non-blocking database operations
- **Retry Logic**: Automatic retry with exponential backoff
- **Schema Management**: Automated table creation and indexing
- **Health Monitoring**: Database health checks and metrics
- **Transaction Support**: ACID compliance for data integrity

---

## Database Schema

### Connection Configuration

The system uses the following connection priority:

1. **Environment Variable**: `POSTGRES_CONNECTION_STRING`
2. **Config File**: `postgres_config.json`
3. **Default**: `postgresql://postgres:postgres@localhost:5432/background_agents`

### Core Tables

#### 1. agents
Primary table for agent registration and state management.

```sql
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'initializing',
    last_heartbeat TIMESTAMPTZ,
    last_state_change TIMESTAMPTZ,
    uptime_details JSONB,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes**:
- `idx_agents_agent_id` on `agent_id`
- `idx_agents_status` on `status`
- `idx_agents_last_heartbeat` on `last_heartbeat`

#### 2. performance_metrics
Stores performance data from all agents.

```sql
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    metric_name VARCHAR(255) NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    source_agent VARCHAR(255)
);
```

**Indexes**:
- `idx_performance_metrics_agent_id` on `agent_id`
- `idx_performance_metrics_timestamp` on `timestamp`
- `idx_performance_metrics_metric_name` on `metric_name`

#### 3. system_state
Key-value store for system-wide configuration and state.

```sql
CREATE TABLE IF NOT EXISTS system_state (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4. agent_heartbeats
Detailed heartbeat tracking for agent health monitoring.

```sql
CREATE TABLE IF NOT EXISTS agent_heartbeats (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50),
    message TEXT,
    metadata JSONB
);
```

**Indexes**:
- `idx_agent_heartbeats_agent_id` on `agent_id`
- `idx_agent_heartbeats_timestamp` on `timestamp`

#### 5. system_events
System-wide event logging and monitoring.

```sql
CREATE TABLE IF NOT EXISTS system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'info'
);
```

**Indexes**:
- `idx_system_events_timestamp` on `timestamp`
- `idx_system_events_event_type` on `event_type`
- `idx_system_events_severity` on `severity`

#### 6. help_requests & help_responses
AI help system for agent assistance.

```sql
CREATE TABLE IF NOT EXISTS help_requests (
    request_id VARCHAR(255) PRIMARY KEY,
    query TEXT NOT NULL,
    context JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS help_responses (
    request_id VARCHAR(255) PRIMARY KEY REFERENCES help_requests(request_id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    response TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'complete'
);
```

#### 7. agent_communications
Inter-agent communication tracking.

```sql
CREATE TABLE IF NOT EXISTS agent_communications (
    id SERIAL PRIMARY KEY,
    from_agent_id INTEGER REFERENCES agents(id),
    to_agent_id INTEGER REFERENCES agents(id),
    message_type VARCHAR(100),
    message_content TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent'
);
```

#### 8. llm_conversations
LLM conversation logging for AI agents.

```sql
CREATE TABLE IF NOT EXISTS llm_conversations (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    conversation_id VARCHAR(255),
    message_content TEXT,
    response_content TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);
```

---

## Agent Connection Patterns

### Current Active Agents

The system includes the following active agents:

1. **AgentCoordinator**: Central orchestration system
2. **HeartbeatHealthAgent**: Monitors agent health and heartbeats
3. **PerformanceMonitor**: Collects and analyzes performance metrics
4. **SharedStateMonitorAgent**: Monitors shared state changes
5. **EnhancedSharedStateMonitorAgent**: Advanced state monitoring
6. **LangSmithBridge**: Connects to LangSmith for tracing
7. **AIHelpAgent**: Provides AI assistance and help responses
8. **SelfHealingAgent**: Automatic system recovery
9. **AgentRestartManager**: Manages agent lifecycle
10. **LangGraphExecutor**: Executes LangGraph workflows

### Connection Patterns

#### 1. Direct PostgreSQL Connection
```python
from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter

# Direct adapter usage
adapter = PostgreSQLAdapter()
await adapter.initialize()
await adapter.register_agent(agent_id, agent_name)
```

#### 2. SharedState Interface
```python
from background_agents.coordination.shared_state import SharedState

# High-level interface
shared_state = SharedState(use_postgresql=True)
await shared_state.initialize()
await shared_state.update_agent_heartbeat(agent_id, heartbeat_data)
```

#### 3. Agent Coordinator Pattern
```python
from background_agents.coordination.agent_coordinator import AgentCoordinator

# Coordinator manages connections
coordinator = AgentCoordinator(shared_state)
await coordinator.register_agent(agent_instance)
```

### Connection Lifecycle

1. **Initialization**: Agent creates connection to shared state
2. **Registration**: Agent registers with coordinator
3. **Heartbeat**: Regular heartbeat updates
4. **State Updates**: State changes and metrics reporting
5. **Shutdown**: Clean connection closure

---

## Connection Procedures

### Standard Connection Procedure

#### 1. Environment Setup
```bash
# Set connection string
export POSTGRES_CONNECTION_STRING="postgresql://user:password@host:port/database"

# Or create config file
cat > postgres_config.json << EOF
{
    "user": "postgres",
    "password": "your_password",
    "host": "localhost",
    "port": 5432,
    "database": "background_agents"
}
EOF
```

#### 2. Agent Initialization
```python
from background_agents.coordination.shared_state import SharedState
from background_agents.coordination.base_agent import BaseAgent

class MyAgent(BaseAgent):
    async def _initialize_agent(self) -> bool:
        # Agent-specific initialization
        self.logger.info("Initializing MyAgent")
        return True
    
    async def _process_cycle(self) -> None:
        # Main agent logic
        await self.shared_state.update_agent_heartbeat(self.agent_id, {
            "agent_name": self.agent_name,
            "state": self.state.value,
            "timestamp": datetime.now().isoformat()
        })

# Usage
agent = MyAgent("my_agent")
shared_state = SharedState(use_postgresql=True)
await shared_state.initialize()

coordinator = AgentCoordinator(shared_state)
await coordinator.register_agent(agent)
```

### Connection Measurement Procedures

#### 1. Connection Health Check
```python
async def check_connection_health():
    adapter = PostgreSQLAdapter()
    await adapter.initialize()
    
    health = await adapter.get_database_health()
    return health
```

#### 2. Performance Metrics Collection
```python
async def collect_connection_metrics():
    adapter = PostgreSQLAdapter()
    stats = adapter.get_query_stats()
    
    metrics = {
        "total_queries": stats["total_queries"],
        "query_errors": stats["query_errors"],
        "connection_errors": stats["connection_errors"],
        "average_query_time": stats["average_query_time"]
    }
    return metrics
```

#### 3. Connection Pool Monitoring
```python
async def monitor_connection_pool():
    adapter = PostgreSQLAdapter()
    if adapter.pool:
        return {
            "pool_size": adapter.pool.get_size(),
            "pool_min_size": adapter.pool.get_min_size(),
            "pool_max_size": adapter.pool.get_max_size(),
            "pool_idle_connections": adapter.pool.get_idle_size()
        }
```

---

## Data Flow Diagrams

### System Architecture Diagram

```mermaid
graph TB
    subgraph "Agent Layer"
        A1[HeartbeatHealthAgent]
        A2[PerformanceMonitor]
        A3[SharedStateMonitorAgent]
        A4[LangSmithBridge]
        A5[AIHelpAgent]
        A6[SelfHealingAgent]
        A7[AgentRestartManager]
        A8[LangGraphExecutor]
    end
    
    subgraph "Coordination Layer"
        AC[AgentCoordinator]
        SS[SharedState]
        PA[PostgreSQLAdapter]
    end
    
    subgraph "Database Layer"
        PG[(PostgreSQL Database)]
        subgraph "Tables"
            T1[agents]
            T2[performance_metrics]
            T3[system_state]
            T4[agent_heartbeats]
            T5[system_events]
            T6[help_requests]
            T7[agent_communications]
            T8[llm_conversations]
        end
    end
    
    subgraph "External Systems"
        LS[LangSmith]
        LG[LangGraph]
        AI[AI Services]
    end
    
    A1 --> AC
    A2 --> AC
    A3 --> AC
    A4 --> AC
    A5 --> AC
    A6 --> AC
    A7 --> AC
    A8 --> AC
    
    AC --> SS
    SS --> PA
    PA --> PG
    
    PG --> T1
    PG --> T2
    PG --> T3
    PG --> T4
    PG --> T5
    PG --> T6
    PG --> T7
    PG --> T8
    
    A4 --> LS
    A8 --> LG
    A5 --> AI
    
    classDef agent fill:#e1f5fe
    classDef coordination fill:#f3e5f5
    classDef database fill:#e8f5e8
    classDef external fill:#fff3e0
    
    class A1,A2,A3,A4,A5,A6,A7,A8 agent
    class AC,SS,PA coordination
    class PG,T1,T2,T3,T4,T5,T6,T7,T8 database
    class LS,LG,AI external
```

### Agent State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> INITIALIZING
    INITIALIZING --> DEPLOYING : initialize()
    DEPLOYING --> MONITORING : deploy_complete()
    MONITORING --> ACTIVE : start()
    ACTIVE --> OPTIMIZING : optimization_request()
    OPTIMIZING --> ACTIVE : optimization_complete()
    ACTIVE --> STANDBY : standby_request()
    STANDBY --> ACTIVE : activate()
    ACTIVE --> MAINTENANCE : maintenance_request()
    MAINTENANCE --> ACTIVE : maintenance_complete()
    ACTIVE --> ERROR : error_occurred()
    ERROR --> RECOVERY : recovery_start()
    RECOVERY --> ACTIVE : recovery_complete()
    RECOVERY --> ERROR : recovery_failed()
    ERROR --> MANUAL : manual_intervention()
    MANUAL --> ACTIVE : manual_fixed()
    ACTIVE --> SHUTDOWN : shutdown_request()
    SHUTDOWN --> [*]
    
    note right of INITIALIZING
        Agent connects to PostgreSQL
        Registers with coordinator
    end note
    
    note right of ACTIVE
        Regular heartbeat updates
        Performance metrics collection
        State synchronization
    end note
```

### Database Connection Flow

```mermaid
sequenceDiagram
    participant A as Agent
    participant C as Coordinator
    participant SS as SharedState
    participant PA as PostgreSQLAdapter
    participant PG as PostgreSQL
    
    A->>C: Register Agent
    C->>SS: Initialize SharedState
    SS->>PA: Create Adapter
    PA->>PG: Create Connection Pool
    PG-->>PA: Pool Created
    PA-->>SS: Adapter Ready
    SS-->>C: SharedState Ready
    C->>A: Set shared_state reference
    
    loop Heartbeat Cycle
        A->>SS: update_agent_heartbeat()
        SS->>PA: update_agent_heartbeat()
        PA->>PG: INSERT/UPDATE agents
        PG-->>PA: Success
        PA-->>SS: Success
        SS-->>A: Success
    end
    
    loop Performance Metrics
        A->>SS: add_performance_metric()
        SS->>PA: add_performance_metric()
        PA->>PG: INSERT performance_metrics
        PG-->>PA: Success
        PA-->>SS: Success
        SS-->>A: Success
    end
    
    A->>C: Shutdown Request
    C->>SS: Cleanup
    SS->>PA: Close connections
    PA->>PG: Close pool
    PG-->>PA: Pool closed
```

---

## Migration Guide

### SQLite to PostgreSQL Migration

#### Changes Required for Each Agent Type

##### 1. HeartbeatHealthAgent
**Current SQLite Connection:**
```python
# Old pattern
self.shared_state = SharedState(sqlite_path="shared_state.db")
```

**New PostgreSQL Connection:**
```python
# New pattern
self.shared_state = SharedState(use_postgresql=True)
await self.shared_state.initialize()
```

**Required Changes:**
- Remove SQLite-specific initialization
- Update connection parameters
- Add async initialization
- Update heartbeat data structure

##### 2. PerformanceMonitor
**Current SQLite Connection:**
```python
# Old pattern
conn = sqlite3.connect('shared_state.db')
cursor.execute("INSERT INTO performance_metrics ...")
```

**New PostgreSQL Connection:**
```python
# New pattern
await self.shared_state.add_performance_metric(
    metric_name="processing_speed",
    value=speed_value,
    source_agent=self.agent_name
)
```

**Required Changes:**
- Replace direct SQLite queries with SharedState methods
- Update metric storage format
- Add async/await patterns
- Update data types for PostgreSQL compatibility

##### 3. SharedStateMonitorAgent
**Current SQLite Connection:**
```python
# Old pattern
self.db_connection = sqlite3.connect('shared_state.db')
```

**New PostgreSQL Connection:**
```python
# New pattern
self.shared_state = SharedState(use_postgresql=True)
await self.shared_state.initialize()
```

**Required Changes:**
- Remove direct database connections
- Use SharedState interface methods
- Update monitoring queries
- Handle async operations

##### 4. LangSmithBridge
**Current SQLite Connection:**
```python
# Old pattern
if self.shared_state and hasattr(self.shared_state, '_db_connection'):
    await self.shared_state._db_connection.execute(...)
```

**New PostgreSQL Connection:**
```python
# New pattern
await self.shared_state.log_system_event(
    event_type="langsmith_trace",
    event_data=trace_data
)
```

**Required Changes:**
- Remove direct database access
- Use event logging methods
- Update trace data storage
- Handle PostgreSQL-specific features

##### 5. AIHelpAgent
**Current SQLite Connection:**
```python
# Old pattern
conn = sqlite3.connect('shared_state.db')
cursor.execute("SELECT * FROM help_requests WHERE status = 'pending'")
```

**New PostgreSQL Connection:**
```python
# New pattern
pending_requests = await self.shared_state.get_pending_help_requests()
```

**Required Changes:**
- Replace direct SQL queries
- Use SharedState help methods
- Update request/response handling
- Handle async operations

### Migration Steps

#### 1. Database Setup
```bash
# Create PostgreSQL database
createdb background_agents

# Run schema setup
psql -d background_agents -f setup_postgresql_schema.sql
```

#### 2. Configuration Update
```python
# Update environment variables
export USE_POSTGRESQL=true
export POSTGRES_CONNECTION_STRING="postgresql://user:password@localhost:5432/background_agents"
```

#### 3. Code Updates
```python
# Update agent initialization
shared_state = SharedState(use_postgresql=True)
await shared_state.initialize()

# Update coordinator setup
coordinator = AgentCoordinator(shared_state)
```

#### 4. Testing
```python
# Test database connection
async def test_connection():
    adapter = PostgreSQLAdapter()
    success = await adapter.initialize()
    assert success, "Failed to connect to PostgreSQL"
    
    # Test basic operations
    await adapter.register_agent("test_agent", "TestAgent")
    agents = await adapter.get_registered_agents()
    assert len(agents) > 0
```

---

## Performance Monitoring

### Key Performance Indicators

#### 1. Connection Pool Metrics
- **Pool Size**: Current number of connections
- **Idle Connections**: Available connections
- **Active Connections**: Connections in use
- **Wait Time**: Time waiting for connections

#### 2. Query Performance
- **Query Execution Time**: Average time per query
- **Query Success Rate**: Percentage of successful queries
- **Query Errors**: Number of failed queries
- **Query Types**: Distribution of query types

#### 3. Agent Performance
- **Heartbeat Frequency**: Agent heartbeat intervals
- **State Change Frequency**: Agent state transitions
- **Metric Collection Rate**: Performance metrics per agent
- **Error Rate**: Agent error frequency

### Performance Optimization

#### 1. Connection Pool Tuning
```python
# Optimal pool settings
adapter = PostgreSQLAdapter(
    connection_string=conn_string,
    max_connections=20,  # Adjust based on load
    min_connections=5,   # Minimum pool size
    command_timeout=30   # Query timeout
)
```

#### 2. Query Optimization
```sql
-- Add indexes for frequent queries
CREATE INDEX idx_agents_last_heartbeat ON agents(last_heartbeat DESC);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp DESC);
CREATE INDEX idx_system_events_timestamp_type ON system_events(timestamp DESC, event_type);
```

#### 3. Monitoring Queries
```python
# Monitor slow queries
async def monitor_slow_queries():
    adapter = PostgreSQLAdapter()
    async with adapter.get_connection() as conn:
        slow_queries = await conn.fetch("""
            SELECT query, mean_time, calls 
            FROM pg_stat_statements 
            WHERE mean_time > 100 
            ORDER BY mean_time DESC
        """)
    return slow_queries
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Failures
**Symptoms:**
- "Failed to initialize PostgreSQL adapter"
- "Connection refused"
- "Connection pool exhausted"

**Solutions:**
```python
# Check connection string
print(os.getenv("POSTGRES_CONNECTION_STRING"))

# Test basic connection
import asyncpg
conn = await asyncpg.connect("postgresql://user:pass@host:port/db")
await conn.execute("SELECT 1")
```

#### 2. Schema Issues
**Symptoms:**
- "Table does not exist"
- "Column does not exist"
- "Constraint violation"

**Solutions:**
```python
# Recreate schema
adapter = PostgreSQLAdapter()
await adapter.initialize()
await adapter._create_schema()
```

#### 3. Performance Issues
**Symptoms:**
- Slow query execution
- High connection wait times
- Memory usage growth

**Solutions:**
```python
# Monitor performance
health = await adapter.get_database_health()
print(f"Active connections: {health['connections']['active']}")
print(f"Query stats: {adapter.get_query_stats()}")

# Optimize queries
await adapter.cleanup_old_data(days_to_keep=7)
```

#### 4. Agent Connection Issues
**Symptoms:**
- Agents stuck in "initializing" state
- Missing heartbeats
- State synchronization failures

**Solutions:**
```python
# Check agent registration
agents = await shared_state.get_registered_agents()
for agent in agents:
    print(f"Agent: {agent['agent_name']}, Status: {agent['status']}")

# Force agent state update
await shared_state.update_agent_state(agent_id, "active")
```

### Debugging Tools

#### 1. Connection Diagnostics
```python
async def diagnose_connection():
    adapter = PostgreSQLAdapter()
    
    # Test basic connection
    try:
        await adapter.initialize()
        print("✅ Connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    
    # Check pool status
    if adapter.pool:
        print(f"Pool size: {adapter.pool.get_size()}")
        print(f"Pool idle: {adapter.pool.get_idle_size()}")
```

#### 2. Query Analysis
```python
async def analyze_queries():
    adapter = PostgreSQLAdapter()
    stats = adapter.get_query_stats()
    
    print(f"Total queries: {stats['total_queries']}")
    print(f"Query errors: {stats['query_errors']}")
    print(f"Avg query time: {stats['average_query_time']:.3f}s")
```

#### 3. Agent Health Check
```python
async def check_agent_health():
    shared_state = SharedState(use_postgresql=True)
    await shared_state.initialize()
    
    active_agents = await shared_state.get_active_agents()
    stale_agents = await shared_state.get_stale_agents()
    
    print(f"Active agents: {len(active_agents)}")
    print(f"Stale agents: {len(stale_agents)}")
```

---

## Best Practices

### 1. Connection Management
- Use connection pooling for all database operations
- Implement proper connection cleanup
- Monitor connection pool utilization
- Set appropriate timeouts

### 2. Error Handling
- Implement retry logic with exponential backoff
- Log all database errors with context
- Provide fallback mechanisms
- Monitor error rates

### 3. Performance Optimization
- Use indexes for frequently queried columns
- Implement query result caching where appropriate
- Monitor and analyze slow queries
- Regular database maintenance

### 4. Security
- Use environment variables for connection strings
- Implement proper authentication
- Restrict database permissions
- Monitor for suspicious activity

### 5. Monitoring
- Track key performance metrics
- Set up alerts for critical issues
- Regular health checks
- Performance trend analysis

---

## Conclusion

The PostgreSQL-based shared state system provides a robust, scalable foundation for the background agents platform. By following the migration guide and best practices outlined in this document, agents can successfully transition from SQLite to PostgreSQL while maintaining performance and reliability.

For additional support or questions, refer to the troubleshooting section or consult the agent-specific documentation. 