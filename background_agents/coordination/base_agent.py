"""
Base Agent Class

Provides the foundation for all background agents in the system.
Includes lifecycle management, health monitoring, PostgreSQL integration,
and comprehensive error handling.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AgentState(Enum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class BaseAgent(ABC):
    """
    Base class for all background agents.
    
    Provides common functionality for:
    - Lifecycle management with proper state transitions
    - Health monitoring and heartbeat system
    - Metrics tracking and performance monitoring
    - PostgreSQL integration through SharedState
    - Error handling and recovery mechanisms
    - Async operation support
    """
    
    def __init__(self, agent_id: str, shared_state, **kwargs):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            shared_state: SharedState instance for database operations
            **kwargs: Additional configuration options
        """
        self.agent_id = agent_id
        self.shared_state = shared_state
        self.state = AgentState.INITIALIZING
        
        # Configuration
        self.config = kwargs
        self.heartbeat_interval = kwargs.get('heartbeat_interval', 60)  # seconds
        self.max_retries = kwargs.get('max_retries', 3)
        self.work_interval = kwargs.get('work_interval', 30)  # seconds between work cycles
        
        # State tracking
        self.start_time = None
        self.last_heartbeat = None
        self.error_count = 0
        self.work_cycles_completed = 0
        self.metrics = {}
        
        # Control flags
        self._running = False
        self._should_stop = False
        self._tasks = []
        
        logger.info(f"Initialized agent {self.agent_id}")
    
    async def start(self):
        """Start the agent and begin its main operations."""
        try:
            self.state = AgentState.RUNNING
            self.start_time = datetime.now(timezone.utc)
            self._running = True
            
            # Register with shared state
            await self._register_agent()
            
            logger.info(f"Starting agent {self.agent_id}")
            
            # Start concurrent tasks
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            main_task = asyncio.create_task(self._main_loop())
            
            self._tasks = [heartbeat_task, main_task]
            
            # Wait for any task to complete (which indicates shutdown)
            done, pending = await asyncio.wait(
                self._tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            logger.error(f"Error in agent {self.agent_id}: {e}")
            self.state = AgentState.ERROR
            self.error_count += 1
        finally:
            await self._cleanup()
    
    async def stop(self):
        """Stop the agent gracefully."""
        logger.info(f"Stopping agent {self.agent_id}")
        self._should_stop = True
        self.state = AgentState.STOPPING
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Wait a moment for graceful shutdown
        await asyncio.sleep(1)
        
        self.state = AgentState.STOPPED
        self._running = False
    
    async def _register_agent(self):
        """Register agent with shared state."""
        try:
            agent_data = {
                'agent_id': self.agent_id,
                'state': self.state.value,
                'started_at': self.start_time.isoformat() if self.start_time else None,
                'config': self.config,
                'heartbeat_interval': self.heartbeat_interval,
                'version': getattr(self, '__version__', '1.0.0')
            }
            
            # Update agent state in database
            if hasattr(self.shared_state, 'update_agent_state'):
                await self.shared_state.update_agent_state(
                    self.agent_id,
                    self.state.value,
                    metadata=agent_data
                )
            
        except Exception as e:
            logger.error(f"Failed to register agent {self.agent_id}: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat signals."""
        while self._running and not self._should_stop:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error for {self.agent_id}: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _send_heartbeat(self):
        """Send a heartbeat signal with current metrics."""
        try:
            self.last_heartbeat = datetime.now(timezone.utc)
            
            # Calculate uptime
            uptime_seconds = None
            if self.start_time:
                uptime_seconds = (self.last_heartbeat - self.start_time).total_seconds()
            
            heartbeat_data = {
                'agent_id': self.agent_id,
                'timestamp': self.last_heartbeat.isoformat(),
                'state': self.state.value,
                'error_count': self.error_count,
                'work_cycles_completed': self.work_cycles_completed,
                'uptime_seconds': uptime_seconds,
                'metrics': self.metrics
            }
            
            # Update heartbeat in database
            if hasattr(self.shared_state, 'update_agent_heartbeat'):
                await self.shared_state.update_agent_heartbeat(
                    self.agent_id,
                    self.last_heartbeat,
                    heartbeat_data
                )
            
        except Exception as e:
            logger.error(f"Failed to send heartbeat for {self.agent_id}: {e}")
    
    async def _main_loop(self):
        """Main agent execution loop."""
        while self._running and not self._should_stop:
            try:
                # Call the agent-specific work method
                await self.do_work()
                
                # Update metrics and counters
                self.work_cycles_completed += 1
                self.metrics['last_work_completed'] = datetime.now(timezone.utc).isoformat()
                self.metrics['work_cycles_completed'] = self.work_cycles_completed
                
                # Wait before next iteration
                await asyncio.sleep(self.work_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop for {self.agent_id}: {e}")
                self.error_count += 1
                
                # Update error metrics
                self.metrics['last_error'] = str(e)
                self.metrics['last_error_time'] = datetime.now(timezone.utc).isoformat()
                
                if self.error_count >= self.max_retries:
                    logger.error(f"Max retries exceeded for {self.agent_id}")
                    self.state = AgentState.ERROR
                    break
                
                # Wait before retrying
                await asyncio.sleep(5)
    
    async def _cleanup(self):
        """Cleanup resources when agent stops."""
        try:
            # Update final state
            if hasattr(self.shared_state, 'update_agent_state'):
                await self.shared_state.update_agent_state(
                    self.agent_id,
                    self.state.value,
                    metadata={
                        'stopped_at': datetime.now(timezone.utc).isoformat(),
                        'final_error_count': self.error_count,
                        'work_cycles_completed': self.work_cycles_completed
                    }
                )
            
            # Call agent-specific cleanup
            await self.cleanup()
            
        except Exception as e:
            logger.error(f"Error during cleanup for {self.agent_id}: {e}")
    
    def update_metric(self, key: str, value: Any):
        """Update an agent metric."""
        self.metrics[key] = value
        self.metrics['last_metric_update'] = datetime.now(timezone.utc).isoformat()
    
    def increment_metric(self, key: str, amount: int = 1):
        """Increment a counter metric."""
        current_value = self.metrics.get(key, 0)
        self.metrics[key] = current_value + amount
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        return {
            'agent_id': self.agent_id,
            'state': self.state.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'uptime_seconds': uptime,
            'error_count': self.error_count,
            'work_cycles_completed': self.work_cycles_completed,
            'metrics': self.metrics,
            'config': self.config
        }
    
    def is_healthy(self) -> bool:
        """Check if agent is in a healthy state."""
        if self.state in [AgentState.ERROR, AgentState.STOPPED]:
            return False
        
        # Check if heartbeat is recent
        if self.last_heartbeat:
            time_since_heartbeat = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
            if time_since_heartbeat > self.heartbeat_interval * 2:  # Allow 2x heartbeat interval
                return False
        
        # Check error rate
        if self.error_count >= self.max_retries:
            return False
        
        return True
    
    @abstractmethod
    async def do_work(self):
        """
        Implement the main work of the agent.
        
        This method should contain the agent's core logic and will be called
        repeatedly in the main loop with intervals defined by work_interval.
        
        Should be implemented by each specific agent.
        """
        pass
    
    async def cleanup(self):
        """
        Override to provide agent-specific cleanup.
        
        Called when the agent is stopping. Default implementation does nothing.
        Override in specific agents to cleanup resources, close connections, etc.
        """
        pass
    
    def __repr__(self):
        """String representation of the agent."""
        return f"<{self.__class__.__name__}(id={self.agent_id}, state={self.state.value})>" 