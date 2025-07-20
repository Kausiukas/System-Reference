"""
Agent Memory Optimization Interface

Standardized interface for distributed memory optimization across all agents.
Each agent implements this interface to participate in coordinated memory management.
"""

import asyncio
import logging
import gc
import weakref
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from abc import ABC, abstractmethod
import psutil
import tracemalloc


@dataclass
class AgentMemoryStatus:
    """Agent memory status report"""
    agent_id: str
    agent_name: str
    current_memory_mb: float
    baseline_memory_mb: float
    memory_growth_rate_mb_per_hour: float
    memory_efficiency_score: float  # 0-100
    optimization_opportunities: List[str]
    last_optimization: Optional[datetime]
    optimization_history: List[Dict[str, Any]]


@dataclass
class MemoryOptimizationRequest:
    """Memory optimization request from coordinator"""
    request_id: str
    optimization_type: str
    priority: int  # 1-10
    estimated_savings_mb: float
    description: str
    parameters: Dict[str, Any]


@dataclass
class MemoryOptimizationResult:
    """Memory optimization result from agent"""
    request_id: str
    success: bool
    actual_savings_mb: float
    execution_time_seconds: float
    error_message: Optional[str]
    optimization_details: Dict[str, Any]


class AgentMemoryOptimizer(ABC):
    """
    Abstract base class for agent memory optimization
    
    Each agent should implement this interface to participate in
    distributed memory management and optimization.
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"memory_optimizer.{agent_id}")
        
        # Memory tracking
        self.memory_history = []
        self.baseline_memory_mb = 0.0
        self.optimization_history = []
        self.last_optimization = None
        
        # Optimization strategies
        self.optimization_strategies = {
            'garbage_collection': self._optimize_garbage_collection,
            'cache_clear': self._optimize_cache_clear,
            'object_cleanup': self._optimize_object_cleanup,
            'memory_compression': self._optimize_memory_compression,
            'resource_release': self._optimize_resource_release
        }
        
        # Initialize baseline memory
        self._initialize_baseline_memory()
    
    def _initialize_baseline_memory(self) -> None:
        """Initialize baseline memory measurement"""
        try:
            process = psutil.Process()
            self.baseline_memory_mb = process.memory_info().rss / 1024 / 1024
        except Exception as e:
            self.logger.error(f"Failed to initialize baseline memory: {e}")
            self.baseline_memory_mb = 100.0  # Default baseline
    
    async def get_memory_status(self) -> AgentMemoryStatus:
        """Get current agent memory status"""
        try:
            # Get current memory usage
            process = psutil.Process()
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Calculate memory growth rate
            memory_growth_rate = self._calculate_memory_growth_rate()
            
            # Calculate efficiency score
            efficiency_score = self._calculate_efficiency_score(current_memory_mb)
            
            # Identify optimization opportunities
            opportunities = await self._identify_optimization_opportunities()
            
            return AgentMemoryStatus(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                current_memory_mb=current_memory_mb,
                baseline_memory_mb=self.baseline_memory_mb,
                memory_growth_rate_mb_per_hour=memory_growth_rate,
                memory_efficiency_score=efficiency_score,
                optimization_opportunities=opportunities,
                last_optimization=self.last_optimization,
                optimization_history=self.optimization_history[-10:]  # Last 10 optimizations
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get memory status: {e}")
            return AgentMemoryStatus(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                current_memory_mb=0.0,
                baseline_memory_mb=self.baseline_memory_mb,
                memory_growth_rate_mb_per_hour=0.0,
                memory_efficiency_score=0.0,
                optimization_opportunities=[],
                last_optimization=self.last_optimization,
                optimization_history=[]
            )
    
    async def optimize_memory(self, request: MemoryOptimizationRequest) -> MemoryOptimizationResult:
        """Execute memory optimization based on request"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info(f"Executing memory optimization: {request.optimization_type}")
            
            # Get memory before optimization
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # Execute optimization strategy
            strategy = self.optimization_strategies.get(request.optimization_type)
            if strategy:
                result = await strategy(request.parameters)
            else:
                # Try agent-specific optimization
                result = await self._agent_specific_optimization(request)
            
            # Get memory after optimization
            memory_after = process.memory_info().rss / 1024 / 1024
            actual_savings = memory_before - memory_after
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Update optimization history
            optimization_record = {
                'request_id': request.request_id,
                'optimization_type': request.optimization_type,
                'timestamp': datetime.now(timezone.utc),
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'savings_mb': actual_savings,
                'execution_time_seconds': execution_time,
                'success': result.get('success', False)
            }
            self.optimization_history.append(optimization_record)
            self.last_optimization = datetime.now(timezone.utc)
            
            return MemoryOptimizationResult(
                request_id=request.request_id,
                success=result.get('success', False),
                actual_savings_mb=actual_savings,
                execution_time_seconds=execution_time,
                error_message=result.get('error'),
                optimization_details=result
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"Memory optimization failed: {e}")
            
            return MemoryOptimizationResult(
                request_id=request.request_id,
                success=False,
                actual_savings_mb=0.0,
                execution_time_seconds=execution_time,
                error_message=str(e),
                optimization_details={}
            )
    
    async def _optimize_garbage_collection(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize garbage collection"""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Collect weak references
            weakref._weakref._cleanup()
            
            return {
                'success': True,
                'objects_collected': collected,
                'strategy': 'forced_garbage_collection'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _optimize_cache_clear(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clear agent-specific caches"""
        try:
            # Clear any agent-specific caches
            caches_cleared = await self._clear_agent_caches()
            
            return {
                'success': True,
                'caches_cleared': caches_cleared,
                'strategy': 'cache_clear'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _optimize_object_cleanup(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up unnecessary objects"""
        try:
            # Clean up agent-specific objects
            objects_cleaned = await self._cleanup_agent_objects()
            
            return {
                'success': True,
                'objects_cleaned': objects_cleaned,
                'strategy': 'object_cleanup'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _optimize_memory_compression(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Compress memory usage"""
        try:
            # Implement memory compression strategies
            compression_result = await self._compress_agent_memory()
            
            return {
                'success': True,
                'compression_applied': compression_result,
                'strategy': 'memory_compression'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _optimize_resource_release(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Release unused resources"""
        try:
            # Release agent-specific resources
            resources_released = await self._release_agent_resources()
            
            return {
                'success': True,
                'resources_released': resources_released,
                'strategy': 'resource_release'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_memory_growth_rate(self) -> float:
        """Calculate memory growth rate in MB per hour"""
        if len(self.memory_history) < 2:
            return 0.0
        
        # Get recent memory measurements
        recent_history = self.memory_history[-10:]  # Last 10 measurements
        
        if len(recent_history) >= 2:
            time_diff = (recent_history[-1]['timestamp'] - recent_history[0]['timestamp']).total_seconds() / 3600
            memory_diff = recent_history[-1]['memory_mb'] - recent_history[0]['memory_mb']
            
            if time_diff > 0:
                return memory_diff / time_diff
        
        return 0.0
    
    def _calculate_efficiency_score(self, current_memory_mb: float) -> float:
        """Calculate memory efficiency score (0-100)"""
        if self.baseline_memory_mb <= 0:
            return 100.0
        
        # Calculate efficiency based on memory usage relative to baseline
        memory_ratio = current_memory_mb / self.baseline_memory_mb
        
        if memory_ratio <= 1.0:
            # At or below baseline - excellent efficiency
            return 100.0
        elif memory_ratio <= 1.5:
            # Up to 50% above baseline - good efficiency
            return max(0, 100 - (memory_ratio - 1.0) * 100)
        else:
            # More than 50% above baseline - poor efficiency
            return max(0, 50 - (memory_ratio - 1.5) * 50)
    
    async def _identify_optimization_opportunities(self) -> List[str]:
        """Identify memory optimization opportunities for this agent"""
        opportunities = []
        
        try:
            # Check current memory usage
            process = psutil.Process()
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            
            # High memory usage opportunity
            if current_memory_mb > self.baseline_memory_mb * 1.5:
                opportunities.append("High memory usage - implement aggressive cleanup")
            
            # Memory growth opportunity
            growth_rate = self._calculate_memory_growth_rate()
            if growth_rate > 10:  # More than 10MB per hour
                opportunities.append(f"High memory growth rate ({growth_rate:.1f}MB/hour) - investigate leaks")
            
            # Agent-specific opportunities
            agent_opportunities = await self._get_agent_specific_opportunities()
            opportunities.extend(agent_opportunities)
            
        except Exception as e:
            self.logger.error(f"Failed to identify optimization opportunities: {e}")
        
        return opportunities
    
    # Abstract methods that agents must implement
    @abstractmethod
    async def _clear_agent_caches(self) -> int:
        """Clear agent-specific caches. Return number of caches cleared."""
        pass
    
    @abstractmethod
    async def _cleanup_agent_objects(self) -> int:
        """Clean up agent-specific objects. Return number of objects cleaned."""
        pass
    
    @abstractmethod
    async def _compress_agent_memory(self) -> Dict[str, Any]:
        """Compress agent memory usage. Return compression details."""
        pass
    
    @abstractmethod
    async def _release_agent_resources(self) -> int:
        """Release agent-specific resources. Return number of resources released."""
        pass
    
    @abstractmethod
    async def _get_agent_specific_opportunities(self) -> List[str]:
        """Get agent-specific optimization opportunities."""
        pass
    
    @abstractmethod
    async def _agent_specific_optimization(self, request: MemoryOptimizationRequest) -> Dict[str, Any]:
        """Perform agent-specific memory optimization."""
        pass
    
    def update_memory_history(self) -> None:
        """Update memory history with current measurement"""
        try:
            process = psutil.Process()
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            
            self.memory_history.append({
                'timestamp': datetime.now(timezone.utc),
                'memory_mb': current_memory_mb
            })
            
            # Keep only last 100 measurements
            if len(self.memory_history) > 100:
                self.memory_history = self.memory_history[-100:]
                
        except Exception as e:
            self.logger.error(f"Failed to update memory history: {e}")


class MemoryOptimizationMixin:
    """
    Mixin class to add memory optimization capabilities to any agent
    
    Usage:
    class MyAgent(BaseAgent, MemoryOptimizationMixin):
        def __init__(self, agent_id, shared_state):
            super().__init__(agent_id, shared_state)
            MemoryOptimizationMixin.__init__(self, agent_id, self.agent_name)
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        # Use a concrete implementation instead of abstract class
        self.memory_optimizer = None  # Will be set by specific agent implementations
        self.memory_optimization_enabled = True
    
    async def get_memory_status(self) -> AgentMemoryStatus:
        """Get memory status for this agent"""
        if self.memory_optimization_enabled:
            return await self.memory_optimizer.get_memory_status()
        else:
            return AgentMemoryStatus(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                current_memory_mb=0.0,
                baseline_memory_mb=0.0,
                memory_growth_rate_mb_per_hour=0.0,
                memory_efficiency_score=0.0,
                optimization_opportunities=[],
                last_optimization=None,
                optimization_history=[]
            )
    
    async def optimize_memory(self, request: MemoryOptimizationRequest) -> MemoryOptimizationResult:
        """Execute memory optimization for this agent"""
        if self.memory_optimization_enabled:
            return await self.memory_optimizer.optimize_memory(request)
        else:
            return MemoryOptimizationResult(
                request_id=request.request_id,
                success=False,
                actual_savings_mb=0.0,
                execution_time_seconds=0.0,
                error_message="Memory optimization disabled for this agent",
                optimization_details={}
            )
    
    def update_memory_history(self) -> None:
        """Update memory history for this agent"""
        if self.memory_optimization_enabled:
            self.memory_optimizer.update_memory_history()


# Example implementation for AI Help Agent
class AIHelpAgentMemoryOptimizer(AgentMemoryOptimizer):
    """Memory optimizer specifically for AI Help Agent"""
    
    def __init__(self, agent_id: str, agent_name: str, rag_system=None, context_integrator=None):
        super().__init__(agent_id, agent_name)
        self.rag_system = rag_system
        self.context_integrator = context_integrator
    
    async def _clear_agent_caches(self) -> int:
        """Clear AI Help Agent specific caches"""
        caches_cleared = 0
        
        try:
            # Clear RAG system caches
            if self.rag_system and hasattr(self.rag_system, 'clear_caches'):
                await self.rag_system.clear_caches()
                caches_cleared += 1
            
            # Clear context integrator caches
            if self.context_integrator and hasattr(self.context_integrator, 'clear_caches'):
                await self.context_integrator.clear_caches()
                caches_cleared += 1
            
            # Clear conversation memory caches
            if hasattr(self, 'conversation_memory'):
                self.conversation_memory.clear()
                caches_cleared += 1
            
        except Exception as e:
            self.logger.error(f"Failed to clear agent caches: {e}")
        
        return caches_cleared
    
    async def _cleanup_agent_objects(self) -> int:
        """Clean up AI Help Agent specific objects"""
        objects_cleaned = 0
        
        try:
            # Clean up old conversation history
            if hasattr(self, 'conversation_memory'):
                # Keep only recent conversations
                if len(self.conversation_memory.conversation_history) > 20:
                    self.conversation_memory.conversation_history = self.conversation_memory.conversation_history[-20:]
                    objects_cleaned += 1
            
            # Clean up old request queue items
            if hasattr(self, 'request_queue'):
                # Clear old requests
                while not self.request_queue.empty():
                    try:
                        self.request_queue.get_nowait()
                        objects_cleaned += 1
                    except:
                        break
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup agent objects: {e}")
        
        return objects_cleaned
    
    async def _compress_agent_memory(self) -> Dict[str, Any]:
        """Compress AI Help Agent memory usage"""
        compression_details = {}
        
        try:
            # Compress conversation history
            if hasattr(self, 'conversation_memory'):
                original_size = len(str(self.conversation_memory.conversation_history))
                
                # Remove metadata from old conversations
                for conv in self.conversation_memory.conversation_history[:-5]:
                    if 'metadata' in conv:
                        conv['metadata'] = {}
                
                compressed_size = len(str(self.conversation_memory.conversation_history))
                compression_details['conversation_compression'] = {
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': compressed_size / original_size if original_size > 0 else 1.0
                }
            
        except Exception as e:
            self.logger.error(f"Failed to compress agent memory: {e}")
        
        return compression_details
    
    async def _release_agent_resources(self) -> int:
        """Release AI Help Agent specific resources"""
        resources_released = 0
        
        try:
            # Release RAG system resources
            if self.rag_system and hasattr(self.rag_system, 'release_resources'):
                await self.rag_system.release_resources()
                resources_released += 1
            
            # Release context integrator resources
            if self.context_integrator and hasattr(self.context_integrator, 'release_resources'):
                await self.context_integrator.release_resources()
                resources_released += 1
            
        except Exception as e:
            self.logger.error(f"Failed to release agent resources: {e}")
        
        return resources_released
    
    async def _get_agent_specific_opportunities(self) -> List[str]:
        """Get AI Help Agent specific optimization opportunities"""
        opportunities = []
        
        try:
            # Check RAG system memory usage
            if self.rag_system and hasattr(self.rag_system, 'get_memory_usage'):
                rag_memory = await self.rag_system.get_memory_usage()
                if rag_memory > 200:  # More than 200MB
                    opportunities.append("Large RAG system memory usage - consider cleanup")
            
            # Check conversation history size
            if hasattr(self, 'conversation_memory'):
                if len(self.conversation_memory.conversation_history) > 50:
                    opportunities.append("Large conversation history - consider pruning")
            
        except Exception as e:
            self.logger.error(f"Failed to get agent-specific opportunities: {e}")
        
        return opportunities
    
    async def _agent_specific_optimization(self, request: MemoryOptimizationRequest) -> Dict[str, Any]:
        """Perform AI Help Agent specific memory optimization"""
        try:
            if request.optimization_type == 'rag_cleanup':
                # Clean up RAG system
                if self.rag_system and hasattr(self.rag_system, 'cleanup'):
                    result = await self.rag_system.cleanup()
                    return {'success': True, 'rag_cleanup_result': result}
            
            elif request.optimization_type == 'conversation_pruning':
                # Prune conversation history
                if hasattr(self, 'conversation_memory'):
                    original_count = len(self.conversation_memory.conversation_history)
                    # Keep only last 10 conversations
                    self.conversation_memory.conversation_history = self.conversation_memory.conversation_history[-10:]
                    pruned_count = original_count - len(self.conversation_memory.conversation_history)
                    return {'success': True, 'conversations_pruned': pruned_count}
            
            return {'success': False, 'error': 'Unknown optimization type'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)} 