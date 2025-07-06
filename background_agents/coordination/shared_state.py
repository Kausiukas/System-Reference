"""
Shared State Management for Background Agents System

Provides centralized state management using PostgreSQL as the backend database.
Handles agent registration, coordination, metrics, and communication between agents.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import json

from .postgresql_adapter import PostgreSQLAdapter

logger = logging.getLogger(__name__)

class SharedState:
    """
    Centralized shared state management using PostgreSQL.
    
    Provides high-level operations for:
    - Agent lifecycle management
    - Performance metrics collection
    - System event logging
    - AI help system integration
    - Inter-agent communication
    """
    
    def __init__(self, adapter: PostgreSQLAdapter = None):
        """Initialize shared state with PostgreSQL adapter."""
        self.adapter = adapter or PostgreSQLAdapter()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the shared state system."""
        if self._initialized:
            return
        
        try:
            await self.adapter.initialize()
            self._initialized = True
            logger.info("SharedState initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SharedState: {e}")
            raise
    
    async def close(self):
        """Close shared state and cleanup resources."""
        if self.adapter:
            await self.adapter.close()
        self._initialized = False
        logger.info("SharedState closed")
    
    # Agent Management
    
    async def register_agent(self, agent_id: str, metadata: Dict[str, Any] = None):
        """Register a new agent."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.adapter.register_agent(
                agent_id=agent_id,
                state='initializing',
                metadata=metadata or {}
            )
            
            # Log registration event
            await self.log_system_event(
                'agent_registered',
                {'agent_id': agent_id, 'metadata': metadata},
                agent_id=agent_id
            )
            
            logger.info(f"Agent {agent_id} registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            raise
    
    async def update_agent_state(self, agent_id: str, state: str, metadata: Dict[str, Any] = None):
        """Update agent state."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.adapter.update_agent_state(
                agent_id=agent_id,
                state=state,
                metadata=metadata
            )
            
            # Log state change
            await self.log_system_event(
                'agent_state_changed',
                {'agent_id': agent_id, 'new_state': state, 'metadata': metadata},
                agent_id=agent_id
            )
            
            logger.debug(f"Agent {agent_id} state updated to {state}")
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} state: {e}")
            raise
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get specific agent status."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.adapter.get_agent_status(agent_id)
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id} status: {e}")
            return None
    
    async def get_registered_agents(self) -> List[Dict[str, Any]]:
        """Get all registered agents."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.adapter.get_agent_status()
        except Exception as e:
            logger.error(f"Failed to get registered agents: {e}")
            return []
    
    async def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get all active (running) agents."""
        agents = await self.get_registered_agents()
        return [agent for agent in agents if agent.get('state') == 'running']
    
    # Heartbeat Management
    
    async def update_agent_heartbeat(self, agent_id: str, timestamp: datetime, heartbeat_data: Dict[str, Any]):
        """Update agent heartbeat."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.adapter.log_heartbeat(
                agent_id=agent_id,
                timestamp=timestamp,
                heartbeat_data=heartbeat_data
            )
            
            logger.debug(f"Heartbeat logged for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to log heartbeat for agent {agent_id}: {e}")
            raise
    
    async def get_recent_heartbeats(self, agent_id: str = None, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get recent heartbeats."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.adapter.get_recent_heartbeats(agent_id, minutes)
        except Exception as e:
            logger.error(f"Failed to get recent heartbeats: {e}")
            return []
    
    async def check_agent_health(self, agent_id: str) -> bool:
        """Check if agent is healthy based on recent heartbeats."""
        heartbeats = await self.get_recent_heartbeats(agent_id, minutes=5)
        
        if not heartbeats:
            return False
        
        # Check if we have a recent heartbeat (within last 2 minutes)
        latest_heartbeat = heartbeats[0]
        heartbeat_time = latest_heartbeat['timestamp']
        
        if isinstance(heartbeat_time, str):
            heartbeat_time = datetime.fromisoformat(heartbeat_time.replace('Z', '+00:00'))
        
        time_diff = (datetime.now(timezone.utc) - heartbeat_time).total_seconds()
        
        return time_diff < 120  # 2 minutes
    
    # Performance Metrics
    
    async def log_performance_metric(self, agent_id: str, metric_name: str, value: float, unit: str = None, metadata: Dict[str, Any] = None):
        """Log a performance metric."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.adapter.log_performance_metric(
                agent_id=agent_id,
                metric_name=metric_name,
                value=value,
                unit=unit,
                metadata=metadata
            )
            
            logger.debug(f"Performance metric logged: {agent_id}.{metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")
            raise
    
    async def get_performance_metrics(self, agent_id: str = None, hours: int = 1) -> List[Dict[str, Any]]:
        """Get performance metrics."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.adapter.get_performance_metrics(agent_id, hours)
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return []
    
    async def get_performance_summary(self, agent_id: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics summary."""
        metrics = await self.get_performance_metrics(agent_id, hours)
        
        if not metrics:
            return {}
        
        summary = {}
        for metric in metrics:
            metric_name = metric['metric_name']
            value = float(metric['value'])
            
            if metric_name not in summary:
                summary[metric_name] = {
                    'count': 0,
                    'sum': 0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'latest': None,
                    'unit': metric.get('unit')
                }
            
            summary[metric_name]['count'] += 1
            summary[metric_name]['sum'] += value
            summary[metric_name]['min'] = min(summary[metric_name]['min'], value)
            summary[metric_name]['max'] = max(summary[metric_name]['max'], value)
            summary[metric_name]['latest'] = value
        
        # Calculate averages
        for metric_name in summary:
            if summary[metric_name]['count'] > 0:
                summary[metric_name]['avg'] = summary[metric_name]['sum'] / summary[metric_name]['count']
        
        return summary
    
    # System Events
    
    async def log_system_event(self, event_type: str, event_data: Dict[str, Any], agent_id: str = None, severity: str = 'INFO'):
        """Log a system event."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await self.adapter.log_system_event(
                event_type=event_type,
                event_data=event_data,
                agent_id=agent_id,
                severity=severity
            )
            
            logger.debug(f"System event logged: {event_type} ({severity})")
            
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
            raise
    
    async def get_system_events(self, event_type: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system events."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.adapter.get_system_events(event_type, hours)
        except Exception as e:
            logger.error(f"Failed to get system events: {e}")
            return []
    
    async def get_error_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get error events."""
        return await self.get_system_events(hours=hours)
    
    # AI Help System Integration
    
    async def create_help_request(self, user_id: str, content: str, context: Dict[str, Any] = None) -> str:
        """Create a help request."""
        if not self._initialized:
            await self.initialize()
        
        request_id = str(uuid.uuid4())
        
        try:
            await self.adapter.create_help_request(
                request_id=request_id,
                user_id=user_id,
                content=content,
                context=context or {}
            )
            
            # Log help request creation
            await self.log_system_event(
                'help_request_created',
                {
                    'request_id': request_id,
                    'user_id': user_id,
                    'content_length': len(content)
                }
            )
            
            logger.info(f"Help request created: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Failed to create help request: {e}")
            raise
    
    async def create_help_response(self, request_id: str, content: str, confidence_score: float = None, sources: List[str] = None, agent_id: str = None) -> str:
        """Create a help response."""
        if not self._initialized:
            await self.initialize()
        
        response_id = str(uuid.uuid4())
        
        try:
            await self.adapter.create_help_response(
                request_id=request_id,
                response_id=response_id,
                content=content,
                confidence_score=confidence_score,
                sources=sources,
                agent_id=agent_id
            )
            
            # Log help response creation
            await self.log_system_event(
                'help_response_created',
                {
                    'request_id': request_id,
                    'response_id': response_id,
                    'agent_id': agent_id,
                    'confidence_score': confidence_score
                },
                agent_id=agent_id
            )
            
            logger.info(f"Help response created: {response_id}")
            return response_id
            
        except Exception as e:
            logger.error(f"Failed to create help response: {e}")
            raise
    
    async def get_help_requests(self, status: str = None, user_id: str = None) -> List[Dict[str, Any]]:
        """Get help requests."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.adapter.get_help_requests(status, user_id)
        except Exception as e:
            logger.error(f"Failed to get help requests: {e}")
            return []
    
    async def get_help_responses(self, request_id: str) -> List[Dict[str, Any]]:
        """Get help responses for a request."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.adapter.get_help_responses(request_id)
        except Exception as e:
            logger.error(f"Failed to get help responses: {e}")
            return []
    
    # System State Management
    
    async def set_system_state(self, key: str, value: Any, updated_by: str = None):
        """Set a system state value."""
        if not self._initialized:
            await self.initialize()
        
        query = """
        INSERT INTO system_state (key, value, updated_by)
        VALUES ($1, $2, $3)
        ON CONFLICT (key)
        DO UPDATE SET value = EXCLUDED.value, updated_by = EXCLUDED.updated_by, updated_at = NOW()
        """
        
        try:
            await self.adapter.execute_query(
                query,
                key,
                json.dumps(value),
                updated_by
            )
            
            logger.debug(f"System state updated: {key}")
            
        except Exception as e:
            logger.error(f"Failed to set system state {key}: {e}")
            raise
    
    async def get_system_state(self, key: str) -> Any:
        """Get a system state value."""
        if not self._initialized:
            await self.initialize()
        
        query = "SELECT value FROM system_state WHERE key = $1"
        
        try:
            result = await self.adapter.execute_query(query, key, fetch_mode='val')
            return json.loads(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get system state {key}: {e}")
            return None
    
    async def get_all_system_state(self) -> Dict[str, Any]:
        """Get all system state values."""
        if not self._initialized:
            await self.initialize()
        
        query = "SELECT key, value FROM system_state"
        
        try:
            results = await self.adapter.execute_query(query, fetch_mode='all')
            return {row['key']: json.loads(row['value']) for row in results}
        except Exception as e:
            logger.error(f"Failed to get all system state: {e}")
            return {}
    
    # System Health and Statistics
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            agents = await self.get_registered_agents()
            active_agents = [a for a in agents if a.get('state') == 'running']
            
            health_status = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_agents': len(agents),
                'active_agents': len(active_agents),
                'healthy_agents': 0,
                'agent_details': {}
            }
            
            # Check individual agent health
            for agent in active_agents:
                agent_id = agent['agent_id']
                is_healthy = await self.check_agent_health(agent_id)
                health_status['agent_details'][agent_id] = {
                    'healthy': is_healthy,
                    'state': agent.get('state'),
                    'last_updated': agent.get('updated_at')
                }
                
                if is_healthy:
                    health_status['healthy_agents'] += 1
            
            # Calculate health percentage
            if active_agents:
                health_status['health_percentage'] = (
                    health_status['healthy_agents'] / len(active_agents)
                ) * 100
            else:
                health_status['health_percentage'] = 0
            
            # Get recent error count
            recent_errors = await self.get_system_events(hours=1)
            error_events = [e for e in recent_errors if e.get('severity') == 'ERROR']
            health_status['recent_errors'] = len(error_events)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {'error': str(e), 'healthy': False}
    
    async def get_system_context(self) -> Dict[str, Any]:
        """Get current system context for AI help."""
        try:
            context = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_health': await self.get_system_health(),
                'recent_performance': await self.get_performance_summary(hours=1),
                'recent_events': await self.get_system_events(hours=1),
                'database_stats': await self.adapter.get_database_stats()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get system context: {e}")
            return {'error': str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        try:
            return await self.adapter.get_database_stats()
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    # Health Check
    
    async def health_check(self) -> bool:
        """Perform system health check."""
        try:
            if not self._initialized:
                await self.initialize()
            
            return await self.adapter.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def __repr__(self):
        """String representation."""
        status = "initialized" if self._initialized else "not initialized"
        return f"<SharedState({status})>" 