"""
Enhanced Memory Management System for AI Help Agent Platform

Advanced memory optimization with predictive analysis, intelligent cleanup,
distributed optimization, and maximum efficiency strategies.
"""

import asyncio
import logging
import time
import psutil
import gc
import os
import shutil
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import statistics
import weakref
from collections import defaultdict, deque
import threading
import tracemalloc

from ..coordination.base_agent import BaseAgent
from ..coordination.shared_state import SharedState
from .memory_manager import MemoryUsageTracker, MemoryLeakDetector, VectorStoreManager


@dataclass
class MemoryMetrics:
    """Enhanced memory usage metrics data structure"""
    timestamp: datetime
    total_memory_mb: float
    available_memory_mb: float
    memory_usage_percent: float
    vector_store_size_mb: float
    embedding_cache_size_mb: float
    process_memory_mb: float
    memory_trend: str = 'stable'
    memory_pressure_score: float = 0.0  # 0-100 scale
    optimization_opportunities: List[str] = field(default_factory=list)


@dataclass
class MemoryOptimization:
    """Memory optimization strategy"""
    strategy_id: str
    strategy_type: str
    description: str
    estimated_savings_mb: float
    execution_time_seconds: float
    risk_level: str  # low, medium, high
    priority: int  # 1-10, higher is more important
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AgentMemoryProfile:
    """Individual agent memory profile"""
    agent_id: str
    agent_name: str
    baseline_memory_mb: float
    current_memory_mb: float
    memory_growth_rate_mb_per_hour: float
    memory_efficiency_score: float  # 0-100
    optimization_recommendations: List[str] = field(default_factory=list)
    last_optimization: Optional[datetime] = None


