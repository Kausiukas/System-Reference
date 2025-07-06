"""
Background Agents Package

This package contains all the background agents for the monitoring system.
Provides infrastructure for PostgreSQL-based agent coordination, monitoring,
and AI-powered system management.
"""

from .coordination.agent_coordinator import AgentCoordinator
from .coordination.shared_state import SharedState
from .coordination.base_agent import BaseAgent, AgentState

__version__ = "1.0.0"
__all__ = [
    'AgentCoordinator',
    'SharedState', 
    'BaseAgent',
    'AgentState'
] 