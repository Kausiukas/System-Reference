"""
Background Agents System

PostgreSQL-based multi-agent monitoring and coordination platform.
"""

from .coordination.postgresql_adapter import PostgreSQLAdapter
from .coordination.shared_state import SharedState
from .coordination.base_agent import BaseAgent, AgentMetrics
from .coordination.agent_coordinator import AgentCoordinator
from .coordination.system_initializer import SystemInitializer

__all__ = [
    'PostgreSQLAdapter',
    'SharedState', 
    'BaseAgent',
    'AgentMetrics',
    'AgentCoordinator',
    'SystemInitializer'
]

__version__ = '1.0.0' 