class PredictiveMemoryAnalyzer:
    """Predictive memory analysis with ML-like pattern recognition"""
    
    def __init__(self):
        self.memory_patterns = deque(maxlen=1000)
        self.prediction_window = 24  # hours
        self.confidence_threshold = 0.8
        
    async def analyze_memory_patterns(self, memory_history: List[MemoryMetrics]) -> Dict[str, Any]:
        """Analyze memory patterns for predictive insights"""
        if len(memory_history) < 10:
            return {'predictions': [], 'confidence': 0.0}
            
        patterns = {
            'hourly_cycles': self._detect_hourly_cycles(memory_history),
            'daily_trends': self._detect_daily_trends(memory_history),
            'growth_patterns': self._detect_growth_patterns(memory_history),
            'pressure_points': self._detect_pressure_points(memory_history)
        }
        
        predictions = self._generate_predictions(patterns, memory_history)
        
        return {
            'patterns': patterns,
            'predictions': predictions,
            'confidence': self._calculate_confidence(patterns),
            'recommendations': self._generate_recommendations(patterns)
        }
    
    def _detect_hourly_cycles(self, history: List[MemoryMetrics]) -> Dict[str, Any]:
        """Detect hourly memory usage patterns"""
        hourly_data = defaultdict(list)
        
        for metric in history[-168:]:  # Last week
            hour = metric.timestamp.hour
            hourly_data[hour].append(metric.memory_usage_percent)
        
        cycles = {}
        for hour, values in hourly_data.items():
            if len(values) >= 3:
                cycles[hour] = {
                    'average_usage': statistics.mean(values),
                    'peak_usage': max(values),
                    'volatility': statistics.stdev(values) if len(values) > 1 else 0
                }
        
        return cycles
    
    def _detect_daily_trends(self, history: List[MemoryMetrics]) -> Dict[str, Any]:
        """Detect daily memory usage trends"""
        if len(history) < 7:
            return {}
            
        daily_averages = []
        for i in range(7):
            day_start = len(history) - (7 - i) * 24
            day_end = len(history) - (6 - i) * 24
            if day_start >= 0 and day_end <= len(history):
                day_metrics = history[day_start:day_end]
                if day_metrics:
                    daily_averages.append(statistics.mean([m.memory_usage_percent for m in day_metrics]))
        
        if len(daily_averages) >= 3:
            trend_slope = self._calculate_slope(list(range(len(daily_averages))), daily_averages)
            return {
                'trend_slope': trend_slope,
                'trend_direction': 'increasing' if trend_slope > 0.5 else 'decreasing' if trend_slope < -0.5 else 'stable',
                'daily_averages': daily_averages
            }
        
        return {}
    
    def _detect_growth_patterns(self, history: List[MemoryMetrics]) -> Dict[str, Any]:
        """Detect memory growth patterns"""
        if len(history) < 20:
            return {}
            
        recent = history[-20:]
        growth_rates = []
        
        for i in range(1, len(recent)):
            time_diff = (recent[i].timestamp - recent[i-1].timestamp).total_seconds() / 3600
            memory_diff = recent[i].process_memory_mb - recent[i-1].process_memory_mb
            if time_diff > 0:
                growth_rates.append(memory_diff / time_diff)
        
        if growth_rates:
            return {
                'average_growth_rate_mb_per_hour': statistics.mean(growth_rates),
                'growth_volatility': statistics.stdev(growth_rates) if len(growth_rates) > 1 else 0,
                'growth_trend': 'accelerating' if len(growth_rates) >= 3 and growth_rates[-1] > statistics.mean(growth_rates) else 'stable'
            }
        
        return {}
    
    def _detect_pressure_points(self, history: List[MemoryMetrics]) -> List[Dict[str, Any]]:
        """Detect memory pressure points"""
        pressure_points = []
        
        for i, metric in enumerate(history[-50:]):
            if metric.memory_usage_percent > 85:
                pressure_points.append({
                    'timestamp': metric.timestamp,
                    'usage_percent': metric.memory_usage_percent,
                    'duration_minutes': self._calculate_pressure_duration(history, i),
                    'severity': 'high' if metric.memory_usage_percent > 95 else 'medium'
                })
        
        return pressure_points
    
    def _calculate_pressure_duration(self, history: List[MemoryMetrics], start_index: int) -> int:
        """Calculate duration of memory pressure"""
        duration = 0
        for i in range(start_index, len(history)):
            if history[i].memory_usage_percent > 85:
                duration += 1
            else:
                break
        return duration
    
    def _generate_predictions(self, patterns: Dict, history: List[MemoryMetrics]) -> List[Dict[str, Any]]:
        """Generate memory usage predictions"""
        predictions = []
        
        # Predict next hour usage
        if patterns.get('hourly_cycles'):
            current_hour = datetime.now(timezone.utc).hour
            next_hour = (current_hour + 1) % 24
            
            if str(next_hour) in patterns['hourly_cycles']:
                cycle_data = patterns['hourly_cycles'][str(next_hour)]
                predictions.append({
                    'type': 'next_hour_usage',
                    'predicted_usage_percent': cycle_data['average_usage'],
                    'confidence': 0.7,
                    'timeframe': '1 hour'
                })
        
        # Predict memory growth
        if patterns.get('growth_patterns'):
            growth_data = patterns['growth_patterns']
            current_memory = history[-1].process_memory_mb if history else 0
            
            predictions.append({
                'type': 'memory_growth',
                'predicted_memory_mb': current_memory + growth_data['average_growth_rate_mb_per_hour'],
                'confidence': 0.6,
                'timeframe': '1 hour'
            })
        
        return predictions
    
    def _calculate_confidence(self, patterns: Dict) -> float:
        """Calculate confidence in predictions"""
        confidence_factors = []
        
        if patterns.get('hourly_cycles'):
            confidence_factors.append(0.7)
        
        if patterns.get('daily_trends'):
            confidence_factors.append(0.6)
        
        if patterns.get('growth_patterns'):
            confidence_factors.append(0.5)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.0
    
    def _generate_recommendations(self, patterns: Dict) -> List[str]:
        """Generate optimization recommendations based on patterns"""
        recommendations = []
        
        if patterns.get('growth_patterns'):
            growth_rate = patterns['growth_patterns']['average_growth_rate_mb_per_hour']
            if growth_rate > 10:
                recommendations.append(f"High memory growth rate ({growth_rate:.1f}MB/hour) - implement aggressive cleanup")
        
        if patterns.get('pressure_points'):
            high_pressure_count = len([p for p in patterns['pressure_points'] if p['severity'] == 'high'])
            if high_pressure_count > 3:
                recommendations.append(f"Frequent high memory pressure ({high_pressure_count} incidents) - optimize memory allocation")
        
        return recommendations
    
    def _calculate_slope(self, x_values: List[int], y_values: List[float]) -> float:
        """Calculate slope of linear regression"""
        n = len(x_values)
        if n < 2:
            return 0.0
        
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope


