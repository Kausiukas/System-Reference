"""
PostgreSQL-Based Agent Coordinator

Enterprise-grade agent coordination system with PostgreSQL backend,
automated recovery, health monitoring, and business intelligence.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
import signal
import sys
from dataclasses import dataclass

from .base_agent import BaseAgent
from .shared_state import SharedState


@dataclass
class AgentStatus:
    """Agent status tracking"""
    agent_id: str
    agent_name: str
    state: str
    last_heartbeat: Optional[datetime]
    health_score: float
    error_count: int
    recovery_attempts: int


class AgentCoordinator:
    """
    Enterprise Agent Coordinator with PostgreSQL Integration
    
    Features:
    - Centralized agent lifecycle management
    - Real-time health monitoring and recovery
    - PostgreSQL-backed coordination and state management
    - Business intelligence and performance analytics
    - Automated error recovery and self-healing
    """
    
    def __init__(self, shared_state: SharedState = None):
        self.shared_state = shared_state or SharedState()
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.coordinator_id = "agent_coordinator"
        
        # Coordination configuration
        self.health_check_interval = 30  # seconds
        self.recovery_attempts_max = 3
        self.startup_timeout = 60  # seconds
        self.shutdown_timeout = 30  # seconds
        
        # State tracking
        self.is_running = False
        self.shutdown_requested = False
        self.startup_complete = False
        
        # Performance tracking
        self.performance_metrics = {
            'agents_managed': 0,
            'successful_startups': 0,
            'recovery_actions': 0,
            'health_checks_performed': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(f"coordinator.{self.coordinator_id}")
        
        # Setup signal handlers for graceful shutdown
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        try:
            if sys.platform != 'win32':
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
        except Exception as e:
            self.logger.warning(f"Could not setup signal handlers: {e}")
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.shutdown_requested = True
        
    async def initialize(self) -> None:
        """Initialize coordinator with PostgreSQL backend"""
        try:
            self.logger.info("Initializing Agent Coordinator with PostgreSQL backend")
            
            # Initialize shared state
            await self.shared_state.initialize()
            
            # Register coordinator as special agent
            await self.shared_state.register_agent(
                self.coordinator_id,
                {
                    'agent_type': 'AgentCoordinator',
                    'agent_name': 'Agent Coordinator',
                    'startup_time': datetime.now(timezone.utc).isoformat(),
                    'capabilities': ['agent_management', 'health_monitoring', 'recovery'],
                    'managed_agents': 0
                }
            )
            
            # Update state to active
            await self.shared_state.update_agent_state(self.coordinator_id, 'active')
            
            self.logger.info("Agent Coordinator initialization completed")
            
        except Exception as e:
            self.logger.error(f"Coordinator initialization failed: {e}")
            raise
            
    async def register_agent(self, agent: BaseAgent) -> None:
        """
        Register agent with coordinator
        
        Args:
            agent: Agent instance to register
        """
        try:
            agent_id = agent.agent_id
            
            if agent_id in self.agents:
                self.logger.warning(f"Agent {agent_id} already registered, skipping")
                return
                
            self.agents[agent_id] = agent
            self.performance_metrics['agents_managed'] += 1
            
            self.logger.info(f"Registered agent: {agent_id} ({agent.__class__.__name__})")
            
            # Update coordinator metrics
            await self.update_coordinator_metrics()
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            raise
            
    async def start_all_agents(self) -> Dict[str, bool]:
        """
        Start all registered agents with comprehensive error handling
        
        Returns:
            Dictionary mapping agent_id to startup success status
        """
        startup_results = {}
        
        if not self.agents:
            self.logger.warning("No agents registered for startup")
            return startup_results
            
        self.logger.info(f"Starting {len(self.agents)} agents...")
        self.is_running = True
        
        # Start agents concurrently with timeout protection
        startup_tasks = []
        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(
                self._start_agent_with_timeout(agent_id, agent),
                name=f"startup_{agent_id}"
            )
            startup_tasks.append((agent_id, task))
            
        # Wait for all startups with results collection
        for agent_id, task in startup_tasks:
            try:
                success = await task
                startup_results[agent_id] = success
                
                if success:
                    self.performance_metrics['successful_startups'] += 1
                    self.logger.info(f"Agent {agent_id} started successfully")
                else:
                    self.logger.error(f"Agent {agent_id} startup failed")
                    
            except Exception as e:
                startup_results[agent_id] = False
                self.logger.error(f"Agent {agent_id} startup error: {e}")
                
        # Start coordinator monitoring loop
        if any(startup_results.values()):
            await self.start_monitoring_loop()
            
        self.startup_complete = True
        
        success_count = sum(startup_results.values())
        self.logger.info(f"Agent startup completed: {success_count}/{len(self.agents)} successful")
        
        return startup_results
        
    async def _start_agent_with_timeout(self, agent_id: str, agent: BaseAgent) -> bool:
        """Start individual agent with timeout protection"""
        try:
            # Create agent task
            agent_task = asyncio.create_task(
                agent.startup(),
                name=f"agent_{agent_id}"
            )
            self.agent_tasks[agent_id] = agent_task
            
            # Wait with timeout
            await asyncio.wait_for(agent_task, timeout=self.startup_timeout)
            
            return True
            
        except asyncio.TimeoutError:
            self.logger.error(f"Agent {agent_id} startup timed out after {self.startup_timeout}s")
            await self._handle_agent_startup_failure(agent_id, "startup_timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Agent {agent_id} startup failed: {e}")
            await self._handle_agent_startup_failure(agent_id, str(e))
            return False
            
    async def start_monitoring_loop(self) -> None:
        """Start the monitoring and health check loop"""
        try:
            monitoring_task = asyncio.create_task(
                self._monitoring_loop(),
                name="coordinator_monitoring"
            )
            self.agent_tasks["coordinator_monitoring"] = monitoring_task
            
            self.logger.info("Started coordinator monitoring loop")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring loop: {e}")
            
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for health checks and recovery"""
        self.logger.info("Coordinator monitoring loop started")
        
        while self.is_running and not self.shutdown_requested:
            try:
                # Update coordinator heartbeat
                await self.update_coordinator_heartbeat()
                
                # Perform health checks on all agents
                health_results = await self.perform_health_checks()
                
                # Process health results and trigger recovery if needed
                await self.process_health_results(health_results)
                
                # Update performance metrics
                self.performance_metrics['health_checks_performed'] += 1
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
                
        self.logger.info("Coordinator monitoring loop stopped")
        
    async def perform_health_checks(self) -> Dict[str, AgentStatus]:
        """
        Perform comprehensive health checks on all agents
        
        Returns:
            Dictionary mapping agent_id to AgentStatus
        """
        health_results = {}
        
        for agent_id in self.agents:
            try:
                agent_status = await self.check_agent_health(agent_id)
                health_results[agent_id] = agent_status
                
            except Exception as e:
                self.logger.error(f"Health check failed for {agent_id}: {e}")
                # Create error status
                health_results[agent_id] = AgentStatus(
                    agent_id=agent_id,
                    agent_name="Unknown",
                    state="error",
                    last_heartbeat=None,
                    health_score=0.0,
                    error_count=1,
                    recovery_attempts=0
                )
                
        return health_results
        
    async def check_agent_health(self, agent_id: str) -> AgentStatus:
        """Check individual agent health"""
        try:
            # Get agent data from shared state
            agent_data = await self.shared_state.get_agent_status(agent_id)
            recent_heartbeats = await self.shared_state.get_recent_heartbeats(agent_id, minutes=5)
            
            # Calculate health score
            health_score = await self.calculate_agent_health_score(agent_data, recent_heartbeats)
            
            # Get error count
            error_events = await self.shared_state.get_system_events('error', hours=1)
            agent_errors = [e for e in error_events if e.get('agent_id') == agent_id]
            
            return AgentStatus(
                agent_id=agent_id,
                agent_name=agent_data.get('agent_name', 'Unknown'),
                state=agent_data.get('state', 'unknown'),
                last_heartbeat=recent_heartbeats[0] if recent_heartbeats else None,
                health_score=health_score,
                error_count=len(agent_errors),
                recovery_attempts=agent_data.get('recovery_attempts', 0)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to check health for {agent_id}: {e}")
            raise
            
    async def calculate_agent_health_score(self, agent_data: Dict, heartbeats: List) -> float:
        """Calculate agent health score (0-100)"""
        score = 100.0
        
        # Heartbeat recency (40% weight)
        if heartbeats:
            last_heartbeat = heartbeats[0]
            time_since_heartbeat = (datetime.now(timezone.utc) - last_heartbeat).total_seconds()
            if time_since_heartbeat > 120:  # 2 minutes
                score -= 40 * min(time_since_heartbeat / 300, 1.0)  # Max penalty at 5 minutes
        else:
            score -= 40  # No heartbeat
            
        # Agent state (30% weight)
        state = agent_data.get('state', 'unknown')
        if state == 'failed':
            score -= 30
        elif state == 'error':
            score -= 20
        elif state == 'inactive':
            score -= 15
            
        # Error rate (30% weight)
        error_count = agent_data.get('error_count', 0)
        if error_count > 0:
            score -= min(error_count * 5, 30)  # Max 30 point penalty
            
        return max(score, 0.0)
        
    async def process_health_results(self, health_results: Dict[str, AgentStatus]) -> None:
        """Process health check results and trigger recovery actions"""
        for agent_id, status in health_results.items():
            # Trigger recovery for unhealthy agents
            if status.health_score < 50 and status.recovery_attempts < self.recovery_attempts_max:
                await self.trigger_agent_recovery(agent_id, status)
                
            # Log health warnings
            if status.health_score < 70:
                self.logger.warning(
                    f"Agent {agent_id} health degraded: "
                    f"score={status.health_score:.1f}, state={status.state}, "
                    f"errors={status.error_count}"
                )
                
    async def trigger_agent_recovery(self, agent_id: str, status: AgentStatus) -> bool:
        """
        Trigger automated recovery for an agent
        
        Returns:
            True if recovery was attempted, False otherwise
        """
        try:
            self.logger.info(f"Triggering recovery for agent {agent_id}")
            
            # Determine recovery strategy based on status
            if status.state in ['failed', 'error']:
                recovery_success = await self.restart_agent(agent_id)
            elif status.health_score < 30:
                recovery_success = await self.reset_agent(agent_id)
            else:
                recovery_success = await self.refresh_agent(agent_id)
                
            # Update recovery metrics
            self.performance_metrics['recovery_actions'] += 1
            
            # Log recovery attempt
            await self.shared_state.log_system_event(
                'agent_recovery',
                {
                    'agent_id': agent_id,
                    'recovery_strategy': 'restart' if status.state in ['failed', 'error'] else 'refresh',
                    'success': recovery_success,
                    'previous_health_score': status.health_score
                },
                agent_id=self.coordinator_id,
                severity='INFO' if recovery_success else 'WARNING'
            )
            
            return recovery_success
            
        except Exception as e:
            self.logger.error(f"Recovery failed for agent {agent_id}: {e}")
            return False
            
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart a failed agent"""
        try:
            agent = self.agents.get(agent_id)
            if not agent:
                self.logger.error(f"Cannot restart unknown agent: {agent_id}")
                return False
                
            # Stop current agent task if running
            if agent_id in self.agent_tasks:
                task = self.agent_tasks[agent_id]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                        
            # Mark as restarting
            await self.shared_state.update_agent_state(agent_id, 'restarting')
            
            # Start agent again
            success = await self._start_agent_with_timeout(agent_id, agent)
            
            if success:
                self.logger.info(f"Successfully restarted agent {agent_id}")
            else:
                self.logger.error(f"Failed to restart agent {agent_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error restarting agent {agent_id}: {e}")
            return False
            
    async def reset_agent(self, agent_id: str) -> bool:
        """Reset agent state and attempt recovery"""
        try:
            # Reset agent state
            await self.shared_state.update_agent_state(agent_id, 'resetting')
            
            # Clear recent errors
            await self.shared_state.log_system_event(
                'agent_reset',
                {'agent_id': agent_id, 'reason': 'health_degradation'},
                agent_id=agent_id,
                severity='INFO'
            )
            
            # Update state to active
            await self.shared_state.update_agent_state(agent_id, 'active')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting agent {agent_id}: {e}")
            return False
            
    async def refresh_agent(self, agent_id: str) -> bool:
        """Refresh agent state"""
        try:
            # Send refresh signal
            await self.shared_state.log_system_event(
                'agent_refresh',
                {'agent_id': agent_id, 'reason': 'health_maintenance'},
                agent_id=agent_id,
                severity='INFO'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error refreshing agent {agent_id}: {e}")
            return False
            
    async def update_coordinator_heartbeat(self) -> None:
        """Update coordinator's own heartbeat"""
        try:
            heartbeat_data = {
                'agent_name': 'Agent Coordinator',
                'state': 'monitoring',
                'agents_managed': len(self.agents),
                'active_tasks': len([t for t in self.agent_tasks.values() if not t.done()]),
                'performance_metrics': self.performance_metrics,
                'system_health': await self.calculate_system_health()
            }
            
            await self.shared_state.update_agent_heartbeat(
                self.coordinator_id,
                datetime.now(timezone.utc),
                heartbeat_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update coordinator heartbeat: {e}")
            
    async def calculate_system_health(self) -> Dict:
        """Calculate overall system health metrics"""
        try:
            active_agents = 0
            total_health = 0
            
            for agent_id in self.agents:
                try:
                    agent_data = await self.shared_state.get_agent_status(agent_id)
                    if agent_data.get('state') == 'active':
                        active_agents += 1
                        
                    recent_heartbeats = await self.shared_state.get_recent_heartbeats(agent_id, minutes=5)
                    health_score = await self.calculate_agent_health_score(agent_data, recent_heartbeats)
                    total_health += health_score
                    
                except Exception:
                    continue
                    
            return {
                'total_agents': len(self.agents),
                'active_agents': active_agents,
                'average_health': total_health / len(self.agents) if self.agents else 0,
                'system_status': 'healthy' if active_agents >= len(self.agents) * 0.8 else 'degraded'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate system health: {e}")
            return {'error': str(e)}
            
    async def update_coordinator_metrics(self) -> None:
        """Update coordinator performance metrics"""
        try:
            await self.shared_state.log_performance_metric(
                'agents_managed',
                len(self.agents),
                'count',
                agent_id=self.coordinator_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update coordinator metrics: {e}")
            
    async def _handle_agent_startup_failure(self, agent_id: str, error_reason: str) -> None:
        """Handle agent startup failure"""
        try:
            await self.shared_state.update_agent_state(agent_id, 'failed')
            await self.shared_state.log_system_event(
                'agent_startup_failure',
                {'agent_id': agent_id, 'reason': error_reason},
                agent_id=agent_id,
                severity='ERROR'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to handle startup failure for {agent_id}: {e}")
            
    async def shutdown(self) -> None:
        """Graceful shutdown of all agents and coordinator"""
        try:
            self.logger.info("Starting graceful shutdown of all agents...")
            self.shutdown_requested = True
            self.is_running = False
            
            # Cancel all agent tasks
            shutdown_tasks = []
            for agent_id, task in self.agent_tasks.items():
                if not task.done():
                    self.logger.info(f"Shutting down {agent_id}...")
                    task.cancel()
                    shutdown_tasks.append(task)
                    
            # Wait for all tasks to complete
            if shutdown_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*shutdown_tasks, return_exceptions=True),
                        timeout=self.shutdown_timeout
                    )
                except asyncio.TimeoutError:
                    self.logger.warning("Some agents did not shutdown gracefully within timeout")
                    
            # Update coordinator state
            await self.shared_state.update_agent_state(self.coordinator_id, 'stopped')
            
            # Close shared state connection
            await self.shared_state.close()
            
            self.logger.info("Agent coordinator shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            
    async def get_agent_status_summary(self) -> Dict:
        """Get comprehensive status summary of all agents"""
        try:
            summary = {
                'coordinator_status': {
                    'is_running': self.is_running,
                    'startup_complete': self.startup_complete,
                    'agents_managed': len(self.agents),
                    'performance_metrics': self.performance_metrics
                },
                'agents': {},
                'system_health': await self.calculate_system_health()
            }
            
            # Get individual agent statuses
            for agent_id in self.agents:
                try:
                    agent_data = await self.shared_state.get_agent_status(agent_id)
                    recent_heartbeats = await self.shared_state.get_recent_heartbeats(agent_id, minutes=5)
                    health_score = await self.calculate_agent_health_score(agent_data, recent_heartbeats)
                    
                    summary['agents'][agent_id] = {
                        'agent_name': agent_data.get('agent_name', 'Unknown'),
                        'state': agent_data.get('state', 'unknown'),
                        'health_score': health_score,
                        'last_heartbeat': recent_heartbeats[0] if recent_heartbeats else None,
                        'task_status': 'running' if agent_id in self.agent_tasks and not self.agent_tasks[agent_id].done() else 'stopped'
                    }
                    
                except Exception as e:
                    summary['agents'][agent_id] = {'error': str(e)}
                    
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get status summary: {e}")
            return {'error': str(e)} 