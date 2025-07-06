"""
Coordination Package

Contains core coordination and management components for the background agents system.
Provides PostgreSQL-based shared state, agent lifecycle management, and system coordination.
"""

from .agent_coordinator import AgentCoordinator
from .shared_state import SharedState
from .base_agent import BaseAgent, AgentState
from .postgresql_adapter import PostgreSQLAdapter
from .system_initializer import SystemInitializer

__all__ = [
    'AgentCoordinator',
    'SharedState',
    'BaseAgent', 
    'AgentState',
    'PostgreSQLAdapter',
    'SystemInitializer'
] 