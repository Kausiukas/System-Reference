"""
Background Agents Coordination Package

PostgreSQL-based agent coordination and state management.
"""

from .postgresql_adapter import PostgreSQLAdapter
from .shared_state import SharedState
from .base_agent import BaseAgent, AgentMetrics
from .agent_coordinator import AgentCoordinator
from .system_initializer import SystemInitializer

__all__ = [
    'PostgreSQLAdapter',
    'SharedState',
    'BaseAgent', 
    'AgentMetrics',
    'AgentCoordinator',
    'SystemInitializer'
]

__version__ = '1.0.0' 