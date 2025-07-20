-- Background Agents PostgreSQL Database Schema
-- Enterprise-grade schema for comprehensive agent monitoring and management

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set timezone to UTC for all operations
SET timezone = 'UTC';

-- ================================================================
-- CORE TABLES
-- ================================================================

-- Agent Registration and Management
CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(255) PRIMARY KEY,
    agent_type VARCHAR(100) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    agent_description TEXT,
    capabilities JSONB DEFAULT '[]'::jsonb,
    configuration JSONB DEFAULT '{}'::jsonb,
    state VARCHAR(50) DEFAULT 'inactive',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Performance optimization indexes
    CONSTRAINT valid_state CHECK (state IN ('active', 'inactive', 'error', 'maintenance', 'starting', 'stopping', 'restarting', 'resetting', 'busy', 'idle', 'shutdown'))
);

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_agents_state ON agents(state);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_last_seen ON agents(last_seen);
CREATE INDEX IF NOT EXISTS idx_agents_updated_at ON agents(updated_at);

-- Agent Heartbeat Tracking
CREATE TABLE IF NOT EXISTS agent_heartbeats (
    heartbeat_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    health_score FLOAT DEFAULT 100.0,
    cpu_usage_percent FLOAT,
    memory_usage_percent FLOAT,
    work_items_processed INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    processing_time_avg FLOAT,
    business_value_generated FLOAT DEFAULT 0.0,
    heartbeat_data JSONB DEFAULT '{}'::jsonb,
    
    -- Performance constraints
    CONSTRAINT valid_health_score CHECK (health_score >= 0 AND health_score <= 100),
    CONSTRAINT valid_cpu_usage CHECK (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100),
    CONSTRAINT valid_memory_usage CHECK (memory_usage_percent >= 0 AND memory_usage_percent <= 100)
);

