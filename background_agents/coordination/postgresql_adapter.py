"""
PostgreSQL Adapter for Background Agents System

Provides high-performance PostgreSQL database connectivity with connection pooling,
async operations, and comprehensive error handling for the background agents system.
"""

import asyncio
import asyncpg
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

class PostgreSQLAdapter:
    """
    High-performance PostgreSQL adapter with connection pooling.
    
    Features:
    - Async connection pooling for optimal performance
    - Comprehensive error handling and retries
    - JSON/JSONB support for complex data structures
    - Transaction management
    - Performance monitoring and logging
    """
    
    def __init__(self, **kwargs):
        """Initialize PostgreSQL adapter with configuration."""
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'background_agents'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'ssl': os.getenv('DB_SSL_MODE', 'prefer'),
            'min_size': int(os.getenv('DB_POOL_MIN_SIZE', '5')),
            'max_size': int(os.getenv('DB_POOL_MAX_SIZE', '20')),
            'timeout': int(os.getenv('DB_TIMEOUT', '30')),
            **kwargs
        }
        
        self.pool = None
        self._initialized = False
        self._connection_count = 0
        self._query_count = 0
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self._initialized:
            return
        
        try:
            logger.info(f"Initializing PostgreSQL connection pool...")
            logger.info(f"Connecting to {self.config['host']}:{self.config['port']}/{self.config['database']}")
            
            self.pool = await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                ssl=self.config['ssl'],
                min_size=self.config['min_size'],
                max_size=self.config['max_size'],
                command_timeout=self.config['timeout'],
                server_settings={
                    'jit': 'off',  # Disable JIT for better connection performance
                    'application_name': 'background_agents_system'
                }
            )
            
            # Test the connection
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT version()')
                logger.info(f"Connected to PostgreSQL: {result}")
            
            self._initialized = True
            logger.info("PostgreSQL adapter initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL adapter: {e}")
            raise
    
    async def close(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            self._connection_count += 1
            try:
                yield connection
            finally:
                pass  # Connection automatically returned to pool
    
    async def execute_query(self, query: str, *args, fetch_mode: str = 'none') -> Any:
        """
        Execute a query with error handling and retries.
        
        Args:
            query: SQL query string
            *args: Query parameters
            fetch_mode: 'none', 'one', 'all', 'val'
        
        Returns:
            Query result based on fetch_mode
        """
        retries = 3
        for attempt in range(retries):
            try:
                async with self.get_connection() as conn:
                    self._query_count += 1
                    
                    if fetch_mode == 'none':
                        result = await conn.execute(query, *args)
                    elif fetch_mode == 'one':
                        result = await conn.fetchrow(query, *args)
                    elif fetch_mode == 'all':
                        result = await conn.fetch(query, *args)
                    elif fetch_mode == 'val':
                        result = await conn.fetchval(query, *args)
                    else:
                        raise ValueError(f"Invalid fetch_mode: {fetch_mode}")
                    
                    return result
                    
            except Exception as e:
                logger.error(f"Query execution failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    
    async def execute_transaction(self, queries: List[tuple]) -> List[Any]:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of tuples (query, args, fetch_mode)
        
        Returns:
            List of query results
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                results = []
                for query, args, fetch_mode in queries:
                    if fetch_mode == 'none':
                        result = await conn.execute(query, *args)
                    elif fetch_mode == 'one':
                        result = await conn.fetchrow(query, *args)
                    elif fetch_mode == 'all':
                        result = await conn.fetch(query, *args)
                    elif fetch_mode == 'val':
                        result = await conn.fetchval(query, *args)
                    else:
                        raise ValueError(f"Invalid fetch_mode: {fetch_mode}")
                    
                    results.append(result)
                
                return results
    
    # Agent-specific database operations
    
    async def register_agent(self, agent_id: str, state: str, metadata: Dict[str, Any] = None):
        """Register or update an agent in the database."""
        query = """
        INSERT INTO agents (agent_id, state, started_at, metadata, updated_at)
        VALUES ($1, $2, $3, $4, NOW())
        ON CONFLICT (agent_id) 
        DO UPDATE SET 
            state = EXCLUDED.state,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        """
        
        metadata = metadata or {}
        started_at = datetime.now(timezone.utc)
        
        await self.execute_query(
            query, 
            agent_id, 
            state, 
            started_at, 
            json.dumps(metadata)
        )
    
    async def update_agent_state(self, agent_id: str, state: str, metadata: Dict[str, Any] = None):
        """Update agent state."""
        query = """
        UPDATE agents 
        SET state = $1, metadata = $2, updated_at = NOW()
        WHERE agent_id = $3
        """
        
        metadata = metadata or {}
        await self.execute_query(
            query, 
            state, 
            json.dumps(metadata), 
            agent_id
        )
    
    async def log_heartbeat(self, agent_id: str, timestamp: datetime, heartbeat_data: Dict[str, Any]):
        """Log agent heartbeat."""
        query = """
        INSERT INTO agent_heartbeats (agent_id, timestamp, state, error_count, metrics)
        VALUES ($1, $2, $3, $4, $5)
        """
        
        await self.execute_query(
            query,
            agent_id,
            timestamp,
            heartbeat_data.get('state', 'unknown'),
            heartbeat_data.get('error_count', 0),
            json.dumps(heartbeat_data.get('metrics', {}))
        )
    
    async def log_performance_metric(self, agent_id: str, metric_name: str, value: float, unit: str = None, metadata: Dict[str, Any] = None):
        """Log performance metric."""
        query = """
        INSERT INTO performance_metrics (agent_id, metric_name, value, unit, metadata)
        VALUES ($1, $2, $3, $4, $5)
        """
        
        await self.execute_query(
            query,
            agent_id,
            metric_name,
            value,
            unit,
            json.dumps(metadata or {})
        )
    
    async def log_system_event(self, event_type: str, event_data: Dict[str, Any], agent_id: str = None, severity: str = 'INFO'):
        """Log system event."""
        query = """
        INSERT INTO system_events (event_type, event_data, agent_id, severity)
        VALUES ($1, $2, $3, $4)
        """
        
        await self.execute_query(
            query,
            event_type,
            json.dumps(event_data),
            agent_id,
            severity
        )
    
    async def get_agent_status(self, agent_id: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get agent status."""
        if agent_id:
            query = "SELECT * FROM agents WHERE agent_id = $1"
            result = await self.execute_query(query, agent_id, fetch_mode='one')
            return dict(result) if result else None
        else:
            query = "SELECT * FROM agents ORDER BY updated_at DESC"
            results = await self.execute_query(query, fetch_mode='all')
            return [dict(row) for row in results]
    
    async def get_recent_heartbeats(self, agent_id: str = None, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get recent heartbeats."""
        if agent_id:
            query = """
            SELECT * FROM agent_heartbeats 
            WHERE agent_id = $1 AND timestamp > NOW() - INTERVAL '%s minutes'
            ORDER BY timestamp DESC
            """ % minutes
            results = await self.execute_query(query, agent_id, fetch_mode='all')
        else:
            query = """
            SELECT * FROM agent_heartbeats 
            WHERE timestamp > NOW() - INTERVAL '%s minutes'
            ORDER BY timestamp DESC
            """ % minutes
            results = await self.execute_query(query, fetch_mode='all')
        
        return [dict(row) for row in results]
    
    async def get_performance_metrics(self, agent_id: str = None, hours: int = 1) -> List[Dict[str, Any]]:
        """Get performance metrics."""
        if agent_id:
            query = """
            SELECT * FROM performance_metrics 
            WHERE agent_id = $1 AND timestamp > NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
            """ % hours
            results = await self.execute_query(query, agent_id, fetch_mode='all')
        else:
            query = """
            SELECT * FROM performance_metrics 
            WHERE timestamp > NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
            """ % hours
            results = await self.execute_query(query, fetch_mode='all')
        
        return [dict(row) for row in results]
    
    async def get_system_events(self, event_type: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system events."""
        if event_type:
            query = """
            SELECT * FROM system_events 
            WHERE event_type = $1 AND timestamp > NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
            """ % hours
            results = await self.execute_query(query, event_type, fetch_mode='all')
        else:
            query = """
            SELECT * FROM system_events 
            WHERE timestamp > NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
            """ % hours
            results = await self.execute_query(query, fetch_mode='all')
        
        return [dict(row) for row in results]
    
    # AI Help System operations
    
    async def create_help_request(self, request_id: str, user_id: str, content: str, context: Dict[str, Any] = None) -> str:
        """Create a help request."""
        query = """
        INSERT INTO help_requests (request_id, user_id, content, context)
        VALUES ($1, $2, $3, $4)
        RETURNING request_id
        """
        
        result = await self.execute_query(
            query,
            request_id,
            user_id,
            content,
            json.dumps(context or {}),
            fetch_mode='val'
        )
        
        return result
    
    async def create_help_response(self, request_id: str, response_id: str, content: str, confidence_score: float = None, sources: List[str] = None, agent_id: str = None):
        """Create a help response."""
        query = """
        INSERT INTO help_responses (request_id, response_id, content, confidence_score, sources, agent_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        await self.execute_query(
            query,
            request_id,
            response_id,
            content,
            confidence_score,
            json.dumps(sources or []),
            agent_id
        )
    
    async def get_help_requests(self, status: str = None, user_id: str = None) -> List[Dict[str, Any]]:
        """Get help requests."""
        if status and user_id:
            query = "SELECT * FROM help_requests WHERE status = $1 AND user_id = $2 ORDER BY created_at DESC"
            results = await self.execute_query(query, status, user_id, fetch_mode='all')
        elif status:
            query = "SELECT * FROM help_requests WHERE status = $1 ORDER BY created_at DESC"
            results = await self.execute_query(query, status, fetch_mode='all')
        elif user_id:
            query = "SELECT * FROM help_requests WHERE user_id = $1 ORDER BY created_at DESC"
            results = await self.execute_query(query, user_id, fetch_mode='all')
        else:
            query = "SELECT * FROM help_requests ORDER BY created_at DESC LIMIT 100"
            results = await self.execute_query(query, fetch_mode='all')
        
        return [dict(row) for row in results]
    
    async def get_help_responses(self, request_id: str) -> List[Dict[str, Any]]:
        """Get help responses for a request."""
        query = "SELECT * FROM help_responses WHERE request_id = $1 ORDER BY generated_at DESC"
        results = await self.execute_query(query, request_id, fetch_mode='all')
        return [dict(row) for row in results]
    
    # Utility methods
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        queries = [
            ("SELECT COUNT(*) FROM agents", [], 'val'),
            ("SELECT COUNT(*) FROM agent_heartbeats", [], 'val'),
            ("SELECT COUNT(*) FROM performance_metrics", [], 'val'),
            ("SELECT COUNT(*) FROM system_events", [], 'val'),
            ("SELECT COUNT(*) FROM help_requests", [], 'val'),
            ("SELECT COUNT(*) FROM help_responses", [], 'val'),
        ]
        
        results = await self.execute_transaction(queries)
        
        return {
            'agents': results[0],
            'heartbeats': results[1],
            'performance_metrics': results[2],
            'system_events': results[3],
            'help_requests': results[4],
            'help_responses': results[5],
            'connection_count': self._connection_count,
            'query_count': self._query_count,
            'pool_size': self.pool.get_size() if self.pool else 0,
            'pool_idle': self.pool.get_idle_size() if self.pool else 0
        }
    
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            async with self.get_connection() as conn:
                await conn.fetchval('SELECT 1')
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def __repr__(self):
        """String representation."""
        return f"<PostgreSQLAdapter(host={self.config['host']}, db={self.config['database']}, pool_size={self.config['max_size']})>" 