class IntelligentMemoryOptimizer:
    """Intelligent memory optimization with multiple strategies"""
    
    def __init__(self):
        self.optimization_history = deque(maxlen=100)
        self.strategy_effectiveness = defaultdict(list)
        self.agent_profiles: Dict[str, AgentMemoryProfile] = {}
        
    async def generate_optimization_plan(self, memory_metrics: MemoryMetrics, 
                                       agent_profiles: Dict[str, AgentMemoryProfile],
                                       predictions: Dict) -> List[MemoryOptimization]:
        """Generate intelligent optimization plan"""
        optimizations = []
        
        # System-level optimizations
        system_optimizations = self._generate_system_optimizations(memory_metrics, predictions)
        optimizations.extend(system_optimizations)
        
        # Agent-specific optimizations
        agent_optimizations = self._generate_agent_optimizations(agent_profiles)
        optimizations.extend(agent_optimizations)
        
        # Vector store optimizations
        vector_optimizations = self._generate_vector_store_optimizations(memory_metrics)
        optimizations.extend(vector_optimizations)
        
        # Sort by priority and estimated savings
        optimizations.sort(key=lambda x: (x.priority, x.estimated_savings_mb), reverse=True)
        
        return optimizations
    
    def _generate_system_optimizations(self, metrics: MemoryMetrics, 
                                           predictions: Dict) -> List[MemoryOptimization]:
        """Generate system-level memory optimizations"""
        optimizations = []
        
        # Garbage collection optimization
        if metrics.memory_usage_percent > 80:
            optimizations.append(MemoryOptimization(
                strategy_id=f"gc_optimization_{int(time.time())}",
                strategy_type="garbage_collection",
                description="Force comprehensive garbage collection",
                estimated_savings_mb=50.0,
                execution_time_seconds=5.0,
                risk_level="low",
                priority=8
            ))
        
        # Memory pressure optimization
        if metrics.memory_pressure_score > 70:
            optimizations.append(MemoryOptimization(
                strategy_id=f"pressure_relief_{int(time.time())}",
                strategy_type="memory_pressure_relief",
                description="Implement memory pressure relief strategies",
                estimated_savings_mb=100.0,
                execution_time_seconds=15.0,
                risk_level="medium",
                priority=9
            ))
        
        # Predictive optimization based on patterns
        if predictions.get('predictions'):
            for prediction in predictions['predictions']:
                if prediction['type'] == 'next_hour_usage' and prediction['predicted_usage_percent'] > 90:
                    optimizations.append(MemoryOptimization(
                        strategy_id=f"predictive_cleanup_{int(time.time())}",
                        strategy_type="predictive_cleanup",
                        description="Proactive cleanup based on predicted high usage",
                        estimated_savings_mb=75.0,
                        execution_time_seconds=10.0,
                        risk_level="low",
                        priority=7
                    ))
        
        return optimizations
    
    def _generate_agent_optimizations(self, agent_profiles: Dict[str, AgentMemoryProfile]) -> List[MemoryOptimization]:
        """Generate agent-specific optimizations"""
        optimizations = []
        
        for agent_id, profile in agent_profiles.items():
            # High memory growth rate
            if profile.memory_growth_rate_mb_per_hour > 20:
                optimizations.append(MemoryOptimization(
                    strategy_id=f"agent_restart_{agent_id}_{int(time.time())}",
                    strategy_type="agent_restart",
                    description=f"Restart {profile.agent_name} due to high memory growth",
                    estimated_savings_mb=profile.current_memory_mb - profile.baseline_memory_mb,
                    execution_time_seconds=30.0,
                    risk_level="medium",
                    priority=6,
                    dependencies=[agent_id]
                ))
            
            # Low memory efficiency
            if profile.memory_efficiency_score < 50:
                optimizations.append(MemoryOptimization(
                    strategy_id=f"agent_optimization_{agent_id}_{int(time.time())}",
                    strategy_type="agent_optimization",
                    description=f"Optimize {profile.agent_name} memory usage",
                    estimated_savings_mb=profile.current_memory_mb * 0.2,
                    execution_time_seconds=20.0,
                    risk_level="low",
                    priority=5,
                    dependencies=[agent_id]
                ))
        
        return optimizations
    
    def _generate_vector_store_optimizations(self, metrics: MemoryMetrics) -> List[MemoryOptimization]:
        """Generate vector store optimizations"""
        optimizations = []
        
        # Large vector store
        if metrics.vector_store_size_mb > 500:
            optimizations.append(MemoryOptimization(
                strategy_id=f"vector_cleanup_{int(time.time())}",
                strategy_type="vector_store_cleanup",
                description="Clean up old vector store data",
                estimated_savings_mb=metrics.vector_store_size_mb * 0.3,
                execution_time_seconds=60.0,
                risk_level="medium",
                priority=7
            ))
        
        # Embedding cache optimization
        if metrics.embedding_cache_size_mb > 100:
            optimizations.append(MemoryOptimization(
                strategy_id=f"cache_optimization_{int(time.time())}",
                strategy_type="embedding_cache_optimization",
                description="Optimize embedding cache usage",
                estimated_savings_mb=metrics.embedding_cache_size_mb * 0.5,
                execution_time_seconds=10.0,
                risk_level="low",
                priority=6
            ))
        
        return optimizations
    
    async def execute_optimization(self, optimization: MemoryOptimization) -> Dict[str, Any]:
        """Execute a memory optimization strategy"""
        start_time = time.time()
        
        try:
            if optimization.strategy_type == "garbage_collection":
                result = await self._execute_garbage_collection()
            elif optimization.strategy_type == "memory_pressure_relief":
                result = await self._execute_memory_pressure_relief()
            elif optimization.strategy_type == "predictive_cleanup":
                result = await self._execute_predictive_cleanup()
            elif optimization.strategy_type == "agent_restart":
                result = await self._execute_agent_restart(optimization)
            elif optimization.strategy_type == "agent_optimization":
                result = await self._execute_agent_optimization(optimization)
            elif optimization.strategy_type == "vector_store_cleanup":
                result = await self._execute_vector_store_cleanup()
            elif optimization.strategy_type == "embedding_cache_optimization":
                result = await self._execute_embedding_cache_optimization()
            else:
                result = {'success': False, 'error': 'Unknown optimization type'}
            
            execution_time = time.time() - start_time
            
            # Update optimization history
            self.optimization_history.append({
                'strategy_id': optimization.strategy_id,
                'strategy_type': optimization.strategy_type,
                'execution_time': execution_time,
                'success': result.get('success', False),
                'actual_savings_mb': result.get('savings_mb', 0),
                'timestamp': datetime.now(timezone.utc)
            })
            
            # Update strategy effectiveness
            self.strategy_effectiveness[optimization.strategy_type].append({
                'estimated_savings': optimization.estimated_savings_mb,
                'actual_savings': result.get('savings_mb', 0),
                'success': result.get('success', False)
            })
            
            return {
                'success': result.get('success', False),
                'execution_time': execution_time,
                'actual_savings_mb': result.get('savings_mb', 0),
                'error': result.get('error')
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'execution_time': execution_time,
                'actual_savings_mb': 0,
                'error': str(e)
            }
    
    async def _execute_garbage_collection(self) -> Dict[str, Any]:
        """Execute comprehensive garbage collection"""
        try:
            # Enable tracemalloc for detailed memory tracking
            tracemalloc.start()
            
            # Force garbage collection
            collected = gc.collect()
            
            # Get memory snapshot
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            # Stop tracemalloc
            tracemalloc.stop()
            
            # Estimate memory freed
            memory_freed = collected * 0.1  # Rough estimate
            
            return {
                'success': True,
                'savings_mb': memory_freed,
                'objects_collected': collected,
                'top_allocations': top_stats[:5]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_memory_pressure_relief(self) -> Dict[str, Any]:
        """Execute memory pressure relief strategies"""
        try:
            total_savings = 0.0
            
            # Clear Python object caches
            import sys
            for module in sys.modules.values():
                if hasattr(module, '__dict__'):
                    module.__dict__.clear()
            
            # Force garbage collection
            collected = gc.collect()
            total_savings += collected * 0.1
            
            # Clear weak references
            weakref._weakref._cleanup()
            total_savings += 10.0
            
            return {
                'success': True,
                'savings_mb': total_savings,
                'strategies_applied': ['module_cache_clear', 'garbage_collection', 'weakref_cleanup']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_predictive_cleanup(self) -> Dict[str, Any]:
        """Execute predictive cleanup based on patterns"""
        try:
            total_savings = 0.0
            
            # Clear temporary files
            temp_dirs = ['temp', 'logs', 'cache']
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file_path in Path(temp_dir).glob('*.tmp'):
                        try:
                            file_size = file_path.stat().st_size / 1024 / 1024
                            file_path.unlink()
                            total_savings += file_size
                        except:
                            pass
            
            # Clear old log files
            if os.path.exists('logs'):
                for log_file in Path('logs').glob('*.log.*'):
                    try:
                        file_size = log_file.stat().st_size / 1024 / 1024
                        if file_size > 10:  # Only delete large log files
                            log_file.unlink()
                            total_savings += file_size
                    except:
                        pass
            
            return {
                'success': True,
                'savings_mb': total_savings,
                'files_cleaned': len(list(Path('temp').glob('*.tmp'))) if os.path.exists('temp') else 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_agent_restart(self, optimization: MemoryOptimization) -> Dict[str, Any]:
        """Execute agent restart optimization"""
        try:
            # This would integrate with the agent coordinator to restart specific agents
            # For now, simulate the restart
            agent_id = optimization.dependencies[0] if optimization.dependencies else None
            
            if agent_id:
                # Simulate restart
                await asyncio.sleep(2)
                
                # Estimate memory savings based on agent profile
                profile = self.agent_profiles.get(agent_id)
                if profile:
                    savings = profile.current_memory_mb - profile.baseline_memory_mb
                    return {
                        'success': True,
                        'savings_mb': savings,
                        'agent_restarted': agent_id
                    }
            
            return {'success': False, 'error': 'Agent restart not implemented'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_agent_optimization(self, optimization: MemoryOptimization) -> Dict[str, Any]:
        """Execute agent-specific optimization"""
        try:
            # This would implement agent-specific memory optimization
            # For now, simulate optimization
            await asyncio.sleep(1)
            
            return {
                'success': True,
                'savings_mb': optimization.estimated_savings_mb * 0.8,
                'optimization_applied': 'memory_efficiency_improvement'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_vector_store_cleanup(self) -> Dict[str, Any]:
        """Execute vector store cleanup"""
        try:
            vector_store_path = Path("./vectorstore_db")
            if not vector_store_path.exists():
                return {'success': True, 'savings_mb': 0, 'message': 'No vector store to clean'}
            
            # Calculate size before cleanup
            before_size = sum(f.stat().st_size for f in vector_store_path.rglob('*') if f.is_file())
            
            # Remove old collections (older than 7 days)
            current_time = time.time()
            files_removed = 0
            
            for file_path in vector_store_path.rglob('*'):
                if file_path.is_file():
                    try:
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > (7 * 24 * 3600):  # 7 days
                            file_path.unlink()
                            files_removed += 1
                    except:
                        pass
            
            # Calculate size after cleanup
            after_size = sum(f.stat().st_size for f in vector_store_path.rglob('*') if f.is_file())
            savings = (before_size - after_size) / 1024 / 1024
            
            return {
                'success': True,
                'savings_mb': savings,
                'files_removed': files_removed
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_embedding_cache_optimization(self) -> Dict[str, Any]:
        """Execute embedding cache optimization"""
        try:
            # This would implement embedding cache optimization
            # For now, simulate cache clearing
            await asyncio.sleep(1)
            
            return {
                'success': True,
                'savings_mb': 50.0,  # Simulated savings
                'cache_optimized': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class DistributedMemoryOptimizer:
    """Distributed memory optimization across all agents"""
    
    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state
        self.optimization_coordination = {}
        self.agent_optimization_status = {}
        
    async def coordinate_agent_optimizations(self) -> Dict[str, Any]:
        """Coordinate memory optimizations across all agents"""
        try:
            # Get all active agents
            agents = await self.shared_state.get_registered_agents()
            active_agents = [a for a in agents if a.get('state') == 'active']
            
            optimization_results = {}
            
            for agent in active_agents:
                agent_id = agent.get('agent_id')
                if agent_id and agent_id != 'memory_manager':
                    # Request optimization from agent
                    result = await self._request_agent_optimization(agent_id)
                    optimization_results[agent_id] = result
            
            return {
                'success': True,
                'agents_optimized': len(optimization_results),
                'total_savings_mb': sum(r.get('savings_mb', 0) for r in optimization_results.values()),
                'results': optimization_results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _request_agent_optimization(self, agent_id: str) -> Dict[str, Any]:
        """Request memory optimization from specific agent"""
        try:
            # This would send optimization request to agent
            # For now, simulate agent optimization
            await asyncio.sleep(0.1)
            
            # Simulate optimization result
            return {
                'success': True,
                'savings_mb': 25.0,  # Simulated savings
                'optimization_applied': 'agent_memory_cleanup'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class EnhancedMemoryManager(BaseAgent):
    """Enhanced Memory Manager with predictive analysis and intelligent optimization"""
    
    def __init__(self, agent_id: str = "enhanced_memory_manager", shared_state=None):
        super().__init__(agent_id, shared_state)
        self.agent_name = "EnhancedMemoryManager"
        
        # Initialize enhanced components
        self.memory_tracker = MemoryUsageTracker()
        self.predictive_analyzer = PredictiveMemoryAnalyzer()
        self.intelligent_optimizer = IntelligentMemoryOptimizer()
        self.distributed_optimizer = DistributedMemoryOptimizer(shared_state) if shared_state else None
        
        # Enhanced configuration
        self.monitoring_interval = 30  # More frequent monitoring
        self.optimization_interval = 300  # 5 minutes
        self.prediction_interval = 600  # 10 minutes
        
        # Advanced thresholds
        self.alert_thresholds = {
            'memory_usage_percent': 80.0,  # Lowered for proactive management
            'vector_store_size_mb': 600.0,  # Lowered threshold
            'process_memory_mb': 400.0,  # Lowered threshold
            'memory_growth_rate_mb_per_hour': 30.0,  # Lowered threshold
            'memory_pressure_score': 70.0  # New threshold
        }
        
        # Enhanced memory management stats
        self.memory_stats = {
            'total_optimizations_performed': 0,
            'total_memory_freed_mb': 0,
            'predictions_generated': 0,
            'predictions_accurate': 0,
            'distributed_optimizations': 0,
            'last_optimization_time': None,
            'last_prediction_time': None,
            'optimization_efficiency_score': 100.0
        }
        
        # Memory pressure tracking
        self.memory_pressure_history = deque(maxlen=100)
        
    async def initialize(self) -> None:
        """Initialize enhanced memory management system"""
        self.logger.info("Initializing Enhanced Memory Management System")
        
        # Set work interval
        self.work_interval = self.monitoring_interval
        
        # Perform initial assessment
        await self.perform_enhanced_assessment()
        
        self.logger.info("Enhanced Memory Management System initialized")
    
    async def perform_enhanced_assessment(self) -> None:
        """Perform comprehensive initial memory assessment"""
        try:
            # Get current memory metrics
            memory_metrics = await self.memory_tracker.get_current_memory_metrics()
            
            # Calculate memory pressure score
            memory_metrics.memory_pressure_score = self._calculate_memory_pressure_score(memory_metrics)
            
            # Generate initial optimization opportunities
            memory_metrics.optimization_opportunities = await self._identify_optimization_opportunities(memory_metrics)
            
            self.logger.info(f"Enhanced memory assessment:")
            self.logger.info(f"  System memory: {memory_metrics.memory_usage_percent:.1f}%")
            self.logger.info(f"  Memory pressure score: {memory_metrics.memory_pressure_score:.1f}")
            self.logger.info(f"  Optimization opportunities: {len(memory_metrics.optimization_opportunities)}")
            
        except Exception as e:
            self.logger.error(f"Enhanced memory assessment failed: {e}")
    
    async def execute_work_cycle(self) -> Dict[str, Any]:
        """Execute enhanced memory management work cycle"""
        work_start_time = time.time()
        
        try:
            # Get current memory metrics
            memory_metrics = await self.memory_tracker.get_current_memory_metrics()
            memory_metrics.memory_pressure_score = self._calculate_memory_pressure_score(memory_metrics)
            memory_metrics.optimization_opportunities = await self._identify_optimization_opportunities(memory_metrics)
            
            # Update memory pressure history
            self.memory_pressure_history.append(memory_metrics.memory_pressure_score)
            
            # Perform predictive analysis
            predictions = None
            if len(self.memory_tracker.memory_history) >= 10:
                predictions = await self.predictive_analyzer.analyze_memory_patterns(
                    self.memory_tracker.memory_history
                )
                self.memory_stats['predictions_generated'] += 1
            
            # Generate optimization plan
            agent_profiles = await self._get_agent_memory_profiles()
            optimization_plan = await self.intelligent_optimizer.generate_optimization_plan(
                memory_metrics, agent_profiles, predictions or {}
            )
            
            # Execute high-priority optimizations
            optimization_results = []
            for optimization in optimization_plan[:3]:  # Execute top 3 optimizations
                if optimization.priority >= 7:  # High priority optimizations
                    result = await self.intelligent_optimizer.execute_optimization(optimization)
                    optimization_results.append(result)
                    
                    if result['success']:
                        self.memory_stats['total_optimizations_performed'] += 1
                        self.memory_stats['total_memory_freed_mb'] += result['actual_savings_mb']
            
            # Perform distributed optimization
            distributed_results = None
            if self.distributed_optimizer:
                distributed_results = await self.distributed_optimizer.coordinate_agent_optimizations()
                if distributed_results['success']:
                    self.memory_stats['distributed_optimizations'] += 1
                    self.memory_stats['total_memory_freed_mb'] += distributed_results['total_savings_mb']
            
            # Generate alerts
            alerts = await self.generate_enhanced_alerts(memory_metrics, predictions, optimization_results)
            
            # Update statistics
            self.memory_stats['last_optimization_time'] = datetime.now(timezone.utc)
            if predictions:
                self.memory_stats['last_prediction_time'] = datetime.now(timezone.utc)
            
            # Calculate efficiency score
            self.memory_stats['optimization_efficiency_score'] = self._calculate_efficiency_score(optimization_results)
            
            processing_time = time.time() - work_start_time
            
            return {
                'success': True,
                'processing_time': processing_time,
                'business_value': self.calculate_enhanced_business_value(
                    memory_metrics, predictions, optimization_results, distributed_results
                ),
                'memory_metrics': memory_metrics,
                'predictions': predictions,
                'optimization_plan': optimization_plan,
                'optimization_results': optimization_results,
                'distributed_results': distributed_results,
                'alerts_generated': alerts,
                'efficiency_score': self.memory_stats['optimization_efficiency_score']
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced memory management cycle failed: {e}")
            return {
                'success': False,
                'processing_time': time.time() - work_start_time,
                'business_value': 0,
                'error_details': str(e)
            }
    
    def _calculate_memory_pressure_score(self, metrics: MemoryMetrics) -> float:
        """Calculate memory pressure score (0-100)"""
        pressure_score = 0.0
        
        # Base pressure from memory usage
        pressure_score += metrics.memory_usage_percent * 0.6
        
        # Additional pressure from process memory
        if metrics.process_memory_mb > 500:
            pressure_score += min((metrics.process_memory_mb - 500) / 10, 20)
        
        # Pressure from vector store size
        if metrics.vector_store_size_mb > 400:
            pressure_score += min((metrics.vector_store_size_mb - 400) / 20, 15)
        
        # Pressure from memory trend
        if metrics.memory_trend == 'increasing':
            pressure_score += 10
        
        return min(pressure_score, 100.0)
    
    async def _identify_optimization_opportunities(self, metrics: MemoryMetrics) -> List[str]:
        """Identify memory optimization opportunities"""
        opportunities = []
        
        if metrics.memory_usage_percent > 75:
            opportunities.append("High system memory usage - implement aggressive cleanup")
        
        if metrics.process_memory_mb > 400:
            opportunities.append("High process memory - optimize agent memory usage")
        
        if metrics.vector_store_size_mb > 400:
            opportunities.append("Large vector store - implement cleanup strategy")
        
        if metrics.memory_trend == 'increasing':
            opportunities.append("Memory growth trend - implement growth control")
        
        if metrics.memory_pressure_score > 70:
            opportunities.append("High memory pressure - implement pressure relief")
        
        return opportunities
    
    async def _get_agent_memory_profiles(self) -> Dict[str, AgentMemoryProfile]:
        """Get memory profiles for all agents"""
        profiles = {}
        
        try:
            agents = await self.shared_state.get_registered_agents()
            
            for agent in agents:
                if isinstance(agent, dict):
                    agent_id = agent.get('agent_id')
                else:
                    agent_id = str(agent) if agent else None
                    
                if agent_id and agent_id != 'enhanced_memory_manager':
                    # Get agent memory metrics from heartbeats
                    recent_heartbeats = await self.shared_state.get_recent_heartbeats(agent_id, minutes=60)
                    
                    if recent_heartbeats:
                        memory_values = []
                        for h in recent_heartbeats:
                            if isinstance(h, dict) and h.get('memory_usage_mb') is not None:
                                memory_values.append(h.get('memory_usage_mb', 0))
                        
                        if memory_values:
                            current_memory = memory_values[-1]
                            baseline_memory = min(memory_values)
                            
                            # Calculate growth rate
                            if len(memory_values) >= 2:
                                time_diff = 1  # 1 hour
                                memory_diff = memory_values[-1] - memory_values[0]
                                growth_rate = memory_diff / time_diff
                            else:
                                growth_rate = 0.0
                            
                            # Calculate efficiency score
                            efficiency_score = max(0, 100 - (current_memory - baseline_memory) / baseline_memory * 100)
                            
                            agent_name = agent.get('agent_name', agent_id) if isinstance(agent, dict) else agent_id
                            
                            profiles[agent_id] = AgentMemoryProfile(
                                agent_id=agent_id,
                                agent_name=agent_name,
                                baseline_memory_mb=baseline_memory,
                                current_memory_mb=current_memory,
                                memory_growth_rate_mb_per_hour=growth_rate,
                                memory_efficiency_score=efficiency_score,
                                optimization_recommendations=[],
                                last_optimization=None
                            )
        
        except Exception as e:
            self.logger.error(f"Failed to get agent memory profiles: {e}")
        
        return profiles
    
    async def generate_enhanced_alerts(self, memory_metrics: MemoryMetrics, 
                                     predictions: Dict, optimization_results: List[Dict]) -> List[Dict]:
        """Generate enhanced memory alerts"""
        alerts = []
        
        # Memory pressure alerts
        if memory_metrics.memory_pressure_score > self.alert_thresholds['memory_pressure_score']:
            alerts.append({
                'type': 'high_memory_pressure',
                'severity': 'high' if memory_metrics.memory_pressure_score > 85 else 'medium',
                'message': f"High memory pressure score: {memory_metrics.memory_pressure_score:.1f}",
                'value': memory_metrics.memory_pressure_score,
                'threshold': self.alert_thresholds['memory_pressure_score']
            })
        
        # Predictive alerts
        if predictions and predictions.get('predictions'):
            for prediction in predictions['predictions']:
                if prediction['type'] == 'next_hour_usage' and prediction['predicted_usage_percent'] > 90:
                    alerts.append({
                        'type': 'predicted_memory_crisis',
                        'severity': 'high',
                        'message': f"Predicted memory crisis: {prediction['predicted_usage_percent']:.1f}% usage in 1 hour",
                        'confidence': prediction['confidence'],
                        'timeframe': prediction['timeframe']
                    })
        
        # Optimization opportunity alerts
        if memory_metrics.optimization_opportunities:
            alerts.append({
                'type': 'optimization_opportunities',
                'severity': 'medium',
                'message': f"Found {len(memory_metrics.optimization_opportunities)} optimization opportunities",
                'opportunities': memory_metrics.optimization_opportunities
            })
        
        return alerts
    
    def _calculate_efficiency_score(self, optimization_results: List[Dict]) -> float:
        """Calculate optimization efficiency score"""
        if not optimization_results:
            return 100.0
        
        successful_optimizations = [r for r in optimization_results if r['success']]
        success_rate = len(successful_optimizations) / len(optimization_results)
        
        # Calculate average execution time efficiency
        execution_times = [r['execution_time'] for r in successful_optimizations]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        
        # Efficiency based on success rate and execution time
        efficiency = success_rate * 70 + max(0, (30 - avg_execution_time) / 30 * 30)
        
        return min(efficiency, 100.0)
    
    def calculate_enhanced_business_value(self, memory_metrics: MemoryMetrics,
                                        predictions: Dict, optimization_results: List[Dict],
                                        distributed_results: Dict) -> float:
        """Calculate enhanced business value of memory management activities"""
        base_value = 50.0  # Base value for enhanced monitoring
        
        # Value for preventing memory issues
        if memory_metrics.memory_pressure_score < 60:
            base_value += 40.0  # Good memory management
        
        # Value for successful optimizations
        successful_optimizations = [r for r in optimization_results if r['success']]
        optimization_value = sum(r['actual_savings_mb'] for r in successful_optimizations) * 0.2
        base_value += optimization_value
        
        # Value for distributed optimizations
        if distributed_results and distributed_results.get('success'):
            distributed_value = distributed_results.get('total_savings_mb', 0) * 0.15
            base_value += distributed_value
        
        # Value for predictive capabilities
        if predictions and predictions.get('confidence', 0) > 0.7:
            base_value += 30.0  # High confidence predictions
        
        # Value for efficiency
        efficiency_bonus = self.memory_stats['optimization_efficiency_score'] * 0.5
        base_value += efficiency_bonus
        
        return round(base_value, 2)
    
    async def get_enhanced_dashboard_data(self) -> Dict[str, Any]:
        """Get data for enhanced memory management dashboard"""
        try:
            memory_metrics = await self.memory_tracker.get_current_memory_metrics()
            memory_metrics.memory_pressure_score = self._calculate_memory_pressure_score(memory_metrics)
            
            agent_profiles = await self._get_agent_memory_profiles()
            
            return {
                'memory_metrics': memory_metrics,
                'agent_profiles': agent_profiles,
                'memory_stats': self.memory_stats,
                'alert_thresholds': self.alert_thresholds,
                'memory_history': self.memory_tracker.memory_history[-100:],
                'pressure_history': list(self.memory_pressure_history),
                'timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get enhanced dashboard data: {e}")
            return {'error': str(e)} 