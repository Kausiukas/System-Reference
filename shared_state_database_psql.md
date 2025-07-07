
# PostgreSQL Database Documentation: Background Agents System

**Database Name:** `background_agents`  
**Version:** PostgreSQL 12+  
**Architecture:** Multi-agent shared state with real-time monitoring

---

## 🏗️ Database Architecture Overview

The background agents system uses PostgreSQL as the central shared state database, replacing SQLite for improved concurrency, performance, and reliability. The database serves as the single source of truth for all agent coordination, monitoring, and communication.

### Key Features
- **High Concurrency**: PostgreSQL connection pooling supports multiple agents
- **Real-time Monitoring**: Performance metrics and health tracking
- **AI Integration**: Help requests/responses with LLM conversation storage
- **Audit Trail**: Complete system event logging
- **Scalability**: Designed for production workloads

---

## 📋 Database Schema

### Core Tables

#### 1. `agents` - Agent Registration & State
```sql
CREATE TABLE agents (
    agent_id VARCHAR(255) PRIMARY KEY,
    state VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,
    config JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agents_state ON agents(state);
CREATE INDEX idx_agents_started_at ON agents(started_at);
```

#### 2. `agent_heartbeats` - Health Monitoring
```sql
CREATE TABLE agent_heartbeats (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    state VARCHAR(50),
    error_count INTEGER DEFAULT 0,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_heartbeats_agent_timestamp ON agent_heartbeats(agent_id, timestamp DESC);
CREATE INDEX idx_heartbeats_timestamp ON agent_heartbeats(timestamp DESC);
```

#### 3. `performance_metrics` - System Performance
```sql
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value NUMERIC,
    unit VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_metrics_agent_name_timestamp ON performance_metrics(agent_id, metric_name, timestamp DESC);
CREATE INDEX idx_metrics_timestamp ON performance_metrics(timestamp DESC);
```

#### 4. `system_state` - Global System State
```sql
CREATE TABLE system_state (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(255)
);

CREATE INDEX idx_system_state_key ON system_state(key);
```

#### 5. `system_events` - Event Logging
```sql
CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    agent_id VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'INFO'
);

CREATE INDEX idx_events_type_timestamp ON system_events(event_type, timestamp DESC);
CREATE INDEX idx_events_agent_timestamp ON system_events(agent_id, timestamp DESC);
CREATE INDEX idx_events_severity ON system_events(severity);
```

### AI Help System Tables

#### 6. `help_requests` - User Help Requests
```sql
CREATE TABLE help_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    context JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_help_requests_status ON help_requests(status);
CREATE INDEX idx_help_requests_user_id ON help_requests(user_id);
CREATE INDEX idx_help_requests_created_at ON help_requests(created_at DESC);
```

#### 7. `help_responses` - AI-Generated Responses
```sql
CREATE TABLE help_responses (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL,
    response_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    confidence_score NUMERIC,
    sources JSONB,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    agent_id VARCHAR(255),
    FOREIGN KEY (request_id) REFERENCES help_requests(request_id) ON DELETE CASCADE
);

CREATE INDEX idx_help_responses_request_id ON help_responses(request_id);
CREATE INDEX idx_help_responses_confidence ON help_responses(confidence_score DESC);
```

#### 8. `agent_communications` - Inter-Agent Messages
```sql
CREATE TABLE agent_communications (
    id SERIAL PRIMARY KEY,
    from_agent VARCHAR(255) NOT NULL,
    to_agent VARCHAR(255) NOT NULL,
    message_type VARCHAR(100) NOT NULL,
    content JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent'
);

CREATE INDEX idx_communications_to_agent ON agent_communications(to_agent, timestamp DESC);
CREATE INDEX idx_communications_type ON agent_communications(message_type);
```

#### 9. `llm_conversations` - LLM Interaction History
```sql
CREATE TABLE llm_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255),
    prompt TEXT NOT NULL,
    response TEXT,
    model VARCHAR(100),
    tokens_used INTEGER,
    cost NUMERIC,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_llm_conversations_agent ON llm_conversations(agent_id, timestamp DESC);
CREATE INDEX idx_llm_conversations_model ON llm_conversations(model, timestamp DESC);
```

---

## 🔧 Database Configuration

### Connection Settings
```env
# PostgreSQL Configuration
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=background_agents
POSTGRESQL_USER=bg_agents_user
POSTGRESQL_PASSWORD=secure_password_here
POSTGRESQL_SSL_MODE=prefer

# Connection Pool Settings
POSTGRESQL_POOL_SIZE=10
POSTGRESQL_TIMEOUT=30
```

