"""
Background Agents Monitoring Package

This package contains monitoring and system health agents for the PostgreSQL-based
background agents system.

Available Agents:
- HeartbeatHealthAgent: System health monitoring and alerting
- PerformanceMonitor: Resource usage tracking and metrics collection
- LangSmithBridge: LLM conversation logging and tracing integration
- EnhancedSharedStateMonitor: Advanced shared state monitoring
- SelfHealingAgent: Automated system recovery and maintenance
"""

from .heartbeat_health_agent import HeartbeatHealthAgent
from .performance_monitor import PerformanceMonitor
from .langsmith_bridge import LangSmithBridge
from .enhanced_shared_state_monitor import EnhancedSharedStateMonitor
from .self_healing_agent import SelfHealingAgent

__all__ = [
    'HeartbeatHealthAgent',
    'PerformanceMonitor', 
    'LangSmithBridge',
    'EnhancedSharedStateMonitor',
    'SelfHealingAgent'
]

__version__ = '1.0.0' 