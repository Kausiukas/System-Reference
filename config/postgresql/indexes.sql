-- PostgreSQL Performance Indexes for Background Agents System
-- This file contains all performance-critical indexes for the background agents database

-- ===============================
-- AGENT HEARTBEATS INDEXES
-- ===============================

-- Primary performance index for agent heartbeat queries
CREATE INDEX IF NOT EXISTS idx_agent_heartbeats_agent_timestamp 
ON agent_heartbeats(agent_id, timestamp DESC);

-- Index for heartbeat cleanup operations
CREATE INDEX IF NOT EXISTS idx_agent_heartbeats_timestamp 
ON agent_heartbeats(timestamp);

-- Index for agent status queries
CREATE INDEX IF NOT EXISTS idx_agent_heartbeats_status 
ON agent_heartbeats(status);

-- ===============================
-- AGENT STATES INDEXES
-- ===============================

-- Primary index for agent state lookups
CREATE INDEX IF NOT EXISTS idx_agent_states_agent_id 
ON agent_states(agent_id);

-- Index for agent state queries by status
CREATE INDEX IF NOT EXISTS idx_agent_states_status 
ON agent_states(status);

-- Index for agent state queries by last seen
CREATE INDEX IF NOT EXISTS idx_agent_states_last_seen 
ON agent_states(last_seen DESC);

-- ===============================
-- PERFORMANCE METRICS INDEXES
-- ===============================

-- Primary index for performance metrics queries
CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent_timestamp 
ON performance_metrics(agent_id, timestamp DESC);

-- Index for metrics cleanup operations
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp 
ON performance_metrics(timestamp);

-- Index for metrics queries by metric type
CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_type 
ON performance_metrics(metric_type);

-- ===============================
-- SYSTEM EVENTS INDEXES
-- ===============================

-- Primary index for system event queries
CREATE INDEX IF NOT EXISTS idx_system_events_timestamp 
ON system_events(timestamp DESC);

-- Index for event queries by source
CREATE INDEX IF NOT EXISTS idx_system_events_source 
ON system_events(source);

-- Index for event queries by event type
CREATE INDEX IF NOT EXISTS idx_system_events_event_type 
ON system_events(event_type);

-- Index for event queries by severity
CREATE INDEX IF NOT EXISTS idx_system_events_severity 
ON system_events(severity);

-- ===============================
-- SHARED STATE INDEXES
-- ===============================

-- Primary index for shared state key lookups
CREATE INDEX IF NOT EXISTS idx_shared_state_key 
ON shared_state(key);

-- Index for shared state queries by updated timestamp
CREATE INDEX IF NOT EXISTS idx_shared_state_updated_at 
ON shared_state(updated_at DESC);

-- ===============================
-- AGENT CONFIGURATIONS INDEXES
-- ===============================

-- Primary index for agent configuration lookups
CREATE INDEX IF NOT EXISTS idx_agent_configurations_agent_id 
ON agent_configurations(agent_id);

-- Index for configuration queries by updated timestamp
CREATE INDEX IF NOT EXISTS idx_agent_configurations_updated_at 
ON agent_configurations(updated_at DESC);

-- ===============================
-- LANGGRAPH TRACES INDEXES
-- ===============================

-- Primary index for LangGraph trace queries
CREATE INDEX IF NOT EXISTS idx_langgraph_traces_run_id 
ON langgraph_traces(run_id);

-- Index for trace queries by timestamp
CREATE INDEX IF NOT EXISTS idx_langgraph_traces_timestamp 
ON langgraph_traces(timestamp DESC);

-- Index for trace queries by agent
CREATE INDEX IF NOT EXISTS idx_langgraph_traces_agent_id 
ON langgraph_traces(agent_id);

-- Index for trace queries by status
CREATE INDEX IF NOT EXISTS idx_langgraph_traces_status 
ON langgraph_traces(status);

-- ===============================
-- COMMUNICATION LOGS INDEXES
-- ===============================

-- Primary index for communication log queries
CREATE INDEX IF NOT EXISTS idx_communication_logs_timestamp 
ON communication_logs(timestamp DESC);

-- Index for communication queries by source agent
CREATE INDEX IF NOT EXISTS idx_communication_logs_source_agent 
ON communication_logs(source_agent);

-- Index for communication queries by target agent
CREATE INDEX IF NOT EXISTS idx_communication_logs_target_agent 
ON communication_logs(target_agent);

-- Index for communication queries by message type
CREATE INDEX IF NOT EXISTS idx_communication_logs_message_type 
ON communication_logs(message_type);

-- ===============================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- ===============================

-- Composite index for agent health monitoring
CREATE INDEX IF NOT EXISTS idx_agent_health_composite 
ON agent_heartbeats(agent_id, status, timestamp DESC);

-- Composite index for performance analysis
CREATE INDEX IF NOT EXISTS idx_performance_analysis_composite 
ON performance_metrics(agent_id, metric_type, timestamp DESC);

-- Composite index for event correlation
CREATE INDEX IF NOT EXISTS idx_event_correlation_composite 
ON system_events(source, event_type, timestamp DESC);

-- ===============================
-- PARTIAL INDEXES FOR EFFICIENCY
-- ===============================

-- Partial index for active agents only
CREATE INDEX IF NOT EXISTS idx_active_agents_partial 
ON agent_states(agent_id, last_seen DESC) 
WHERE status = 'active';

-- Partial index for failed heartbeats
CREATE INDEX IF NOT EXISTS idx_failed_heartbeats_partial 
ON agent_heartbeats(agent_id, timestamp DESC) 
WHERE status = 'failed';

-- Partial index for high-severity events
CREATE INDEX IF NOT EXISTS idx_high_severity_events_partial 
ON system_events(timestamp DESC, source) 
WHERE severity IN ('ERROR', 'CRITICAL');

-- ===============================
-- MAINTENANCE COMMANDS
-- ===============================

-- Analyze all tables for query optimization
-- Run these commands periodically for optimal performance

-- ANALYZE agent_heartbeats;
-- ANALYZE agent_states;
-- ANALYZE performance_metrics;
-- ANALYZE system_events;
-- ANALYZE shared_state;
-- ANALYZE agent_configurations;
-- ANALYZE langgraph_traces;
-- ANALYZE communication_logs;

-- ===============================
-- NOTES
-- ===============================

-- 1. These indexes are designed for the most common query patterns
-- 2. Monitor query performance and adjust indexes as needed
-- 3. Consider dropping unused indexes to save space and improve write performance
-- 4. Use EXPLAIN ANALYZE to validate index usage in production queries
-- 5. Regular maintenance with VACUUM and ANALYZE is recommended 