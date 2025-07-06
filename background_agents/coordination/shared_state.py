"""
PostgreSQL-Based Shared State Management

Enterprise shared state system with PostgreSQL integration,
high-performance operations, and comprehensive business intelligence.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import json

from .postgresql_adapter import PostgreSQLAdapter, ConnectionConfig


class SharedState:
    """
    Enterprise Shared State with PostgreSQL Integration
    
    Provides high-performance, scalable state management for the agent system including:
    - Agent registration and lifecycle management
    - Real-time heartbeat tracking and health monitoring
    - Performance metrics collection and analysis
    - System event logging and analytics
    - Business intelligence data aggregation
    """
    
    def __init__(self, postgresql_adapter: PostgreSQLAdapter = None):
        self.postgresql_adapter = postgresql_adapter
        self.is_initialized = False
        
        # Performance optimization
        self._connection_pool_ready = False
        self._initialization_lock = asyncio.Lock()
        
        # Caching for performance
        self._agent_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = None
        
        # Setup logging
        self.logger = logging.getLogger("shared_state")
        
    async def initialize(self) -> None:
        """Initialize shared state with PostgreSQL backend"""
        async with self._initialization_lock:
            if self.is_initialized:
                return
                
            try:
                self.logger.info("Initializing SharedState with PostgreSQL backend")
                
                # Initialize PostgreSQL adapter if not provided
                if not self.postgresql_adapter:
                    self.postgresql_adapter = PostgreSQLAdapter()
                    await self.postgresql_adapter.initialize()
                    
                # Verify PostgreSQL connection
                health_check = await self.postgresql_adapter.health_check()
                if health_check['status'] != 'healthy':
                    raise RuntimeError(f"PostgreSQL not healthy: {health_check}")
                    
                self._connection_pool_ready = True
                self.is_initialized = True
                
                self.logger.info("SharedState initialization completed successfully")
                
            except Exception as e:
                self.logger.error(f"SharedState initialization failed: {e}")
                raise
                
    # Agent Management Operations
    
    async def register_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> None:
        """
        Register agent with comprehensive metadata
        
        Args:
            agent_id: Unique identifier for the agent
            agent_data: Agent registration data and metadata
        """
        try:
            await self._ensure_initialized()
            
            # Enhance agent data with registration timestamp
            enhanced_data = {
                **agent_data,
                'registration_timestamp': datetime.now(timezone.utc).isoformat(),
                'last_update': datetime.now(timezone.utc).isoformat()
            }
            
            # Register with PostgreSQL
            await self.postgresql_adapter.register_agent(agent_id, enhanced_data)
            
            # Update cache
            self._update_agent_cache(agent_id, enhanced_data)
            
            # Log registration event
            await self.log_system_event(
                'agent_registration',
                {
                    'agent_id': agent_id,
                    'agent_type': agent_data.get('agent_type', 'Unknown'),
                    'capabilities': agent_data.get('capabilities', [])
                },
                agent_id=agent_id,
                severity='INFO'
            )
            
            self.logger.info(f"Agent {agent_id} registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_id}: {e}")
            raise
            
    async def update_agent_state(self, agent_id: str, state: str, metadata: Dict = None) -> None:
        """
        Update agent state with optional metadata
        
        Args:
            agent_id: Agent identifier
            state: New agent state
            metadata: Optional additional metadata
        """
        try:
            await self._ensure_initialized()
            
            # Update in PostgreSQL
            update_metadata = metadata or {}
            update_metadata['state_change_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            await self.postgresql_adapter.update_agent_state(agent_id, state, update_metadata)
            
            # Update cache
            if agent_id in self._agent_cache:
                self._agent_cache[agent_id]['state'] = state
                self._agent_cache[agent_id]['updated_at'] = datetime.now(timezone.utc)
                
            # Log state change
            await self.log_system_event(
                'agent_state_change',
                {
                    'agent_id': agent_id,
                    'new_state': state,
                    'previous_state': metadata.get('previous_state') if metadata else None,
                    'metadata': update_metadata
                },
                agent_id=agent_id,
                severity='INFO'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update agent state for {agent_id}: {e}")
            raise
            
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive agent status and metadata
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary with agent status and metadata, or None if not found
        """
        try:
            await self._ensure_initialized()
            
            # Check cache first
            if agent_id in self._agent_cache and self._is_cache_valid():
                return self._agent_cache[agent_id]
                
            # Get from PostgreSQL
            agent_data = await self.postgresql_adapter.get_agent_status(agent_id)
            
            # Update cache
            if agent_data:
                self._update_agent_cache(agent_id, agent_data)
                
            return agent_data
            
        except Exception as e:
            self.logger.error(f"Failed to get agent status for {agent_id}: {e}")
            raise
            
    async def get_registered_agents(self, states: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get all registered agents with optional state filtering
        
        Args:
            states: Optional list of states to filter by
            
        Returns:
            List of agent data dictionaries
        """
        try:
            await self._ensure_initialized()
            
            # Get from PostgreSQL (cache not suitable for bulk operations)
            agents = await self.postgresql_adapter.get_registered_agents(states)
            
            # Update cache with fresh data
            for agent in agents:
                agent_id = agent.get('agent_id')
                if agent_id:
                    self._update_agent_cache(agent_id, agent)
                    
            return agents
            
        except Exception as e:
            self.logger.error(f"Failed to get registered agents: {e}")
            raise
            
    # Heartbeat Operations
    
    async def update_agent_heartbeat(self, agent_id: str, timestamp: datetime, 
                                   heartbeat_data: Dict[str, Any]) -> None:
        """
        Update agent heartbeat with comprehensive metrics
        
        Args:
            agent_id: Agent identifier
            timestamp: Heartbeat timestamp
            heartbeat_data: Comprehensive heartbeat data
        """
        try:
            await self._ensure_initialized()
            
            # Enhance heartbeat data
            enhanced_heartbeat = {
                **heartbeat_data,
                'heartbeat_sequence': await self._get_next_heartbeat_sequence(agent_id),
                'system_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store in PostgreSQL
            await self.postgresql_adapter.update_agent_heartbeat(
                agent_id, timestamp, enhanced_heartbeat
            )
            
            # Log performance metrics from heartbeat
            await self._extract_and_log_heartbeat_metrics(agent_id, enhanced_heartbeat)
            
        except Exception as e:
            self.logger.error(f"Failed to update heartbeat for {agent_id}: {e}")
            raise
            
    async def get_recent_heartbeats(self, agent_id: str, minutes: int = 10) -> List[datetime]:
        """
        Get recent heartbeat timestamps for an agent
        
        Args:
            agent_id: Agent identifier
            minutes: Number of minutes to look back
            
        Returns:
            List of heartbeat timestamps
        """
        try:
            await self._ensure_initialized()
            
            heartbeats = await self.postgresql_adapter.get_recent_heartbeats(agent_id, minutes)
            return heartbeats
            
        except Exception as e:
            self.logger.error(f"Failed to get recent heartbeats for {agent_id}: {e}")
            raise
            
    async def get_agent_health_data(self, agent_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get comprehensive agent health data over time
        
        Args:
            agent_id: Agent identifier
            hours: Number of hours to look back
            
        Returns:
            List of health data points
        """
        try:
            await self._ensure_initialized()
            
            health_data = await self.postgresql_adapter.get_agent_health_data(agent_id, hours)
            return health_data
            
        except Exception as e:
            self.logger.error(f"Failed to get health data for {agent_id}: {e}")
            raise
            
    # Performance Metrics Operations
    
    async def log_performance_metric(self, metric_name: str, value: float, unit: str, 
                                   agent_id: str = None) -> None:
        """
        Log performance metric to database
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            agent_id: Optional agent identifier
        """
        try:
            await self._ensure_initialized()
            
            await self.postgresql_adapter.log_performance_metric(
                metric_name, value, unit, agent_id
            )
            
            # Log business metrics for key performance indicators
            await self._log_business_metric_if_applicable(metric_name, value, agent_id)
            
        except Exception as e:
            self.logger.error(f"Failed to log performance metric {metric_name}: {e}")
            raise
            
    async def get_performance_metrics(self, agent_id: str = None, metric_name: str = None, 
                                    hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get performance metrics with optional filtering
        
        Args:
            agent_id: Optional agent identifier filter
            metric_name: Optional metric name filter
            hours: Number of hours to look back
            
        Returns:
            List of performance metric data
        """
        try:
            await self._ensure_initialized()
            
            metrics = await self.postgresql_adapter.get_performance_metrics(
                agent_id, metric_name, hours
            )
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            raise
            
    # System Events Operations
    
    async def log_system_event(self, event_type: str, event_data: Dict[str, Any], 
                             agent_id: str = None, severity: str = 'INFO') -> None:
        """
        Log system event with comprehensive context
        
        Args:
            event_type: Type of system event
            event_data: Event data and context
            agent_id: Optional agent identifier
            severity: Event severity level
        """
        try:
            await self._ensure_initialized()
            
            # Enhance event data with system context
            enhanced_event_data = {
                **event_data,
                'system_timestamp': datetime.now(timezone.utc).isoformat(),
                'event_source': 'shared_state'
            }
            
            await self.postgresql_adapter.log_system_event(
                event_type, enhanced_event_data, agent_id, severity
            )
            
            # Trigger alerts for critical events
            if severity in ['ERROR', 'CRITICAL']:
                await self._handle_critical_event(event_type, enhanced_event_data, agent_id)
                
        except Exception as e:
            self.logger.error(f"Failed to log system event {event_type}: {e}")
            # Don't re-raise to avoid event logging loops
            
    async def get_system_events(self, event_type: str = None, agent_id: str = None, 
                              severity: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get system events with optional filtering
        
        Args:
            event_type: Optional event type filter
            agent_id: Optional agent identifier filter
            severity: Optional severity filter
            hours: Number of hours to look back
            
        Returns:
            List of system event data
        """
        try:
            await self._ensure_initialized()
            
            events = await self.postgresql_adapter.get_system_events(
                event_type, agent_id, severity, hours
            )
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to get system events: {e}")
            raise
            
    # Business Intelligence Operations
    
    async def log_business_metric(self, category: str, metric_name: str, value: float, 
                                metadata: Dict[str, Any] = None) -> None:
        """
        Log business intelligence metric
        
        Args:
            category: Business metric category
            metric_name: Name of the business metric
            value: Metric value
            metadata: Optional metadata
        """
        try:
            await self._ensure_initialized()
            
            await self.postgresql_adapter.log_business_metric(
                category, metric_name, value, metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log business metric {metric_name}: {e}")
            raise
            
    async def get_business_metrics(self, category: str = None, metric_name: str = None, 
                                 hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get business metrics with optional filtering
        
        Args:
            category: Optional category filter
            metric_name: Optional metric name filter
            hours: Number of hours to look back
            
        Returns:
            List of business metric data
        """
        try:
            await self._ensure_initialized()
            
            metrics = await self.postgresql_adapter.get_business_metrics(
                category, metric_name, hours
            )
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get business metrics: {e}")
            raise
            
    # Health and Monitoring Operations
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status
        
        Returns:
            Dictionary with system health information
        """
        try:
            await self._ensure_initialized()
            
            # Get database health
            db_health = await self.postgresql_adapter.health_check()
            
            # Get agent summary
            agents = await self.get_registered_agents()
            active_agents = len([a for a in agents if a.get('state') == 'active'])
            
            # Get recent system activity
            recent_events = await self.get_system_events(hours=1)
            error_events = [e for e in recent_events if e.get('severity') in ['ERROR', 'CRITICAL']]
            
            # Calculate overall health score
            health_score = await self._calculate_system_health_score(
                len(agents), active_agents, len(error_events), db_health
            )
            
            return {
                'overall_health_score': health_score,
                'database_health': db_health,
                'total_agents': len(agents),
                'active_agents': active_agents,
                'recent_errors': len(error_events),
                'system_status': 'healthy' if health_score > 80 else 'degraded',
                'last_updated': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system health: {e}")
            return {
                'overall_health_score': 0,
                'system_status': 'error',
                'error': str(e),
                'last_updated': datetime.now(timezone.utc)
            }
            
    async def get_system_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive system performance summary
        
        Returns:
            Dictionary with performance summary
        """
        try:
            await self._ensure_initialized()
            
            # Get performance metrics
            metrics = await self.get_performance_metrics(hours=24)
            
            # Aggregate metrics by type
            metric_summary = {}
            for metric in metrics:
                metric_name = metric['metric_name']
                if metric_name not in metric_summary:
                    metric_summary[metric_name] = {
                        'values': [],
                        'unit': metric.get('metric_unit', ''),
                        'count': 0
                    }
                metric_summary[metric_name]['values'].append(metric['metric_value'])
                metric_summary[metric_name]['count'] += 1
                
            # Calculate summary statistics
            performance_summary = {}
            for metric_name, data in metric_summary.items():
                values = data['values']
                performance_summary[metric_name] = {
                    'average': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'count': data['count'],
                    'unit': data['unit']
                }
                
            return {
                'summary_timestamp': datetime.now(timezone.utc),
                'metrics_analyzed': len(metrics),
                'performance_metrics': performance_summary,
                'system_efficiency': await self._calculate_system_efficiency(performance_summary)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}
            
    # Utility and Maintenance Operations
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """
        Clean up old data to maintain performance
        
        Args:
            days: Number of days of data to retain
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            await self._ensure_initialized()
            
            cleanup_stats = await self.postgresql_adapter.cleanup_old_data(days)
            
            # Log cleanup activity
            await self.log_system_event(
                'data_cleanup',
                {
                    'retention_days': days,
                    'cleanup_stats': cleanup_stats
                },
                severity='INFO'
            )
            
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            raise
            
    async def reconnect(self) -> None:
        """Reconnect to database (useful for recovery)"""
        try:
            self.logger.info("Reconnecting SharedState to PostgreSQL...")
            
            if self.postgresql_adapter:
                await self.postgresql_adapter.reconnect()
                
            # Clear cache
            self._agent_cache.clear()
            self._last_cache_update = None
            
            self.logger.info("SharedState reconnection successful")
            
        except Exception as e:
            self.logger.error(f"SharedState reconnection failed: {e}")
            raise
            
    async def close(self) -> None:
        """Close shared state and database connections"""
        try:
            self.logger.info("Closing SharedState...")
            
            if self.postgresql_adapter:
                await self.postgresql_adapter.close()
                
            self.is_initialized = False
            self._connection_pool_ready = False
            
            self.logger.info("SharedState closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing SharedState: {e}")
            raise
            
    # Private Helper Methods
    
    async def _ensure_initialized(self) -> None:
        """Ensure shared state is initialized"""
        if not self.is_initialized:
            await self.initialize()
            
    def _update_agent_cache(self, agent_id: str, agent_data: Dict[str, Any]) -> None:
        """Update agent cache with fresh data"""
        self._agent_cache[agent_id] = agent_data
        self._last_cache_update = datetime.now(timezone.utc)
        
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self._last_cache_update:
            return False
            
        cache_age = (datetime.now(timezone.utc) - self._last_cache_update).total_seconds()
        return cache_age < self._cache_ttl
        
    async def _get_next_heartbeat_sequence(self, agent_id: str) -> int:
        """Get next heartbeat sequence number for agent"""
        # Simple implementation - could be enhanced with proper sequence tracking
        return int(datetime.now(timezone.utc).timestamp())
        
    async def _extract_and_log_heartbeat_metrics(self, agent_id: str, 
                                               heartbeat_data: Dict[str, Any]) -> None:
        """Extract and log performance metrics from heartbeat data"""
        try:
            # Extract common metrics
            metrics_to_log = [
                ('heartbeat_health_score', heartbeat_data.get('health_score'), 'score'),
                ('heartbeat_cpu_usage', heartbeat_data.get('cpu_usage_percent'), 'percent'),
                ('heartbeat_memory_usage', heartbeat_data.get('memory_usage_percent'), 'percent'),
                ('heartbeat_work_items', heartbeat_data.get('work_items_processed'), 'count'),
                ('heartbeat_error_count', heartbeat_data.get('error_count'), 'count')
            ]
            
            for metric_name, value, unit in metrics_to_log:
                if value is not None:
                    await self.log_performance_metric(metric_name, value, unit, agent_id)
                    
        except Exception as e:
            self.logger.error(f"Failed to extract heartbeat metrics: {e}")
            
    async def _log_business_metric_if_applicable(self, metric_name: str, value: float, 
                                               agent_id: str = None) -> None:
        """Log business metric if the performance metric has business relevance"""
        try:
            business_mappings = {
                'business_value_generated': ('revenue', 'business_value_generated'),
                'cost_efficiency': ('cost_optimization', 'efficiency_score'),
                'user_satisfaction': ('customer_experience', 'satisfaction_score'),
                'error_rate': ('quality', 'error_rate')
            }
            
            if metric_name in business_mappings:
                category, business_metric_name = business_mappings[metric_name]
                await self.log_business_metric(
                    category, business_metric_name, value,
                    {'source_agent': agent_id, 'source_metric': metric_name}
                )
                
        except Exception as e:
            self.logger.error(f"Failed to log business metric: {e}")
            
    async def _handle_critical_event(self, event_type: str, event_data: Dict[str, Any], 
                                   agent_id: str = None) -> None:
        """Handle critical system events"""
        try:
            # Log critical event for business intelligence
            await self.log_business_metric(
                'system_reliability',
                'critical_event',
                1.0,
                {
                    'event_type': event_type,
                    'agent_id': agent_id,
                    'severity': 'CRITICAL'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to handle critical event: {e}")
            
    async def _calculate_system_health_score(self, total_agents: int, active_agents: int, 
                                           error_count: int, db_health: Dict) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            # Agent health component (40%)
            agent_ratio = active_agents / max(total_agents, 1)
            agent_score = agent_ratio * 40
            
            # Database health component (30%)
            db_score = 30 if db_health.get('status') == 'healthy' else 0
            
            # Error rate component (20%)
            error_score = max(20 - error_count * 2, 0)
            
            # System responsiveness component (10%)
            db_response_time = db_health.get('response_time_seconds', 0)
            response_score = max(10 - db_response_time * 2, 0)
            
            total_score = agent_score + db_score + error_score + response_score
            return min(max(total_score, 0), 100)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate system health score: {e}")
            return 50.0  # Default to medium health
            
    async def _calculate_system_efficiency(self, performance_summary: Dict) -> float:
        """Calculate overall system efficiency score"""
        try:
            efficiency_factors = []
            
            # Processing time efficiency
            if 'processing_time' in performance_summary:
                avg_processing = performance_summary['processing_time']['average']
                processing_efficiency = max(100 - avg_processing * 10, 0)
                efficiency_factors.append(processing_efficiency)
                
            # CPU efficiency
            if 'cpu_usage' in performance_summary:
                avg_cpu = performance_summary['cpu_usage']['average']
                cpu_efficiency = max(100 - avg_cpu, 0)
                efficiency_factors.append(cpu_efficiency)
                
            # Memory efficiency
            if 'memory_usage' in performance_summary:
                avg_memory = performance_summary['memory_usage']['average']
                memory_efficiency = max(100 - avg_memory, 0)
                efficiency_factors.append(memory_efficiency)
                
            # Error rate efficiency
            if 'error_count' in performance_summary:
                avg_errors = performance_summary['error_count']['average']
                error_efficiency = max(100 - avg_errors * 10, 0)
                efficiency_factors.append(error_efficiency)
                
            if efficiency_factors:
                return sum(efficiency_factors) / len(efficiency_factors)
            else:
                return 85.0  # Default good efficiency
                
        except Exception as e:
            self.logger.error(f"Failed to calculate system efficiency: {e}")
            return 70.0  # Default medium efficiency 