### Performance Optimization
```sql
-- Enable query optimization
SET shared_preload_libraries = 'pg_stat_statements';
SET track_activity_query_size = 2048;
SET log_min_duration_statement = 1000;

-- Memory settings for performance
SET shared_buffers = '256MB';
SET effective_cache_size = '1GB';
SET work_mem = '16MB';
SET maintenance_work_mem = '64MB';
```

---

## 🔌 Agent Connection Patterns

### Connection Management
Each agent maintains a connection pool to PostgreSQL:

```python
# Example connection pattern for agents
from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter

class ExampleAgent(BaseAgent):
    def __init__(self, agent_id, shared_state):
        super().__init__(agent_id, shared_state)
        self.db = PostgreSQLAdapter()
    
    async def do_work(self):
        # Use connection pool for database operations
        await self.db.execute_query(
            "INSERT INTO performance_metrics (agent_id, metric_name, value) VALUES ($1, $2, $3)",
            self.agent_id, "cpu_usage", 25.5
        )
```

### Agent Registration Flow
1. **Agent Startup**: Register in `agents` table
2. **Heartbeat Loop**: Regular updates to `agent_heartbeats`
3. **Performance Metrics**: Log metrics to `performance_metrics`
4. **Event Logging**: System events to `system_events`
5. **Graceful Shutdown**: Update agent state and cleanup

---

## 📊 Monitoring & Performance

### Key Performance Indicators (KPIs)

#### Database Performance
- **Connection Pool Utilization**: Target < 80%
- **Query Response Time**: Target < 100ms for 95th percentile
- **Transaction Throughput**: Target > 1000 TPS
- **Lock Contention**: Target < 5% blocking queries

#### Agent Health Metrics
- **Heartbeat Frequency**: Every 60 seconds per agent
- **Failed Heartbeats**: Alert if > 2 consecutive misses
- **Performance Metrics**: Collected every 30 seconds
- **Error Rate**: Alert if > 5% of operations fail

### Monitoring Queries

#### Active Agents
```sql
SELECT 
    agent_id,
    state,
    started_at,
    NOW() - started_at AS uptime
FROM agents 
WHERE state = 'running'
ORDER BY started_at;
```

#### Recent Heartbeats
```sql
SELECT 
    agent_id,
    timestamp,
    state,
    error_count,
    metrics->'cpu_usage' as cpu_usage
FROM agent_heartbeats 
WHERE timestamp > NOW() - INTERVAL '5 minutes'
ORDER BY timestamp DESC;
```

#### Performance Metrics Summary
```sql
SELECT 
    agent_id,
    metric_name,
    AVG(value) as avg_value,
    MAX(value) as max_value,
    COUNT(*) as sample_count
FROM performance_metrics 
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY agent_id, metric_name
ORDER BY agent_id, metric_name;
```

#### System Health Overview
```sql
SELECT 
    'Total Agents' as metric,
    COUNT(*) as value
FROM agents
UNION ALL
SELECT 
    'Running Agents' as metric,
    COUNT(*) as value
FROM agents WHERE state = 'running'
UNION ALL
SELECT 
    'Recent Heartbeats (5min)' as metric,
    COUNT(*) as value
FROM agent_heartbeats WHERE timestamp > NOW() - INTERVAL '5 minutes'
UNION ALL
SELECT 
    'Error Events (1hour)' as metric,
    COUNT(*) as value
FROM system_events WHERE severity = 'ERROR' AND timestamp > NOW() - INTERVAL '1 hour';
```

---

## 🔄 Migration from SQLite

### Migration Process
1. **Backup SQLite**: Create backup of existing `shared_state.db`
2. **Schema Creation**: Execute PostgreSQL schema creation scripts
3. **Data Migration**: Transfer existing data using migration scripts
4. **Configuration Update**: Update environment variables
5. **Testing**: Validate all operations work correctly

### Migration Script Usage
```bash
# 1. Setup PostgreSQL environment
python setup_postgresql_environment.py

# 2. Run migration
python migrate_sqlite_to_postgresql.py --source shared_state.db --target postgresql

# 3. Validate migration
python test_postgresql_migration.py
```

### Data Migration Mapping
- `agents` table → PostgreSQL `agents`
- SQLite heartbeat data → PostgreSQL `agent_heartbeats`
- Performance data → PostgreSQL `performance_metrics`
- System events → PostgreSQL `system_events`

---

## 🛠️ Maintenance & Administration

### Regular Maintenance Tasks

#### Daily
```sql
-- Update table statistics
ANALYZE;

-- Check for long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

#### Weekly
```sql
-- Vacuum analyze for performance
VACUUM ANALYZE;

