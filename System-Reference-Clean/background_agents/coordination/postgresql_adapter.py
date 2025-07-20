"""
PostgreSQL Adapter for Enterprise Agent System

High-performance PostgreSQL integration with connection pooling,
transaction management, health monitoring, and business intelligence.
"""

import asyncio
import asyncpg
import logging
import json
from typing import Dict, List, Optional, Any, Union
# Optional automatic .env loading to support validation scripts that
# assume credentials are provided via a local .env file rather than
# pre-exported environment variables.
try:
    from dotenv import load_dotenv  # type: ignore

    # Load only once at import; nested load_dotenv calls are cheap/no-op.
    load_dotenv()
except ModuleNotFoundError:
    # python-dotenv is not an obligatory dependency; ignore if missing.
    pass
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dataclasses import dataclass
import os


@dataclass
class ConnectionConfig:
    """PostgreSQL connection configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: int = 60
    server_settings: Dict[str, str] = None


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def safe_json_dumps(data: Any) -> str:
    """Safely serialize data to JSON, handling datetime objects"""
    try:
        return json.dumps(data, cls=DateTimeEncoder)
    except (TypeError, ValueError) as e:
        # If direct serialization fails, convert datetime objects to strings
        if isinstance(data, dict):
            safe_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    safe_data[key] = value.isoformat()
                elif isinstance(value, dict):
                    safe_data[key] = {k: v.isoformat() if isinstance(v, datetime) else v 
                                    for k, v in value.items()}
                elif isinstance(value, list):
                    safe_data[key] = [item.isoformat() if isinstance(item, datetime) else item 
                                    for item in value]
                else:
                    safe_data[key] = value
            return json.dumps(safe_data)
        elif isinstance(data, list):
            safe_data = [item.isoformat() if isinstance(item, datetime) else item 
                        for item in data]
            return json.dumps(safe_data)
        else:
            return json.dumps(str(data))  # fallback to string representation


class PostgreSQLAdapter:
    """
    Enterprise PostgreSQL Adapter with High-Performance Features
    
    Features:
    - Connection pooling with automatic scaling
    - Transaction management with isolation levels
    - Health monitoring and performance analytics
    - Business intelligence data structures
    - Comprehensive error handling and recovery
    """
    
    def __init__(self, config: Union[ConnectionConfig, Dict[str, Any], None] = None):
        """Initialize adapter with flexible config input.

        The validation scripts sometimes provide a plain ``dict`` instead of a
        ``ConnectionConfig`` instance. To make the adapter more resilient we
        convert such dictionaries on-the-fly. If *config* is ``None`` we fall
        back to environment variables.
        """

        # Accept raw dicts for backwards-compatibility with validation scripts
        if isinstance(config, dict):
            config = self._dict_to_config(config)

        self.config = config or self._load_config_from_env()
        self.connection_pool = None
        self.is_initialized = False
        
        # Performance tracking
        self.connection_stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'queries_executed': 0,
            'transactions_committed': 0,
            'transactions_rolled_back': 0,
            'errors_encountered': 0
        }
        
        # Health monitoring
        self.last_health_check = None
        self.health_status = 'unknown'
        
        # Setup logging
        self.logger = logging.getLogger("postgresql_adapter")
        
    def _dict_to_config(self, cfg: Dict[str, Any]) -> ConnectionConfig:
        """Convert a plain dictionary to ``ConnectionConfig``.

        Missing keys are filled with sane defaults so that older calling code
        which only sets e.g. ``host``/``database`` continues to work. Any extra
        keys are ignored.
        """
        defaults = self._load_config_from_env()
        return ConnectionConfig(
            host=cfg.get("host") or os.getenv("POSTGRESQL_HOST", defaults.host),
            port=int(cfg.get("port") or os.getenv("POSTGRESQL_PORT", defaults.port)),
            database=cfg.get("database") or os.getenv("POSTGRESQL_DATABASE", defaults.database),
            user=cfg.get("user") or os.getenv("POSTGRESQL_USER", defaults.user),
            password=(cfg.get("password") or os.getenv("POSTGRESQL_PASSWORD", defaults.password) or ""),
            min_connections=int(cfg.get("min_connections", defaults.min_connections)),
            max_connections=int(cfg.get("max_connections", defaults.max_connections)),
            command_timeout=int(cfg.get("command_timeout", defaults.command_timeout)),
            server_settings=cfg.get("server_settings", defaults.server_settings),
        )
        
    def _load_config_from_env(self) -> ConnectionConfig:
        """Load configuration from environment variables"""
        return ConnectionConfig(
            host=os.getenv('POSTGRESQL_HOST', 'localhost'),
            port=int(os.getenv('POSTGRESQL_PORT', 5432)),
            database=os.getenv('POSTGRESQL_DATABASE', 'background_agents'),
            user=os.getenv('POSTGRESQL_USER', 'postgres'),
            password=os.getenv('POSTGRESQL_PASSWORD', ''),
            min_connections=int(os.getenv('POSTGRESQL_POOL_SIZE', 10)) // 2,
            max_connections=int(os.getenv('POSTGRESQL_POOL_SIZE', 10)),
            command_timeout=int(os.getenv('POSTGRESQL_TIMEOUT', 60)),
            server_settings={
                'application_name': 'background_agents_system',
                'search_path': 'public',
                'timezone': 'UTC'
            }
        )
        
    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool and database schema"""
        try:
            self.logger.info("Initializing PostgreSQL adapter...")
            
            # Create connection pool
            self.connection_pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings
            )
            
            # Verify connection and schema
            await self.verify_database_schema()
            
            # Initialize health monitoring
            await self.initialize_health_monitoring()
            
            self.is_initialized = True
            self.health_status = 'healthy'
            
            self.logger.info(
                f"PostgreSQL adapter initialized successfully "
                f"({self.config.min_connections}-{self.config.max_connections} connections)"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL adapter: {e}")
            self.health_status = 'failed'
            raise
            
    async def verify_database_schema(self) -> None:
        """Verify and create database schema if needed"""
        try:
            async with self.connection_pool.acquire() as connection:
                # Check if required tables exist
                required_tables = [
                    'agents',
                    'agent_heartbeats',
                    'performance_metrics',
                    'system_events',
                    'business_analytics'
                ]
                
                for table in required_tables:
                    exists = await self.table_exists(connection, table)
                    if not exists:
                        await self.create_table(connection, table)
                        
                self.logger.info("Database schema verification completed")
                
        except Exception as e:
            self.logger.error(f"Schema verification failed: {e}")
            raise
            
    async def table_exists(self, connection, table_name: str) -> bool:
        """Check if table exists"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = $1
            )
        """
        return await connection.fetchval(query, table_name)
        
    async def create_table(self, connection, table_name: str) -> None:
        """Create table with schema"""
        schemas = {
            'agents': """
                CREATE TABLE agents (
                    agent_id VARCHAR(255) PRIMARY KEY,
                    agent_type VARCHAR(100) NOT NULL,
                    agent_name VARCHAR(255) NOT NULL,
                    state VARCHAR(50) NOT NULL DEFAULT 'initializing',
                    registration_data JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """,
            'agent_heartbeats': """
                CREATE TABLE agent_heartbeats (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    heartbeat_data JSONB,
                    health_score FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
                )
            """,
            'performance_metrics': """
                CREATE TABLE performance_metrics (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(255) NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    metric_unit VARCHAR(50),
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
                )
            """,
            'system_events': """
                CREATE TABLE system_events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    event_data JSONB,
                    agent_id VARCHAR(255),
                    severity VARCHAR(20) DEFAULT 'INFO',
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
                )
            """,
            'business_analytics': """
                CREATE TABLE business_analytics (
                    id SERIAL PRIMARY KEY,
                    metric_category VARCHAR(100) NOT NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    metadata JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                )
            """
        }
        
        if table_name in schemas:
            await connection.execute(schemas[table_name])
            self.logger.info(f"Created table: {table_name}")
            
            # Create indexes for performance
            await self.create_table_indexes(connection, table_name)
        else:
            raise ValueError(f"Unknown table schema: {table_name}")
            
    async def create_table_indexes(self, connection, table_name: str) -> None:
        """Create performance indexes for tables"""
        indexes = {
            'agents': [
                "CREATE INDEX idx_agents_state ON agents(state)",
                "CREATE INDEX idx_agents_type ON agents(agent_type)",
                "CREATE INDEX idx_agents_updated ON agents(updated_at)"
            ],
            'agent_heartbeats': [
                "CREATE INDEX idx_heartbeats_agent_id ON agent_heartbeats(agent_id)",
                "CREATE INDEX idx_heartbeats_timestamp ON agent_heartbeats(timestamp)",
                "CREATE INDEX idx_heartbeats_agent_time ON agent_heartbeats(agent_id, timestamp)"
            ],
            'performance_metrics': [
                "CREATE INDEX idx_metrics_agent_id ON performance_metrics(agent_id)",
                "CREATE INDEX idx_metrics_name ON performance_metrics(metric_name)",
                "CREATE INDEX idx_metrics_timestamp ON performance_metrics(timestamp)",
                "CREATE INDEX idx_metrics_agent_metric ON performance_metrics(agent_id, metric_name)"
            ],
            'system_events': [
                "CREATE INDEX idx_events_type ON system_events(event_type)",
                "CREATE INDEX idx_events_agent_id ON system_events(agent_id)",
                "CREATE INDEX idx_events_timestamp ON system_events(timestamp)",
                "CREATE INDEX idx_events_severity ON system_events(severity)"
            ],
            'business_analytics': [
                "CREATE INDEX idx_analytics_category ON business_analytics(metric_category)",
                "CREATE INDEX idx_analytics_name ON business_analytics(metric_name)",
                "CREATE INDEX idx_analytics_timestamp ON business_analytics(timestamp)"
            ]
        }
        
        if table_name in indexes:
            for index_sql in indexes[table_name]:
                try:
                    await connection.execute(index_sql)
                except Exception as e:
                    # Index might already exist
                    if "already exists" not in str(e):
                        self.logger.warning(f"Failed to create index: {e}")
                        
    async def initialize_health_monitoring(self) -> None:
        """Initialize health monitoring capabilities"""
        try:
            # Test connection pool health
            async with self.connection_pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
                
            self.last_health_check = datetime.now(timezone.utc)
            self.logger.info("Health monitoring initialized")
            
        except Exception as e:
            self.logger.error(f"Health monitoring initialization failed: {e}")
            raise
            
    @asynccontextmanager
    async def get_connection(self):
        """Get connection from pool with automatic resource management"""
        if not self.is_initialized:
            raise RuntimeError("PostgreSQL adapter not initialized")
            
        connection = None
        try:
            connection = await self.connection_pool.acquire()
            self.connection_stats['connections_created'] += 1
            yield connection
        finally:
            if connection:
                await self.connection_pool.release(connection)
                self.connection_stats['connections_closed'] += 1
                
    @asynccontextmanager
    async def transaction(self, isolation_level: str = 'read_committed'):
        """Transaction context manager with isolation level support"""
        async with self.get_connection() as connection:
            async with connection.transaction(isolation=isolation_level):
                try:
                    yield connection
                    self.connection_stats['transactions_committed'] += 1
                except Exception:
                    self.connection_stats['transactions_rolled_back'] += 1
                    raise
                    
    # Agent Management Operations
    
    async def register_agent(self, agent_id: str, registration_data: Dict[str, Any]) -> None:
        """Register new agent in database"""
        try:
            async with self.get_connection() as connection:
                await connection.execute(
                    """
                    INSERT INTO agents (agent_id, agent_type, agent_name, registration_data)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (agent_id) 
                    DO UPDATE SET 
                        agent_type = EXCLUDED.agent_type,
                        agent_name = EXCLUDED.agent_name,
                        registration_data = EXCLUDED.registration_data,
                        updated_at = NOW()
                    """,
                    agent_id,
                    registration_data.get('agent_type', 'Unknown'),
                    registration_data.get('agent_name', agent_id),
                    json.dumps(registration_data)
                )
                
            self.connection_stats['queries_executed'] += 1
            self.logger.debug(f"Agent {agent_id} registered successfully")
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to register agent {agent_id}: {e}")
            raise
            
    async def update_agent_state(self, agent_id: str, state: str, metadata: Dict = None) -> None:
        """Update agent state"""
        try:
            async with self.get_connection() as connection:
                if metadata:
                    await connection.execute(
                        """
                        UPDATE agents 
                        SET state = $2, registration_data = registration_data || $3, updated_at = NOW()
                        WHERE agent_id = $1
                        """,
                        agent_id, state, json.dumps(metadata)
                    )
                else:
                    await connection.execute(
                        "UPDATE agents SET state = $2, updated_at = NOW() WHERE agent_id = $1",
                        agent_id, state
                    )
                    
            self.connection_stats['queries_executed'] += 1
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to update agent state for {agent_id}: {e}")
            raise
            
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent status and registration data"""
        try:
            async with self.get_connection() as connection:
                row = await connection.fetchrow(
                    """
                    SELECT agent_id, agent_type, agent_name, state, 
                           registration_data, created_at, updated_at
                    FROM agents WHERE agent_id = $1
                    """,
                    agent_id
                )
                
            self.connection_stats['queries_executed'] += 1
            
            if row:
                registration_data = json.loads(row['registration_data']) if row['registration_data'] else {}
                return {
                    'agent_id': row['agent_id'],
                    'agent_type': row['agent_type'],
                    'agent_name': row['agent_name'],
                    'state': row['state'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    **registration_data
                }
            return None
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to get agent status for {agent_id}: {e}")
            raise
            
    async def get_registered_agents(self, states: List[str] = None) -> List[Dict[str, Any]]:
        """Get all registered agents, optionally filtered by states"""
        try:
            async with self.get_connection() as connection:
                if states:
                    query = """
                        SELECT agent_id, agent_type, agent_name, state, 
                               registration_data, created_at, updated_at
                        FROM agents WHERE state = ANY($1)
                        ORDER BY created_at
                    """
                    rows = await connection.fetch(query, states)
                else:
                    query = """
                        SELECT agent_id, agent_type, agent_name, state, 
                               registration_data, created_at, updated_at
                        FROM agents ORDER BY created_at
                    """
                    rows = await connection.fetch(query)
                    
            self.connection_stats['queries_executed'] += 1
            
            agents = []
            for row in rows:
                registration_data = json.loads(row['registration_data']) if row['registration_data'] else {}
                agents.append({
                    'agent_id': row['agent_id'],
                    'agent_type': row['agent_type'],
                    'agent_name': row['agent_name'],
                    'state': row['state'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    **registration_data
                })
                
            return agents
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to get registered agents: {e}")
            raise
            
    # Heartbeat Operations
    
    async def update_agent_heartbeat(self, agent_id: str, timestamp: datetime, 
                                   heartbeat_data: Dict[str, Any]) -> None:
        """Update agent heartbeat with comprehensive data"""
        try:
            health_score = heartbeat_data.get('health_score', 100.0)
            
            async with self.get_connection() as connection:
                await connection.execute(
                    """
                    INSERT INTO agent_heartbeats (agent_id, timestamp, heartbeat_data, health_score)
                    VALUES ($1, $2, $3, $4)
                    """,
                    agent_id, timestamp, safe_json_dumps(heartbeat_data), health_score
                )
                
            self.connection_stats['queries_executed'] += 1
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to update heartbeat for {agent_id}: {e}")
            raise
            
    async def get_recent_heartbeats(self, agent_id: str = None, minutes: int = 10) -> List[Dict[str, Any]]:
        """Get recent heartbeats.

        If *agent_id* is provided we filter by that agent, otherwise we return
        heartbeats for all agents within the given time window. This overload
        keeps backward-compatibility with external validation scripts that call
        the function with only the *minutes* argument.
        """
        try:
            async with self.get_connection() as connection:
                if agent_id:
                    query = f"""
                        SELECT agent_id, timestamp FROM agent_heartbeats
                        WHERE agent_id = $1 
                        AND timestamp >= NOW() - INTERVAL '{minutes} minutes'
                        ORDER BY timestamp DESC
                    """
                    rows = await connection.fetch(query, agent_id)
                else:
                    query = f"""
                        SELECT agent_id, timestamp FROM agent_heartbeats
                        WHERE timestamp >= NOW() - INTERVAL '{minutes} minutes'
                        ORDER BY timestamp DESC
                    """
                    rows = await connection.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get recent heartbeats: {e}")
            return []
            
    async def get_agent_health_data(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get agent health data over time"""
        try:
            async with self.get_connection() as connection:
                query = f"""
                    SELECT timestamp, heartbeat_data, health_score
                    FROM agent_heartbeats
                    WHERE agent_id = $1 
                    AND timestamp >= NOW() - INTERVAL '{hours} hours'
                    ORDER BY timestamp DESC
                """
                rows = await connection.fetch(query, agent_id)
                
            self.connection_stats['queries_executed'] += 1
            
            health_data = []
            for row in rows:
                heartbeat_data = json.loads(row['heartbeat_data']) if row['heartbeat_data'] else {}
                health_data.append({
                    'timestamp': row['timestamp'],
                    'health_score': row['health_score'],
                    **heartbeat_data
                })
                
            return health_data
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to get health data for {agent_id}: {e}")
            raise
            
    # Performance Metrics Operations
    
    async def log_performance_metric(self, metric_name: str, value: float, unit: str, 
                                   agent_id: str = None) -> None:
        """Log performance metric to database"""
        try:
            # For system-level metrics, check if agent exists to avoid foreign key constraint
            valid_agent_id = None
            if agent_id:
                async with self.get_connection() as connection:
                    agent_exists = await connection.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM agents WHERE agent_id = $1)", 
                        agent_id
                    )
                    
                if agent_exists:
                    valid_agent_id = agent_id
                else:
                    # Log as system metric without agent_id to avoid foreign key constraint
                    self.logger.debug(f"Agent {agent_id} not found in registry, logging as system metric")
                    
            async with self.get_connection() as connection:
                await connection.execute(
                    """
                    INSERT INTO performance_metrics (agent_id, metric_name, metric_value, metric_unit)
                    VALUES ($1, $2, $3, $4)
                    """,
                    valid_agent_id, metric_name, value, unit
                )
                
            self.connection_stats['queries_executed'] += 1
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to log performance metric {metric_name}: {e}")
            raise
            
    async def get_performance_metrics(self, agent_id: str = None, metric_name: str = None, 
                                    hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance metrics with optional filtering"""
        try:
            async with self.get_connection() as connection:
                conditions = [f"timestamp >= NOW() - INTERVAL '{hours} hours'"]
                params = []
                
                if agent_id:
                    conditions.append("agent_id = $%d" % (len(params) + 1))
                    params.append(agent_id)
                    
                if metric_name:
                    conditions.append("metric_name = $%d" % (len(params) + 1))
                    params.append(metric_name)
                    
                query = f"""
                    SELECT agent_id, metric_name, metric_value, metric_unit, timestamp
                    FROM performance_metrics
                    WHERE {' AND '.join(conditions)}
                    ORDER BY timestamp DESC
                """
                
                rows = await connection.fetch(query, *params)
                
            self.connection_stats['queries_executed'] += 1
            
            return [
                {
                    'agent_id': row['agent_id'],
                    'metric_name': row['metric_name'],
                    'metric_value': row['metric_value'],
                    'metric_unit': row['metric_unit'],
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to get performance metrics: {e}")
            raise
            
    # System Events Operations
    
    async def log_system_event(self, event_type: str, event_data: Dict[str, Any], 
                             agent_id: str = None, severity: str = 'INFO') -> None:
        """Log system event to database"""
        try:
            # For system-level events, check if agent exists to avoid foreign key constraint
            valid_agent_id = None
            if agent_id:
                async with self.get_connection() as connection:
                    agent_exists = await connection.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM agents WHERE agent_id = $1)", 
                        agent_id
                    )
                    
                if agent_exists:
                    valid_agent_id = agent_id
                else:
                    # Log as system event without agent_id to avoid foreign key constraint
                    self.logger.debug(f"Agent {agent_id} not found in registry, logging as system event")
                    
            async with self.get_connection() as connection:
                await connection.execute(
                    """
                    INSERT INTO system_events (event_type, event_data, agent_id, severity)
                    VALUES ($1, $2, $3, $4)
                    """,
                    event_type, safe_json_dumps(event_data), valid_agent_id, severity
                )
                
            self.connection_stats['queries_executed'] += 1
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to log system event {event_type}: {e}")
            raise
            
    async def get_system_events(self, event_type: str = None, agent_id: str = None, 
                              severity: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system events with optional filtering"""
        try:
            async with self.get_connection() as connection:
                conditions = [f"timestamp >= NOW() - INTERVAL '{hours} hours'"]
                params = []
                
                if event_type:
                    conditions.append("event_type = $%d" % (len(params) + 1))
                    params.append(event_type)
                    
                if agent_id:
                    conditions.append("agent_id = $%d" % (len(params) + 1))
                    params.append(agent_id)
                    
                if severity:
                    conditions.append("severity = $%d" % (len(params) + 1))
                    params.append(severity)
                    
                query = f"""
                    SELECT id, event_type, event_data, agent_id, severity, timestamp
                    FROM system_events
                    WHERE {' AND '.join(conditions)}
                    ORDER BY timestamp DESC
                """
                
                rows = await connection.fetch(query, *params)
                
            self.connection_stats['queries_executed'] += 1
            
            events = []
            for row in rows:
                event_data = json.loads(row['event_data']) if row['event_data'] else {}
                events.append({
                    'id': row['id'],
                    'event_type': row['event_type'],
                    'agent_id': row['agent_id'],
                    'severity': row['severity'],
                    'timestamp': row['timestamp'],
                    **event_data
                })
                
            return events
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to get system events: {e}")
            raise
            
    # Business Analytics Operations
    
    async def log_business_metric(self, category: str, metric_name: str, value: float, 
                                metadata: Dict[str, Any] = None) -> None:
        """Log business intelligence metric"""
        try:
            async with self.get_connection() as connection:
                await connection.execute(
                    """
                    INSERT INTO business_analytics (metric_category, metric_name, metric_value, metadata)
                    VALUES ($1, $2, $3, $4)
                    """,
                    category, metric_name, value, safe_json_dumps(metadata) if metadata else None
                )
                
            self.connection_stats['queries_executed'] += 1
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to log business metric {metric_name}: {e}")
            raise
            
    async def get_business_metrics(self, category: str = None, metric_name: str = None, 
                                 hours: int = 24) -> List[Dict[str, Any]]:
        """Get business analytics metrics"""
        try:
            async with self.get_connection() as connection:
                conditions = [f"timestamp >= NOW() - INTERVAL '{hours} hours'"]
                params = []
                
                if category:
                    conditions.append("metric_category = $%d" % (len(params) + 1))
                    params.append(category)
                    
                if metric_name:
                    conditions.append("metric_name = $%d" % (len(params) + 1))
                    params.append(metric_name)
                    
                query = f"""
                    SELECT metric_category, metric_name, metric_value, metadata, timestamp
                    FROM business_analytics
                    WHERE {' AND '.join(conditions)}
                    ORDER BY timestamp DESC
                """
                
                rows = await connection.fetch(query, *params)
                
            self.connection_stats['queries_executed'] += 1
            
            metrics = []
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                metrics.append({
                    'category': row['metric_category'],
                    'metric_name': row['metric_name'],
                    'value': row['metric_value'],
                    'timestamp': row['timestamp'],
                    **metadata
                })
                
            return metrics
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Failed to get business metrics: {e}")
            raise
            
    # Health and Monitoring Operations
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection pool status"""
        if not self.connection_pool:
            return {'status': 'not_initialized'}
            
        return {
            'status': self.health_status,
            'pool_size': self.connection_pool.get_size(),
            'pool_idle': self.connection_pool.get_idle_size(),
            'last_health_check': self.last_health_check,
            'connection_stats': self.connection_stats
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # Test connection
            async with self.get_connection() as connection:
                await connection.fetchval("SELECT 1")
                
            # Test query performance
            async with self.get_connection() as connection:
                await connection.fetchval("SELECT COUNT(*) FROM agents")
                
            end_time = datetime.now(timezone.utc)
            response_time = (end_time - start_time).total_seconds()
            
            self.last_health_check = end_time
            self.health_status = 'healthy'
            
            return {
                'status': 'healthy',
                'response_time_seconds': response_time,
                'pool_status': {
                    'size': self.connection_pool.get_size(),
                    'idle': self.connection_pool.get_idle_size()
                },
                'connection_stats': self.connection_stats,
                'last_check': self.last_health_check
            }
            
        except Exception as e:
            self.health_status = 'unhealthy'
            self.logger.error(f"Health check failed: {e}")
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_stats': self.connection_stats,
                'last_check': datetime.now(timezone.utc)
            }
            
    async def get_database_performance(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            async with self.get_connection() as connection:
                # Get database size
                db_size = await connection.fetchval(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                )
                
                # Get table sizes
                table_sizes = await connection.fetch("""
                    SELECT schemaname, tablename,
                           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)
                
                # Get connection count
                connection_count = await connection.fetchval(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                )
                
            return {
                'database_size': db_size,
                'table_sizes': [dict(row) for row in table_sizes],
                'active_connections': connection_count,
                'pool_size': self.connection_pool.get_size(),
                'pool_idle': self.connection_pool.get_idle_size(),
                'connection_stats': self.connection_stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get database performance: {e}")
            return {'error': str(e)}
            
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data to maintain performance"""
        try:
            cleanup_stats = {}
            
            async with self.transaction() as connection:
                # Cleanup old heartbeats
                heartbeat_count = await connection.fetchval(
                    f"DELETE FROM agent_heartbeats WHERE timestamp < NOW() - INTERVAL '{days} days' RETURNING count(*)"
                )
                cleanup_stats['heartbeats_deleted'] = heartbeat_count or 0
                
                # Cleanup old performance metrics
                metrics_count = await connection.fetchval(
                    f"DELETE FROM performance_metrics WHERE timestamp < NOW() - INTERVAL '{days} days' RETURNING count(*)"
                )
                cleanup_stats['metrics_deleted'] = metrics_count or 0
                
                # Cleanup old system events (keep errors longer)
                events_count = await connection.fetchval(
                    f"""
                    DELETE FROM system_events 
                    WHERE timestamp < NOW() - INTERVAL '{days} days' 
                    AND severity NOT IN ('ERROR', 'CRITICAL')
                    RETURNING count(*)
                    """
                )
                cleanup_stats['events_deleted'] = events_count or 0
                
            self.logger.info(f"Data cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
            raise
            
    async def reconnect(self) -> None:
        """Reconnect to database (useful for recovery)"""
        try:
            self.logger.info("Attempting to reconnect to PostgreSQL...")
            
            if self.connection_pool:
                await self.connection_pool.close()
                
            # Reinitialize
            await self.initialize()
            
            self.logger.info("PostgreSQL reconnection successful")
            
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            raise
            
    # Generic Query Methods (for SystemInitializer compatibility)
    
    async def execute_query(self, query: str, *params) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        try:
            async with self.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                
            self.connection_stats['queries_executed'] += 1
            
            # Convert rows to list of dictionaries
            result = []
            for row in rows:
                result.append(dict(row))
                
            return result
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Query execution failed: {e}")
            raise
            
    async def execute_raw_sql(self, sql: str) -> None:
        """Execute raw SQL (CREATE, ALTER, DROP, etc.)"""
        try:
            async with self.get_connection() as connection:
                await connection.execute(sql)
                
            self.connection_stats['queries_executed'] += 1
            self.logger.debug(f"Raw SQL executed successfully: {sql[:100]}...")
            
        except Exception as e:
            self.connection_stats['errors_encountered'] += 1
            self.logger.error(f"Raw SQL execution failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close connection pool gracefully"""
        try:
            if self.connection_pool:
                await self.connection_pool.close()
                self.logger.info("PostgreSQL connection pool closed")
                
            self.is_initialized = False
            self.health_status = 'closed'
            
        except Exception as e:
            self.logger.error(f"Error closing connection pool: {e}")
            raise 

    def _run_sync(self, coro):
        """Helper to run *coro* in a synchronous context even if an event loop is already running."""
        try:
            return asyncio.run(coro)
        except RuntimeError:
            # Running inside an existing event-loop (e.g. Jupyter, Streamlit)
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

    def test_connection(self) -> bool:
        """Synchronous connectivity check for validation scripts (non-await)."""
        try:
            return self._run_sync(self._async_test_connection())
        except Exception as e:
            self.logger.error(f"PostgreSQL test_connection failed: {e}")
            return False

    async def _async_test_connection(self) -> bool:
        """Internal async connectivity check"""
        if not self.connection_pool:
            await self.initialize()
        async with self.connection_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return True

    async def get_all_agents(self) -> List[str]:
        """Asynchronously fetch all registered agent IDs."""
        try:
            if not self.connection_pool:
                await self.initialize()
            async with self.connection_pool.acquire() as conn:
                rows = await conn.fetch("SELECT agent_id FROM agents")
                return [row["agent_id"] for row in rows]
        except Exception as e:
            self.logger.error(f"get_all_agents failed: {e}")
            return []

    # Legacy synchronous helper for older code paths (not used by validation)
    def get_all_agents_sync(self) -> List[str]:
        try:
            return self._run_sync(self.get_all_agents())
        except Exception as e:
            self.logger.error(f"get_all_agents_sync failed: {e}")
            return []