-- Optimize heartbeat queries
CREATE INDEX IF NOT EXISTS idx_heartbeats_agent_timestamp ON agent_heartbeats(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_heartbeats_timestamp ON agent_heartbeats(timestamp);
CREATE INDEX IF NOT EXISTS idx_heartbeats_health_score ON agent_heartbeats(health_score);

-- Performance Metrics Collection
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_id VARCHAR(255) REFERENCES agents(agent_id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    tags JSONB DEFAULT '{}'::jsonb,
    business_context JSONB DEFAULT '{}'::jsonb,
    
    -- Composite index for efficient querying
    CONSTRAINT non_empty_metric_name CHECK (LENGTH(metric_name) > 0)
);

-- Optimize performance metric queries
CREATE INDEX IF NOT EXISTS idx_metrics_agent_name_timestamp ON performance_metrics(agent_id, metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON performance_metrics(metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp);

-- System Events and Logging
CREATE TABLE IF NOT EXISTS system_events (
    event_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    agent_id VARCHAR(255) REFERENCES agents(agent_id) ON DELETE SET NULL,
    severity VARCHAR(20) DEFAULT 'INFO',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    business_impact JSONB DEFAULT '{}'::jsonb,
    correlation_id VARCHAR(255),
    
    -- Ensure valid severity levels
    CONSTRAINT valid_severity CHECK (severity IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Optimize event queries
CREATE INDEX IF NOT EXISTS idx_events_type_timestamp ON system_events(event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_agent_timestamp ON system_events(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity_timestamp ON system_events(severity, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON system_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_correlation_id ON system_events(correlation_id);

-- Business Intelligence Metrics
CREATE TABLE IF NOT EXISTS business_metrics (
    business_metric_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    cost_impact FLOAT DEFAULT 0.0,
    revenue_impact FLOAT DEFAULT 0.0,
    
    -- Ensure meaningful categories
    CONSTRAINT non_empty_category CHECK (LENGTH(category) > 0),
    CONSTRAINT non_empty_metric_name CHECK (LENGTH(metric_name) > 0)
);

-- Optimize business metric queries
CREATE INDEX IF NOT EXISTS idx_business_metrics_category_timestamp ON business_metrics(category, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_business_metrics_name_timestamp ON business_metrics(metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_business_metrics_timestamp ON business_metrics(timestamp);

-- Agent Health History
CREATE TABLE IF NOT EXISTS agent_health_history (
    health_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    health_score FLOAT NOT NULL,
    health_details JSONB DEFAULT '{}'::jsonb,
    anomalies_detected JSONB DEFAULT '[]'::jsonb,
    recovery_actions JSONB DEFAULT '[]'::jsonb,
    business_impact_score FLOAT DEFAULT 0.0,
    
    -- Ensure valid health scores
    CONSTRAINT valid_health_score_range CHECK (health_score >= 0 AND health_score <= 100)
);

-- Optimize health history queries
CREATE INDEX IF NOT EXISTS idx_health_agent_timestamp ON agent_health_history(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_health_score ON agent_health_history(health_score);
CREATE INDEX IF NOT EXISTS idx_health_timestamp ON agent_health_history(timestamp);

-- Communication and Help Interactions
CREATE TABLE IF NOT EXISTS communication_logs (
    communication_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    interaction_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    agent_id VARCHAR(255) REFERENCES agents(agent_id) ON DELETE SET NULL,
    request_data JSONB DEFAULT '{}'::jsonb,
    response_data JSONB DEFAULT '{}'::jsonb,
    processing_time FLOAT,
    satisfaction_score FLOAT,
    business_value FLOAT DEFAULT 0.0,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure valid scores
    CONSTRAINT valid_satisfaction CHECK (satisfaction_score IS NULL OR (satisfaction_score >= 0 AND satisfaction_score <= 10))
);

-- Optimize communication queries
CREATE INDEX IF NOT EXISTS idx_communication_type_timestamp ON communication_logs(interaction_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_communication_user_timestamp ON communication_logs(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_communication_agent_timestamp ON communication_logs(agent_id, timestamp DESC);

-- ================================================================
-- ADVANCED FEATURES
-- ================================================================

-- Agent Dependencies and Relationships
CREATE TABLE IF NOT EXISTS agent_dependencies (
    dependency_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    parent_agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    dependent_agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    dependency_type VARCHAR(100) NOT NULL,
    dependency_strength FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent self-dependencies
    CONSTRAINT no_self_dependency CHECK (parent_agent_id != dependent_agent_id),
    -- Ensure valid dependency strength
    CONSTRAINT valid_strength CHECK (dependency_strength >= 0 AND dependency_strength <= 1),
    -- Prevent duplicate dependencies
    UNIQUE(parent_agent_id, dependent_agent_id, dependency_type)
);

-- System Configuration and Settings
CREATE TABLE IF NOT EXISTS system_configuration (
    config_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    config_category VARCHAR(255) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique configuration keys per category
    UNIQUE(config_category, config_key)
);

-- Performance Optimization Recommendations
CREATE TABLE IF NOT EXISTS optimization_recommendations (
    recommendation_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    recommendation_type VARCHAR(255) NOT NULL,
    target_component VARCHAR(255),
    recommendation_text TEXT NOT NULL,
    expected_improvement FLOAT,
    implementation_effort VARCHAR(50),
    business_impact FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    applied_at TIMESTAMPTZ,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'applied', 'rejected', 'expired'))
);

-- ================================================================
-- TRIGGERS AND AUTOMATION
-- ================================================================

-- Automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply automatic timestamp updates to relevant tables
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_configuration_updated_at BEFORE UPDATE ON system_configuration
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Automatic agent last_seen update on heartbeat
CREATE OR REPLACE FUNCTION update_agent_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE agents 
    SET last_seen = NEW.timestamp 
    WHERE agent_id = NEW.agent_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_last_seen_trigger AFTER INSERT ON agent_heartbeats
    FOR EACH ROW EXECUTE FUNCTION update_agent_last_seen();

-- ================================================================
-- VIEWS FOR ANALYTICS AND REPORTING
-- ================================================================

-- Agent Status Dashboard View
CREATE OR REPLACE VIEW agent_status_dashboard AS
SELECT 
    a.agent_id,
    a.agent_name,
    a.agent_type,
    a.state,
    a.last_seen,
    h.health_score,
    h.cpu_usage_percent,
    h.memory_usage_percent,
    h.timestamp as last_heartbeat,
    CASE 
        WHEN a.last_seen > NOW() - INTERVAL '5 minutes' THEN 'healthy'
        WHEN a.last_seen > NOW() - INTERVAL '15 minutes' THEN 'warning'
        ELSE 'critical'
    END as status_indicator,
    EXTRACT(EPOCH FROM (NOW() - a.last_seen))/60 as minutes_since_last_seen
FROM agents a
LEFT JOIN LATERAL (
    SELECT health_score, cpu_usage_percent, memory_usage_percent, timestamp
    FROM agent_heartbeats 
    WHERE agent_id = a.agent_id 
    ORDER BY timestamp DESC 
    LIMIT 1
) h ON true;

-- Performance Summary View
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    pm.agent_id,
    pm.metric_name,
    COUNT(*) as measurement_count,
    AVG(pm.metric_value) as avg_value,
    MIN(pm.metric_value) as min_value,
    MAX(pm.metric_value) as max_value,
    STDDEV(pm.metric_value) as std_deviation,
    pm.metric_unit,
    DATE_TRUNC('hour', pm.timestamp) as measurement_hour
FROM performance_metrics pm
WHERE pm.timestamp > NOW() - INTERVAL '24 hours'
GROUP BY pm.agent_id, pm.metric_name, pm.metric_unit, DATE_TRUNC('hour', pm.timestamp)
ORDER BY measurement_hour DESC, pm.agent_id, pm.metric_name;

-- Business Intelligence Summary View
CREATE OR REPLACE VIEW business_intelligence_summary AS
SELECT 
    bm.category,
    bm.metric_name,
    COUNT(*) as measurement_count,
    SUM(bm.metric_value) as total_value,
    AVG(bm.metric_value) as avg_value,
    SUM(bm.cost_impact) as total_cost_impact,
    SUM(bm.revenue_impact) as total_revenue_impact,
    DATE_TRUNC('day', bm.timestamp) as measurement_date
FROM business_metrics bm
WHERE bm.timestamp > NOW() - INTERVAL '30 days'
GROUP BY bm.category, bm.metric_name, DATE_TRUNC('day', bm.timestamp)
ORDER BY measurement_date DESC, bm.category, bm.metric_name;

-- System Health Overview
CREATE OR REPLACE VIEW system_health_overview AS
SELECT 
    COUNT(DISTINCT a.agent_id) as total_agents,
    COUNT(DISTINCT CASE WHEN a.state = 'active' THEN a.agent_id END) as active_agents,
    COUNT(DISTINCT CASE WHEN a.last_seen > NOW() - INTERVAL '5 minutes' THEN a.agent_id END) as healthy_agents,
    AVG(h.health_score) as avg_health_score,
    COUNT(DISTINCT CASE WHEN se.severity IN ('ERROR', 'CRITICAL') AND se.timestamp > NOW() - INTERVAL '1 hour' THEN se.event_id END) as recent_errors,
    AVG(pm.metric_value) FILTER (WHERE pm.metric_name = 'processing_time' AND pm.timestamp > NOW() - INTERVAL '1 hour') as avg_processing_time,
    NOW() as last_updated
FROM agents a
LEFT JOIN agent_heartbeats h ON a.agent_id = h.agent_id AND h.timestamp > NOW() - INTERVAL '1 hour'
LEFT JOIN system_events se ON a.agent_id = se.agent_id
LEFT JOIN performance_metrics pm ON a.agent_id = pm.agent_id;

-- ================================================================
-- DATA RETENTION AND CLEANUP PROCEDURES
-- ================================================================

-- Data retention function for automatic cleanup
CREATE OR REPLACE FUNCTION cleanup_old_data(retention_days INTEGER DEFAULT 30)
RETURNS TABLE(
    table_name TEXT,
    rows_deleted BIGINT
) AS $$
DECLARE
    cutoff_date TIMESTAMPTZ;
BEGIN
    cutoff_date := NOW() - (retention_days || ' days')::INTERVAL;
    
    -- Clean up old heartbeats
    DELETE FROM agent_heartbeats WHERE timestamp < cutoff_date;
    table_name := 'agent_heartbeats';
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN NEXT;
    
    -- Clean up old performance metrics
    DELETE FROM performance_metrics WHERE timestamp < cutoff_date;
    table_name := 'performance_metrics';
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN NEXT;
    
    -- Clean up old system events (keep critical events longer)
    DELETE FROM system_events 
    WHERE timestamp < cutoff_date 
    AND severity NOT IN ('ERROR', 'CRITICAL');
    table_name := 'system_events';
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN NEXT;
    
    -- Clean up old health history
    DELETE FROM agent_health_history WHERE timestamp < cutoff_date;
    table_name := 'agent_health_history';
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN NEXT;
    
    -- Clean up old communication logs
    DELETE FROM communication_logs WHERE timestamp < cutoff_date;
    table_name := 'communication_logs';
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN NEXT;
    
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- PERFORMANCE MONITORING FUNCTIONS
-- ================================================================

-- Function to get agent performance summary
CREATE OR REPLACE FUNCTION get_agent_performance_summary(
    p_agent_id VARCHAR(255),
    p_hours INTEGER DEFAULT 24
)
RETURNS TABLE(
    metric_name VARCHAR(255),
    avg_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    measurement_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pm.metric_name,
        AVG(pm.metric_value) as avg_value,
        MIN(pm.metric_value) as min_value,
        MAX(pm.metric_value) as max_value,
        COUNT(*) as measurement_count
    FROM performance_metrics pm
    WHERE pm.agent_id = p_agent_id
    AND pm.timestamp > NOW() - (p_hours || ' hours')::INTERVAL
    GROUP BY pm.metric_name
    ORDER BY pm.metric_name;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate system health score
CREATE OR REPLACE FUNCTION calculate_system_health_score()
RETURNS FLOAT AS $$
DECLARE
    health_score FLOAT;
    total_agents INTEGER;
    active_agents INTEGER;
    recent_errors INTEGER;
    avg_processing_time FLOAT;
BEGIN
    -- Get basic metrics
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN state = 'active' THEN 1 END)
    INTO total_agents, active_agents
    FROM agents;
    
    -- Get recent error count
    SELECT COUNT(*)
    INTO recent_errors
    FROM system_events
    WHERE severity IN ('ERROR', 'CRITICAL')
    AND timestamp > NOW() - INTERVAL '1 hour';
    
    -- Get average processing time
    SELECT AVG(metric_value)
    INTO avg_processing_time
    FROM performance_metrics
    WHERE metric_name = 'processing_time'
    AND timestamp > NOW() - INTERVAL '1 hour';
    
    -- Calculate composite health score (0-100)
    health_score := GREATEST(0, LEAST(100,
        (CASE WHEN total_agents > 0 THEN (active_agents::FLOAT / total_agents) * 40 ELSE 40 END) +
        (CASE WHEN recent_errors = 0 THEN 30 WHEN recent_errors <= 5 THEN 20 ELSE 10 END) +
        (CASE 
            WHEN avg_processing_time IS NULL THEN 20
            WHEN avg_processing_time <= 1.0 THEN 20
            WHEN avg_processing_time <= 5.0 THEN 15
            ELSE 10
        END) +
        10 -- Base operational score
    ));
    
    RETURN health_score;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- INITIAL CONFIGURATION DATA
-- ================================================================

-- Insert default system configuration
INSERT INTO system_configuration (config_category, config_key, config_value, description) VALUES
('monitoring', 'heartbeat_interval', '60', 'Default heartbeat interval in seconds'),
('monitoring', 'health_check_timeout', '30', 'Health check timeout in seconds'),
('monitoring', 'performance_retention_days', '30', 'Number of days to retain performance metrics'),
('alerts', 'error_threshold', '5', 'Number of errors before triggering alert'),
('alerts', 'response_time_threshold', '5.0', 'Response time threshold in seconds'),
('business', 'cost_per_agent_hour', '2.50', 'Estimated cost per agent hour in USD'),
('business', 'uptime_value_per_hour', '1000.0', 'Business value of system uptime per hour in USD')
ON CONFLICT (config_category, config_key) DO NOTHING;

-- Grant appropriate permissions
-- Note: In production, create specific roles with limited permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO background_agents_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO background_agents_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO background_agents_user;

-- Create indexes for optimal performance
-- Additional composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_heartbeats_agent_health_timestamp ON agent_heartbeats(agent_id, health_score, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_agent_value_timestamp ON performance_metrics(agent_id, metric_value, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity_type_timestamp ON system_events(severity, event_type, timestamp DESC);

-- Analyze tables for query optimization
ANALYZE agents;
ANALYZE agent_heartbeats;
ANALYZE performance_metrics;
ANALYZE system_events;
ANALYZE business_metrics;
ANALYZE agent_health_history;
ANALYZE communication_logs;

-- Display schema creation summary
DO $$
BEGIN
    RAISE NOTICE 'Background Agents PostgreSQL Schema created successfully!';
    RAISE NOTICE 'Tables created: 8 core tables + 3 advanced feature tables';
    RAISE NOTICE 'Views created: 4 analytical views for reporting';
    RAISE NOTICE 'Functions created: 3 maintenance and analytics functions';
    RAISE NOTICE 'Triggers created: 3 automation triggers';
    RAISE NOTICE 'Initial configuration: 7 default settings inserted';
    RAISE NOTICE 'Performance optimization: 15+ indexes created for query efficiency';
END $$; 