-- Check database size
SELECT pg_size_pretty(pg_database_size('background_agents'));

-- Archive old data (keep 30 days)
DELETE FROM agent_heartbeats WHERE timestamp < NOW() - INTERVAL '30 days';
DELETE FROM performance_metrics WHERE timestamp < NOW() - INTERVAL '30 days';
DELETE FROM system_events WHERE timestamp < NOW() - INTERVAL '30 days';
```

#### Monthly
```sql
-- Full vacuum (schedule during maintenance window)
VACUUM FULL;

-- Reindex for performance
REINDEX DATABASE background_agents;
```

### Backup Strategy
```bash
# Daily backup
pg_dump -h localhost -U bg_agents_user -d background_agents > backup_$(date +%Y%m%d).sql

# Continuous WAL archiving
archive_mode = on
archive_command = 'cp %p /backup/archive/%f'
```

---

## 🔒 Security Configuration

### User Management
```sql
-- Create dedicated user for agents
CREATE USER bg_agents_user WITH PASSWORD 'secure_password_here';

-- Grant minimal required permissions
GRANT CONNECT ON DATABASE background_agents TO bg_agents_user;
GRANT USAGE ON SCHEMA public TO bg_agents_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bg_agents_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bg_agents_user;
```

### Connection Security
```conf
# postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'

# pg_hba.conf
hostssl background_agents bg_agents_user 0.0.0.0/0 md5
```

---

## 🚀 Performance Optimization

### Index Strategy
- **Primary Keys**: All tables have optimized primary keys
- **Foreign Keys**: Proper foreign key constraints with indexes
- **Temporal Data**: Timestamp-based indexes for time-series queries
- **JSON Data**: GIN indexes on JSONB columns for fast searches

### Query Optimization
```sql
-- Enable query plan analysis
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM agent_heartbeats 
WHERE agent_id = 'performance_monitor' 
AND timestamp > NOW() - INTERVAL '1 hour';

-- Create materialized views for complex reports
CREATE MATERIALIZED VIEW agent_health_summary AS
SELECT 
    agent_id,
    COUNT(*) as heartbeat_count,
    MAX(timestamp) as last_heartbeat,
    AVG((metrics->>'cpu_usage')::numeric) as avg_cpu
FROM agent_heartbeats 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY agent_id;
```

---

## 📈 Scaling Considerations

### Horizontal Scaling
- **Read Replicas**: Configure read replicas for dashboard queries
- **Connection Pooling**: Use PgBouncer for connection management
- **Partitioning**: Partition time-series tables by date

### Vertical Scaling
- **Memory**: Increase `shared_buffers` and `effective_cache_size`
- **CPU**: Optimize `max_worker_processes` and `max_parallel_workers`
- **Storage**: Use fast SSD storage with proper RAID configuration

---

## 🔧 Troubleshooting Guide

### Common Issues

#### Connection Pool Exhaustion
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Identify long-running connections
SELECT pid, state, query_start, query FROM pg_stat_activity 
WHERE state != 'idle' AND query_start < NOW() - INTERVAL '10 minutes';
```

#### Performance Degradation
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Check table bloat
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
       (n_dead_tup::float / (n_live_tup + n_dead_tup)) * 100 AS dead_percentage
FROM pg_stat_user_tables 
WHERE n_dead_tup > 0 
ORDER BY dead_percentage DESC;
```

#### Disk Space Issues
```sql
-- Check database sizes
SELECT datname, pg_size_pretty(pg_database_size(datname)) 
FROM pg_database 
ORDER BY pg_database_size(datname) DESC;

-- Check largest tables
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;
```

---

## ✅ Production Readiness Checklist

### Infrastructure
- [ ] PostgreSQL 12+ installed and configured
- [ ] Connection pooling configured (PgBouncer recommended)
- [ ] SSL/TLS encryption enabled
- [ ] Backup strategy implemented
- [ ] Monitoring tools configured

### Security
- [ ] Dedicated database user with minimal permissions
- [ ] Network security configured (firewall, VPN)
- [ ] Regular security updates scheduled
- [ ] Audit logging enabled

### Performance
- [ ] Appropriate hardware sizing
- [ ] Index optimization completed
- [ ] Query performance validated
- [ ] Load testing completed

### Monitoring
- [ ] Database monitoring tools configured
- [ ] Alert thresholds set
- [ ] Dashboard integration tested
- [ ] Log analysis tools configured

---

*This documentation provides comprehensive guidance for deploying, managing, and optimizing the PostgreSQL database infrastructure for the background agents system.* 