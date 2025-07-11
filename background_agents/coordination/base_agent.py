"""
PostgreSQL-Based Base Agent

Enterprise-grade base agent class with PostgreSQL integration,
comprehensive health monitoring, automated recovery, and business intelligence.
"""

import asyncio
import logging
import time
import psutil
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    work_items_processed: int = 0
    processing_time_total: float = 0.0
    error_count: int = 0
    recovery_attempts: int = 0
    business_value_generated: float = 0.0
    uptime_seconds: float = 0.0


class BaseAgent(ABC):
    """
    Enterprise Base Agent with PostgreSQL Integration
    
    Provides comprehensive foundation for all agents including:
    - PostgreSQL-backed state management and coordination
    - Real-time health monitoring and business impact tracking
    - Automated error recovery and self-healing capabilities
    - Performance analytics and optimization recommendations
    - Business intelligence integration and executive reporting
    """
    
    def __init__(self, agent_id: str, shared_state=None, **kwargs):
        self.agent_id = agent_id
        self.shared_state = shared_state
        self.start_time = None
        self.last_heartbeat = None
        
        # Agent configuration
        self.work_interval = kwargs.get('work_interval', 60)  # seconds
        self.heartbeat_interval = kwargs.get('heartbeat_interval', 30)  # seconds
        self.health_monitoring_enabled = kwargs.get('health_monitoring_enabled', True)
        self.auto_recovery_enabled = kwargs.get('auto_recovery_enabled', True)
        self.business_metrics_enabled = kwargs.get('business_metrics_enabled', True)
        
        # Performance tracking
        self.metrics = AgentMetrics()
        
        # Business metrics
        self.business_metrics = {
            'cost_efficiency': 100.0,
            'user_satisfaction_impact': 100.0,
            'revenue_impact': 0.0,
            'operational_efficiency': 100.0
        }
        
        # Health tracking
        self.health_score = 100.0
        self.error_count = 0
        self.recovery_attempts = 0
        
        # State tracking
        self.current_state = 'initialized'
        self.is_running = False
        self.shutdown_requested = False
        
        # Setup logging
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Performance optimization
        self._last_performance_log = time.time()
        self._performance_log_interval = 300  # 5 minutes
        
    async def startup(self) -> None:
        """
        Enterprise agent startup with comprehensive initialization
        
        This method handles:
        - PostgreSQL registration and state management
        - Health monitoring setup
        - Business intelligence initialization
        - Error recovery preparation
        """
        try:
            self.start_time = datetime.now(timezone.utc)
            self.logger.info(f"Starting enterprise agent: {self.agent_id}")
            
            # Validate shared state connection
            if not self.shared_state:
                raise RuntimeError("SharedState is required for agent operation")
                
            # Register agent with PostgreSQL backend
            await self.register_agent()
            
            # Initialize agent-specific components
            await self.initialize()
            
            # Setup health monitoring
            if self.health_monitoring_enabled:
                await self.setup_health_monitoring()
                
            # Setup business intelligence
            if self.business_metrics_enabled:
                await self.setup_business_intelligence()
                
            # Update state to active
            await self.shared_state.update_agent_state(self.agent_id, 'active')
            self.current_state = 'active'
            self.is_running = True
            
            self.logger.info(f"Agent {self.agent_id} startup completed successfully")
            
            # Start main execution loop
            await self.main_loop()
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id} startup failed: {e}")
            await self.handle_startup_error(e)
            raise
            
    async def register_agent(self) -> None:
        """Register agent with PostgreSQL-backed shared state"""
        try:
            registration_data = {
                'agent_type': self.__class__.__name__,
                'agent_name': getattr(self, 'agent_name', self.agent_id),
                'startup_time': self.start_time.isoformat(),
                'capabilities': await self.get_capabilities(),
                'configuration': await self.get_configuration(),
                'health_monitoring_enabled': self.health_monitoring_enabled,
                'business_metrics_enabled': self.business_metrics_enabled,
                'auto_recovery_enabled': self.auto_recovery_enabled
            }
            
            await self.shared_state.register_agent(self.agent_id, registration_data)
            await self.shared_state.update_agent_state(self.agent_id, 'starting')
            self.current_state = 'starting'
            
            self.logger.info(f"Agent {self.agent_id} registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {self.agent_id}: {e}")
            raise
            
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize agent-specific components
        
        Subclasses must implement this method to setup:
        - Agent-specific configuration and resources
        - External API connections
        - Data processing pipelines
        - Business logic initialization
        """
        pass
        
    async def main_loop(self) -> None:
        """
        Main execution loop with enterprise-grade monitoring
        
        Handles:
        - Regular heartbeat updates with comprehensive metrics
        - Work execution with performance tracking
        - Error handling and automated recovery
        - Business metrics calculation and reporting
        """
        self.logger.info(f"Agent {self.agent_id} entering main execution loop")
        self.logger.info(f"Agent {self.agent_id} initial state - is_running: {self.is_running}, shutdown_requested: {self.shutdown_requested}")
        
        iteration_count = 0
        
        while self.is_running and not self.shutdown_requested:
            try:
                iteration_count += 1
                self.logger.debug(f"Agent {self.agent_id} main loop iteration {iteration_count} starting")
                
                loop_start_time = time.time()
                
                # Update comprehensive heartbeat
                self.logger.debug(f"Agent {self.agent_id} updating heartbeat...")
                await self.update_comprehensive_heartbeat()
                
                # Perform agent work
                self.logger.debug(f"Agent {self.agent_id} executing work cycle...")
                work_result = await self.execute_work_cycle()
                self.logger.debug(f"Agent {self.agent_id} work cycle completed: {work_result.get('success', 'unknown')}")
                
                # Update performance metrics
                self.logger.debug(f"Agent {self.agent_id} updating performance metrics...")
                await self.update_performance_metrics(work_result, loop_start_time)
                
                # Update business metrics
                if self.business_metrics_enabled:
                    self.logger.debug(f"Agent {self.agent_id} updating business metrics...")
                    await self.update_business_metrics(work_result)
                    
                # Check for optimization opportunities
                self.logger.debug(f"Agent {self.agent_id} checking optimization opportunities...")
                await self.check_optimization_opportunities()
                
                # Log performance periodically
                await self.log_periodic_performance()
                
                # Wait for next cycle
                self.logger.debug(f"Agent {self.agent_id} iteration {iteration_count} completed, sleeping for {self.work_interval}s")
                await asyncio.sleep(self.work_interval)
                
                # Log state after sleep
                self.logger.debug(f"Agent {self.agent_id} woke up - is_running: {self.is_running}, shutdown_requested: {self.shutdown_requested}")
                
            except asyncio.CancelledError:
                self.logger.warning(f"Agent {self.agent_id} main loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Agent {self.agent_id} main loop error in iteration {iteration_count}: {e}")
                await self.handle_execution_error(e)
                
        self.logger.warning(f"Agent {self.agent_id} main loop exiting after {iteration_count} iterations")
        self.logger.warning(f"Agent {self.agent_id} exit conditions - is_running: {self.is_running}, shutdown_requested: {self.shutdown_requested}")
        
        # Mark agent as inactive when exiting main loop
        try:
            await self.shared_state.update_agent_state(self.agent_id, 'inactive')
            self.current_state = 'inactive'
        except Exception as e:
            self.logger.error(f"Failed to update agent state to inactive: {e}")
            
    async def update_comprehensive_heartbeat(self) -> None:
        """Update heartbeat with comprehensive enterprise metrics"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Calculate uptime
            uptime_seconds = (current_time - self.start_time).total_seconds() if self.start_time else 0
            
            # Get system resource usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            heartbeat_data = {
                'agent_name': getattr(self, 'agent_name', self.agent_id),
                'state': self.current_state,
                'timestamp': current_time.isoformat(),
                
                # Performance metrics
                'work_items_processed': self.metrics.work_items_processed,
                'average_processing_time': self.calculate_average_processing_time(),
                'error_rate': self.calculate_error_rate(),
                'uptime_seconds': uptime_seconds,
                
                # Resource metrics
                'cpu_usage_percent': psutil.cpu_percent(interval=None),
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'memory_usage_percent': process.memory_percent(),
                
                # Business metrics
                'cost_efficiency': self.business_metrics['cost_efficiency'],
                'user_satisfaction_impact': self.business_metrics['user_satisfaction_impact'],
                'revenue_impact': self.business_metrics['revenue_impact'],
                'operational_efficiency': self.business_metrics['operational_efficiency'],
                
                # Health indicators
                'health_score': await self.calculate_health_score(),
                'error_count': self.error_count,
                'recovery_attempts': self.recovery_attempts,
                
                # Enterprise features
                'business_value_generated': self.metrics.business_value_generated,
                'optimization_opportunities': await self.identify_optimization_opportunities(),
                'recommendations': await self.generate_recommendations()
            }
            
            await self.shared_state.update_agent_heartbeat(
                self.agent_id,
                current_time,
                heartbeat_data
            )
            
            self.last_heartbeat = current_time
            
        except Exception as e:
            self.logger.error(f"Failed to update heartbeat: {e}")
            # Don't raise - heartbeat failures shouldn't stop agent
            
    @abstractmethod
    async def execute_work_cycle(self) -> Dict[str, Any]:
        """
        Execute one cycle of agent work
        
        Subclasses must implement this method to define:
        - Core business logic and processing
        - Data analysis and transformation
        - External system integration
        - Decision making and actions
        
        Returns:
            Dictionary with work results including:
            - success: bool
            - items_processed: int
            - processing_time: float
            - business_value: float
            - error_details: Optional[str]
        """
        pass
        
    async def update_performance_metrics(self, work_result: Dict[str, Any], loop_start_time: float) -> None:
        """Update comprehensive performance metrics"""
        try:
            loop_time = time.time() - loop_start_time
            
            # Update core metrics
            if work_result.get('success', False):
                self.metrics.work_items_processed += work_result.get('items_processed', 0)
                self.metrics.processing_time_total += work_result.get('processing_time', 0)
                self.metrics.business_value_generated += work_result.get('business_value', 0)
            else:
                self.metrics.error_count += 1
                self.error_count += 1
                
            # Log individual metrics to PostgreSQL
            metrics_to_log = [
                ('work_items_processed', work_result.get('items_processed', 0), 'count'),
                ('processing_time', work_result.get('processing_time', 0), 'seconds'),
                ('loop_time', loop_time, 'seconds'),
                ('business_value_generated', work_result.get('business_value', 0), 'dollars'),
                ('cpu_usage', psutil.cpu_percent(), 'percent'),
                ('memory_usage', psutil.virtual_memory().percent, 'percent')
            ]
            
            for metric_name, value, unit in metrics_to_log:
                await self.log_performance_metric(metric_name, value, unit)
                
        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {e}")
            
    async def update_business_metrics(self, work_result: Dict[str, Any]) -> None:
        """Update business impact metrics"""
        try:
            # Calculate cost efficiency
            if work_result.get('success', False):
                processing_time = work_result.get('processing_time', 0)
                items_processed = work_result.get('items_processed', 0)
                
                if processing_time > 0 and items_processed > 0:
                    efficiency = min(items_processed / processing_time * 100, 100)
                    self.business_metrics['cost_efficiency'] = (
                        self.business_metrics['cost_efficiency'] * 0.9 + efficiency * 0.1
                    )
                    
            # Calculate operational efficiency
            if self.metrics.work_items_processed > 0:
                error_rate = self.error_count / max(self.metrics.work_items_processed, 1)
                self.business_metrics['operational_efficiency'] = max(100 - error_rate * 100, 0)
                
            # Update revenue impact
            self.business_metrics['revenue_impact'] += work_result.get('business_value', 0)
            
        except Exception as e:
            self.logger.error(f"Failed to update business metrics: {e}")
            
    async def calculate_health_score(self) -> float:
        """Calculate comprehensive agent health score (0-100)"""
        try:
            health_factors = {
                'uptime': await self.calculate_uptime_score(),
                'performance': await self.calculate_performance_score(),
                'error_rate': await self.calculate_error_rate_score(),
                'resource_efficiency': await self.calculate_resource_efficiency_score(),
                'business_impact': await self.calculate_business_impact_score()
            }
            
            # Weighted health score
            weights = {
                'uptime': 0.25,
                'performance': 0.25,
                'error_rate': 0.20,
                'resource_efficiency': 0.15,
                'business_impact': 0.15
            }
            
            health_score = sum(
                health_factors[factor] * weights[factor]
                for factor in health_factors
            )
            
            self.health_score = max(min(health_score, 100), 0)
            return self.health_score
            
        except Exception as e:
            self.logger.error(f"Failed to calculate health score: {e}")
            return 50.0  # Default to medium health on error
            
    async def calculate_uptime_score(self) -> float:
        """Calculate uptime score based on agent availability"""
        if not self.start_time:
            return 0.0
            
        uptime_seconds = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # Score based on continuous uptime (full score after 1 hour)
        return min(uptime_seconds / 3600 * 100, 100)
        
    async def calculate_performance_score(self) -> float:
        """Calculate performance score based on processing efficiency"""
        if self.metrics.work_items_processed == 0:
            return 100.0  # New agent gets full score
            
        avg_processing_time = self.calculate_average_processing_time()
        
        # Score based on processing speed (assuming 1 second is optimal)
        if avg_processing_time <= 1.0:
            return 100.0
        elif avg_processing_time <= 5.0:
            return 80.0
        elif avg_processing_time <= 10.0:
            return 60.0
        else:
            return 40.0
            
    async def calculate_error_rate_score(self) -> float:
        """Calculate error rate score"""
        if self.metrics.work_items_processed == 0:
            return 100.0
            
        error_rate = self.error_count / max(self.metrics.work_items_processed, 1)
        
        # Score based on error rate (0% errors = 100 points)
        return max(100 - error_rate * 100, 0)
        
    async def calculate_resource_efficiency_score(self) -> float:
        """Calculate resource efficiency score"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Score based on resource usage (lower is better)
            cpu_score = max(100 - cpu_percent, 0)
            memory_score = max(100 - memory_percent, 0)
            
            return (cpu_score + memory_score) / 2
            
        except Exception:
            return 70.0  # Default score on error
            
    async def calculate_business_impact_score(self) -> float:
        """Calculate business impact score"""
        return min(self.business_metrics['operational_efficiency'], 100)
        
    def calculate_average_processing_time(self) -> float:
        """Calculate average processing time per item"""
        if self.metrics.work_items_processed == 0:
            return 0.0
            
        return self.metrics.processing_time_total / self.metrics.work_items_processed
        
    def calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if self.metrics.work_items_processed == 0:
            return 0.0
            
        return self.error_count / max(self.metrics.work_items_processed, 1)
        
    async def handle_execution_error(self, error: Exception) -> None:
        """Handle errors during main execution loop"""
        try:
            self.error_count += 1
            
            error_data = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'agent_state': self.current_state,
                'business_impact': await self.assess_error_business_impact(error)
            }
            
            # Log error to PostgreSQL
            await self.shared_state.log_system_event(
                'agent_error',
                error_data,
                agent_id=self.agent_id,
                severity=self.determine_error_severity(error)
            )
            
            # Attempt automated recovery if enabled
            if self.auto_recovery_enabled and self.error_count < 3:
                recovery_success = await self.attempt_automated_recovery(error)
                if recovery_success:
                    self.logger.info(f"Automated recovery successful for {type(error).__name__}")
                    return
                    
            # If recovery fails or not enabled, wait before retry
            self.logger.error(f"Agent {self.agent_id} execution error: {error}")
            await asyncio.sleep(min(self.error_count * 5, 30))  # Exponential backoff
            
        except Exception as e:
            self.logger.error(f"Error handling execution error: {e}")
            await asyncio.sleep(30)  # Default wait on error handling failure
            
    async def attempt_automated_recovery(self, error: Exception) -> bool:
        """Attempt automated recovery from error"""
        try:
            self.recovery_attempts += 1
            
            recovery_strategies = {
                ConnectionError: self.recover_connection_error,
                MemoryError: self.recover_memory_error,
                TimeoutError: self.recover_timeout_error,
            }
            
            strategy = recovery_strategies.get(type(error), self.recover_generic_error)
            return await strategy(error)
            
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {e}")
            return False
            
    async def recover_connection_error(self, error: Exception) -> bool:
        """Recover from connection errors"""
        try:
            self.logger.info("Attempting connection recovery...")
            
            # Reinitialize shared state connection
            await self.shared_state.reconnect()
            
            # Update agent state
            await self.shared_state.update_agent_state(self.agent_id, 'active')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection recovery failed: {e}")
            return False
            
    async def recover_memory_error(self, error: Exception) -> bool:
        """Recover from memory errors"""
        try:
            self.logger.info("Attempting memory recovery...")
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Reset metrics to free memory
            self.metrics = AgentMetrics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Memory recovery failed: {e}")
            return False
            
    async def recover_timeout_error(self, error: Exception) -> bool:
        """Recover from timeout errors"""
        try:
            self.logger.info("Attempting timeout recovery...")
            
            # Increase work interval temporarily
            original_interval = self.work_interval
            self.work_interval = min(self.work_interval * 1.5, 300)  # Max 5 minutes
            
            # Reset after successful cycle
            await asyncio.sleep(5)
            self.work_interval = original_interval
            
            return True
            
        except Exception as e:
            self.logger.error(f"Timeout recovery failed: {e}")
            return False
            
    async def recover_generic_error(self, error: Exception) -> bool:
        """Generic recovery strategy"""
        try:
            self.logger.info(f"Attempting generic recovery for {type(error).__name__}")
            
            # Brief pause and state reset
            await asyncio.sleep(2)
            await self.shared_state.update_agent_state(self.agent_id, 'active')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Generic recovery failed: {e}")
            return False
            
    async def handle_startup_error(self, error: Exception) -> None:
        """Handle startup errors"""
        try:
            await self.shared_state.update_agent_state(self.agent_id, 'error')
            await self.shared_state.log_system_event(
                'agent_startup_failure',
                {
                    'agent_id': self.agent_id,
                    'error_type': type(error).__name__,
                    'error_message': str(error)
                },
                agent_id=self.agent_id,
                severity='ERROR'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to handle startup error: {e}")
            
    def determine_error_severity(self, error: Exception) -> str:
        """Determine error severity level"""
        critical_errors = (MemoryError, SystemError, KeyboardInterrupt)
        warning_errors = (ConnectionError, TimeoutError)
        
        if isinstance(error, critical_errors):
            return 'CRITICAL'
        elif isinstance(error, warning_errors):
            return 'WARNING'
        else:
            return 'ERROR'
            
    async def assess_error_business_impact(self, error: Exception) -> Dict[str, Any]:
        """Assess business impact of error"""
        return {
            'cost_impact': 'low' if self.calculate_error_rate() < 0.1 else 'medium',
            'user_impact': 'minimal',
            'revenue_impact': 0.0,
            'operational_impact': 'temporary'
        }
        
    async def check_optimization_opportunities(self) -> None:
        """Check for performance optimization opportunities"""
        try:
            # Check processing efficiency
            avg_time = self.calculate_average_processing_time()
            if avg_time > 5.0:  # 5 seconds threshold
                await self.log_optimization_opportunity(
                    'processing_time',
                    f"Average processing time is {avg_time:.2f}s - consider optimization"
                )
                
            # Check error rate
            error_rate = self.calculate_error_rate()
            if error_rate > 0.05:  # 5% threshold
                await self.log_optimization_opportunity(
                    'error_rate',
                    f"Error rate is {error_rate:.2%} - investigate error patterns"
                )
                
            # Check resource usage
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > 80:
                await self.log_optimization_opportunity(
                    'cpu_usage',
                    f"CPU usage is {cpu_percent}% - consider load balancing"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to check optimization opportunities: {e}")
            
    async def log_optimization_opportunity(self, category: str, description: str) -> None:
        """Log optimization opportunity"""
        try:
            await self.shared_state.log_system_event(
                'optimization_opportunity',
                {
                    'category': category,
                    'description': description,
                    'agent_id': self.agent_id,
                    'current_metrics': {
                        'avg_processing_time': self.calculate_average_processing_time(),
                        'error_rate': self.calculate_error_rate(),
                        'health_score': self.health_score
                    }
                },
                agent_id=self.agent_id,
                severity='INFO'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log optimization opportunity: {e}")
            
    async def log_periodic_performance(self) -> None:
        """Log performance metrics periodically"""
        try:
            current_time = time.time()
            if current_time - self._last_performance_log >= self._performance_log_interval:
                
                performance_summary = {
                    'work_items_processed': self.metrics.work_items_processed,
                    'average_processing_time': self.calculate_average_processing_time(),
                    'error_rate': self.calculate_error_rate(),
                    'health_score': self.health_score,
                    'business_value_generated': self.metrics.business_value_generated,
                    'uptime_hours': (current_time - self.start_time.timestamp()) / 3600 if self.start_time else 0
                }
                
                await self.shared_state.log_system_event(
                    'performance_summary',
                    performance_summary,
                    agent_id=self.agent_id,
                    severity='INFO'
                )
                
                self._last_performance_log = current_time
                
        except Exception as e:
            self.logger.error(f"Failed to log periodic performance: {e}")
            
    async def log_performance_metric(self, metric_name: str, value: float, unit: str) -> None:
        """Log individual performance metric to PostgreSQL"""
        try:
            await self.shared_state.log_performance_metric(
                metric_name,
                value,
                unit,
                agent_id=self.agent_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log performance metric {metric_name}: {e}")
            
    async def setup_health_monitoring(self) -> None:
        """Setup health monitoring components"""
        self.logger.info(f"Health monitoring enabled for {self.agent_id}")
        
    async def setup_business_intelligence(self) -> None:
        """Setup business intelligence components"""
        self.logger.info(f"Business intelligence enabled for {self.agent_id}")
        
    async def get_capabilities(self) -> List[str]:
        """Get agent capabilities for registration"""
        return [
            'postgresql_integration',
            'health_monitoring',
            'automated_recovery',
            'business_intelligence',
            'performance_optimization'
        ]
        
    async def get_configuration(self) -> Dict[str, Any]:
        """Get current agent configuration"""
        return {
            'work_interval': self.work_interval,
            'heartbeat_interval': self.heartbeat_interval,
            'health_monitoring_enabled': self.health_monitoring_enabled,
            'auto_recovery_enabled': self.auto_recovery_enabled,
            'business_metrics_enabled': self.business_metrics_enabled
        }
        
    async def identify_optimization_opportunities(self) -> List[str]:
        """Identify current optimization opportunities"""
        opportunities = []
        
        if self.calculate_average_processing_time() > 5.0:
            opportunities.append("Optimize processing time")
            
        if self.calculate_error_rate() > 0.05:
            opportunities.append("Reduce error rate")
            
        if self.health_score < 80:
            opportunities.append("Improve overall health")
            
        return opportunities
        
    async def generate_recommendations(self) -> List[str]:
        """Generate performance and business recommendations"""
        recommendations = []
        
        if self.business_metrics['cost_efficiency'] < 80:
            recommendations.append("Optimize resource usage for cost efficiency")
            
        if self.error_count > 10:
            recommendations.append("Implement additional error prevention")
            
        if self.business_metrics['operational_efficiency'] < 90:
            recommendations.append("Review workflow optimization")
            
        return recommendations
        
    async def shutdown(self) -> None:
        """Graceful agent shutdown"""
        try:
            self.logger.info(f"Shutting down agent {self.agent_id}")
            self.shutdown_requested = True
            self.is_running = False
            
            # Update state
            await self.shared_state.update_agent_state(self.agent_id, 'stopping')
            
            # Log final metrics
            await self.log_final_metrics()
            
            # Update state to stopped
            await self.shared_state.update_agent_state(self.agent_id, 'inactive')
            
            self.logger.info(f"Agent {self.agent_id} shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during agent shutdown: {e}")
            
    async def log_final_metrics(self) -> None:
        """Log final performance metrics"""
        try:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds() if self.start_time else 0
            
            final_metrics = {
                'total_uptime_seconds': uptime,
                'total_work_items_processed': self.metrics.work_items_processed,
                'total_business_value_generated': self.metrics.business_value_generated,
                'final_health_score': self.health_score,
                'total_error_count': self.error_count,
                'total_recovery_attempts': self.recovery_attempts,
                'average_processing_time': self.calculate_average_processing_time(),
                'final_error_rate': self.calculate_error_rate()
            }
            
            await self.shared_state.log_system_event(
                'agent_shutdown_metrics',
                final_metrics,
                agent_id=self.agent_id,
                severity='INFO'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log final metrics: {e}") 
