"""
Memory Management System for AI Help Agent Platform

Comprehensive memory monitoring, optimization, and cleanup system
for vector stores, embeddings, and system resources.
"""

import asyncio
import logging
import time
import psutil
import gc
import os
import shutil
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path
import statistics

from ..coordination.base_agent import BaseAgent
from ..coordination.shared_state import SharedState


@dataclass
class MemoryMetrics:
    """Memory usage metrics data structure"""
    timestamp: datetime
    total_memory_mb: float
    available_memory_mb: float
    memory_usage_percent: float
    vector_store_size_mb: float
    embedding_cache_size_mb: float
    process_memory_mb: float
    memory_trend: str = 'stable'  # increasing, decreasing, stable


@dataclass
class VectorStoreMetrics:
    """Vector store size and performance metrics"""
    timestamp: datetime
    total_documents: int
    total_collections: int
    storage_size_mb: float
    embeddings_count: int
    average_embedding_size_kb: float
    oldest_document_age_hours: float
    newest_document_age_hours: float


class MemoryUsageTracker:
    """Tracks system and process memory usage"""
    
    def __init__(self):
        self.memory_history: List[MemoryMetrics] = []
        self.max_history_size = 1000
        self.trend_window = 10  # Number of samples for trend analysis
        
    async def get_current_memory_metrics(self) -> MemoryMetrics:
        """Get current memory usage metrics"""
        try:
            # System memory
            system_memory = psutil.virtual_memory()
            
            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Vector store size (estimate)
            vector_store_size = await self._estimate_vector_store_size()
            
            # Embedding cache size (estimate)
            embedding_cache_size = await self._estimate_embedding_cache_size()
            
            # Calculate memory trend
            memory_trend = self._calculate_memory_trend()
            
            metrics = MemoryMetrics(
                timestamp=datetime.now(timezone.utc),
                total_memory_mb=system_memory.total / 1024 / 1024,
                available_memory_mb=system_memory.available / 1024 / 1024,
                memory_usage_percent=system_memory.percent,
                vector_store_size_mb=vector_store_size,
                embedding_cache_size_mb=embedding_cache_size,
                process_memory_mb=process_memory,
                memory_trend=memory_trend
            )
            
            # Store in history
            self.memory_history.append(metrics)
            if len(self.memory_history) > self.max_history_size:
                self.memory_history = self.memory_history[-self.max_history_size:]
            
            return metrics
            
        except Exception as e:
            logging.error(f"Failed to get memory metrics: {e}")
            return MemoryMetrics(
                timestamp=datetime.now(timezone.utc),
                total_memory_mb=0,
                available_memory_mb=0,
                memory_usage_percent=0,
                vector_store_size_mb=0,
                embedding_cache_size_mb=0,
                process_memory_mb=0,
                memory_trend='unknown'
            )
    
    async def _estimate_vector_store_size(self) -> float:
        """Estimate vector store size on disk"""
        try:
            vector_store_path = Path("./vectorstore_db")
            if not vector_store_path.exists():
                return 0.0
            
            total_size = 0
            for file_path in vector_store_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size / 1024 / 1024  # Convert to MB
            
        except Exception as e:
            logging.error(f"Failed to estimate vector store size: {e}")
            return 0.0
    
    async def _estimate_embedding_cache_size(self) -> float:
        """Estimate embedding cache size in memory"""
        try:
            # This is a rough estimate based on typical embedding sizes
            # In a real implementation, you'd track actual cache usage
            return 50.0  # MB estimate
            
        except Exception as e:
            logging.error(f"Failed to estimate embedding cache size: {e}")
            return 0.0
    
    def _calculate_memory_trend(self) -> str:
        """Calculate memory usage trend"""
        if len(self.memory_history) < self.trend_window:
            return 'stable'
        
        recent_metrics = self.memory_history[-self.trend_window:]
        memory_values = [m.memory_usage_percent for m in recent_metrics]
        
        if len(memory_values) < 2:
            return 'stable'
        
        # Calculate trend using linear regression
        x_values = list(range(len(memory_values)))
        slope = self._calculate_slope(x_values, memory_values)
        
        if slope > 1.0:  # More than 1% increase per sample
            return 'increasing'
        elif slope < -1.0:  # More than 1% decrease per sample
            return 'decreasing'
        else:
            return 'stable'
    
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


class MemoryLeakDetector:
    """Detects potential memory leaks in the system"""
    
    def __init__(self):
        self.leak_threshold = 20.0  # MB increase threshold
        self.trend_window = 20  # Number of samples to analyze
        self.detection_history: List[Dict] = []
        
    async def detect_memory_leaks(self, memory_history: List[MemoryMetrics]) -> List[Dict]:
        """Detect potential memory leaks"""
        leaks = []
        
        if len(memory_history) < self.trend_window:
            return leaks
        
        # Analyze process memory trend
        process_memory_trend = await self._analyze_process_memory_trend(memory_history)
        if process_memory_trend['leak_detected']:
            leaks.append(process_memory_trend)
        
        # Analyze vector store growth
        vector_store_trend = await self._analyze_vector_store_trend(memory_history)
        if vector_store_trend['leak_detected']:
            leaks.append(vector_store_trend)
        
        # Analyze overall memory usage
        overall_trend = await self._analyze_overall_memory_trend(memory_history)
        if overall_trend['leak_detected']:
            leaks.append(overall_trend)
        
        return leaks
    
    async def _analyze_process_memory_trend(self, memory_history: List[MemoryMetrics]) -> Dict:
        """Analyze process memory for leaks"""
        recent_metrics = memory_history[-self.trend_window:]
        process_memory_values = [m.process_memory_mb for m in recent_metrics]
        
        if len(process_memory_values) < 5:
            return {'leak_detected': False}
        
        # Calculate growth rate
        initial_memory = process_memory_values[0]
        final_memory = process_memory_values[-1]
        memory_growth = final_memory - initial_memory
        
        # Calculate trend
        x_values = list(range(len(process_memory_values)))
        slope = self._calculate_slope(x_values, process_memory_values)
        
        leak_detected = memory_growth > self.leak_threshold and slope > 0.5
        
        return {
            'leak_detected': leak_detected,
            'leak_type': 'process_memory',
            'growth_mb': memory_growth,
            'growth_rate_mb_per_sample': slope,
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'severity': 'high' if memory_growth > 50 else 'medium' if memory_growth > 20 else 'low'
        }
    
    async def _analyze_vector_store_trend(self, memory_history: List[MemoryMetrics]) -> Dict:
        """Analyze vector store growth for potential issues"""
        recent_metrics = memory_history[-self.trend_window:]
        vector_store_values = [m.vector_store_size_mb for m in recent_metrics]
        
        if len(vector_store_values) < 5:
            return {'leak_detected': False}
        
        # Calculate growth rate
        initial_size = vector_store_values[0]
        final_size = vector_store_values[-1]
        size_growth = final_size - initial_size
        
        # Calculate trend
        x_values = list(range(len(vector_store_values)))
        slope = self._calculate_slope(x_values, vector_store_values)
        
        # Vector store growth is expected, but excessive growth might indicate issues
        leak_detected = size_growth > 100 and slope > 2.0  # 100MB growth threshold
        
        return {
            'leak_detected': leak_detected,
            'leak_type': 'vector_store_growth',
            'growth_mb': size_growth,
            'growth_rate_mb_per_sample': slope,
            'initial_size_mb': initial_size,
            'final_size_mb': final_size,
            'severity': 'high' if size_growth > 500 else 'medium' if size_growth > 200 else 'low'
        }
    
    async def _analyze_overall_memory_trend(self, memory_history: List[MemoryMetrics]) -> Dict:
        """Analyze overall system memory usage"""
        recent_metrics = memory_history[-self.trend_window:]
        memory_usage_values = [m.memory_usage_percent for m in recent_metrics]
        
        if len(memory_usage_values) < 5:
            return {'leak_detected': False}
        
        # Check if memory usage is consistently high
        avg_usage = statistics.mean(memory_usage_values)
        max_usage = max(memory_usage_values)
        
        # Calculate trend
        x_values = list(range(len(memory_usage_values)))
        slope = self._calculate_slope(x_values, memory_usage_values)
        
        leak_detected = avg_usage > 85 or (max_usage > 90 and slope > 0.5)
        
        return {
            'leak_detected': leak_detected,
            'leak_type': 'system_memory',
            'average_usage_percent': avg_usage,
            'max_usage_percent': max_usage,
            'trend_slope': slope,
            'severity': 'high' if max_usage > 95 else 'medium' if max_usage > 90 else 'low'
        }
    
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


class VectorStoreManager:
    """Manages vector store size and cleanup operations"""
    
    def __init__(self, vector_store_path: str = "./vectorstore_db"):
        self.vector_store_path = Path(vector_store_path)
        self.max_size_mb = 1000  # 1GB default limit
        self.cleanup_threshold = 0.8  # Cleanup when 80% full
        self.retention_days = 30  # Keep documents for 30 days
        
    async def get_vector_store_metrics(self) -> VectorStoreMetrics:
        """Get comprehensive vector store metrics"""
        try:
            if not self.vector_store_path.exists():
                return VectorStoreMetrics(
                    timestamp=datetime.now(timezone.utc),
                    total_documents=0,
                    total_collections=0,
                    storage_size_mb=0,
                    embeddings_count=0,
                    average_embedding_size_kb=0,
                    oldest_document_age_hours=0,
                    newest_document_age_hours=0
                )
            
            # Calculate storage size
            total_size = 0
            file_count = 0
            for file_path in self.vector_store_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            storage_size_mb = total_size / 1024 / 1024
            
            # Estimate document count (rough estimate based on file structure)
            total_documents = await self._estimate_document_count()
            
            # Estimate collections count
            total_collections = len([d for d in self.vector_store_path.iterdir() if d.is_dir()])
            
            # Estimate embeddings count
            embeddings_count = total_documents  # Rough estimate
            
            # Calculate average embedding size
            average_embedding_size_kb = (storage_size_mb * 1024) / max(embeddings_count, 1)
            
            # Calculate document ages (rough estimate)
            oldest_document_age_hours = 24 * 30  # 30 days default
            newest_document_age_hours = 1  # 1 hour default
            
            return VectorStoreMetrics(
                timestamp=datetime.now(timezone.utc),
                total_documents=total_documents,
                total_collections=total_collections,
                storage_size_mb=storage_size_mb,
                embeddings_count=embeddings_count,
                average_embedding_size_kb=average_embedding_size_kb,
                oldest_document_age_hours=oldest_document_age_hours,
                newest_document_age_hours=newest_document_age_hours
            )
            
        except Exception as e:
            logging.error(f"Failed to get vector store metrics: {e}")
            return VectorStoreMetrics(
                timestamp=datetime.now(timezone.utc),
                total_documents=0,
                total_collections=0,
                storage_size_mb=0,
                embeddings_count=0,
                average_embedding_size_kb=0,
                oldest_document_age_hours=0,
                newest_document_age_hours=0
            )
    
    async def _estimate_document_count(self) -> int:
        """Estimate total number of documents in vector store"""
        try:
            # This is a rough estimate based on file structure
            # In a real implementation, you'd query the vector store directly
            total_files = 0
            for file_path in self.vector_store_path.rglob("*.bin"):
                total_files += 1
            
            # Rough estimate: each document has multiple files
            return total_files // 4  # Assuming 4 files per document
            
        except Exception as e:
            logging.error(f"Failed to estimate document count: {e}")
            return 0
    
    async def check_cleanup_needed(self) -> Dict[str, Any]:
        """Check if vector store cleanup is needed"""
        metrics = await self.get_vector_store_metrics()
        
        cleanup_needed = False
        reason = ""
        
        # Check size threshold
        if metrics.storage_size_mb > (self.max_size_mb * self.cleanup_threshold):
            cleanup_needed = True
            reason = f"Storage size ({metrics.storage_size_mb:.1f}MB) exceeds threshold ({self.max_size_mb * self.cleanup_threshold:.1f}MB)"
        
        # Check age threshold
        if metrics.oldest_document_age_hours > (self.retention_days * 24):
            cleanup_needed = True
            reason = f"Documents older than {self.retention_days} days detected"
        
        return {
            'cleanup_needed': cleanup_needed,
            'reason': reason,
            'current_size_mb': metrics.storage_size_mb,
            'size_threshold_mb': self.max_size_mb * self.cleanup_threshold,
            'oldest_document_age_hours': metrics.oldest_document_age_hours,
            'retention_threshold_hours': self.retention_days * 24
        }
    
    async def perform_cleanup(self) -> Dict[str, Any]:
        """Perform vector store cleanup"""
        try:
            cleanup_start = time.time()
            
            # Get current metrics
            before_metrics = await self.get_vector_store_metrics()
            
            # Perform cleanup operations
            cleanup_results = await self._cleanup_old_documents()
            size_cleanup_results = await self._cleanup_by_size()
            
            # Get metrics after cleanup
            after_metrics = await self.get_vector_store_metrics()
            
            cleanup_time = time.time() - cleanup_start
            size_reduction = before_metrics.storage_size_mb - after_metrics.storage_size_mb
            
            return {
                'success': True,
                'cleanup_time_seconds': cleanup_time,
                'size_reduction_mb': size_reduction,
                'documents_removed': before_metrics.total_documents - after_metrics.total_documents,
                'before_metrics': before_metrics,
                'after_metrics': after_metrics,
                'cleanup_details': {
                    'age_cleanup': cleanup_results,
                    'size_cleanup': size_cleanup_results
                }
            }
            
        except Exception as e:
            logging.error(f"Vector store cleanup failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'cleanup_time_seconds': 0,
                'size_reduction_mb': 0,
                'documents_removed': 0
            }
    
    async def _cleanup_old_documents(self) -> Dict[str, Any]:
        """Clean up documents older than retention period"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you'd query the vector store for old documents
            # and remove them based on timestamps
            
            return {
                'documents_removed': 0,
                'size_freed_mb': 0,
                'oldest_document_removed_hours': 0
            }
            
        except Exception as e:
            logging.error(f"Age-based cleanup failed: {e}")
            return {'error': str(e)}
    
    async def _cleanup_by_size(self) -> Dict[str, Any]:
        """Clean up documents to reduce storage size"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you'd implement LRU-based cleanup
            
            return {
                'documents_removed': 0,
                'size_freed_mb': 0,
                'cleanup_strategy': 'lru'
            }
            
        except Exception as e:
            logging.error(f"Size-based cleanup failed: {e}")
            return {'error': str(e)}


class MemoryManager(BaseAgent):
    """Comprehensive memory management agent"""
    
    def __init__(self, agent_id: str = "memory_manager", shared_state=None):
        super().__init__(agent_id, shared_state)
        self.agent_name = "MemoryManager"
        
        # Initialize components
        self.memory_tracker = MemoryUsageTracker()
        self.leak_detector = MemoryLeakDetector()
        self.vector_store_manager = VectorStoreManager()
        
        # Configuration
        self.monitoring_interval = 60  # seconds
        self.alert_thresholds = {
            'memory_usage_percent': 85.0,
            'vector_store_size_mb': 800.0,
            'process_memory_mb': 500.0,
            'memory_growth_rate_mb_per_hour': 50.0
        }
        
        # Memory management stats
        self.memory_stats = {
            'total_cleanups_performed': 0,
            'total_memory_freed_mb': 0,
            'leaks_detected': 0,
            'alerts_generated': 0,
            'last_cleanup_time': None,
            'last_leak_detection_time': None
        }
        
    async def initialize(self) -> None:
        """Initialize memory management system"""
        self.logger.info("Initializing Memory Management System")
        
        # Set work interval
        self.work_interval = self.monitoring_interval
        
        # Perform initial memory assessment
        await self.perform_initial_assessment()
        
        self.logger.info("Memory Management System initialized")
    
    async def perform_initial_assessment(self) -> None:
        """Perform initial memory assessment"""
        try:
            # Get current memory metrics
            memory_metrics = await self.memory_tracker.get_current_memory_metrics()
            vector_store_metrics = await self.vector_store_manager.get_vector_store_metrics()
            
            self.logger.info(f"Initial memory assessment:")
            self.logger.info(f"  System memory: {memory_metrics.memory_usage_percent:.1f}%")
            self.logger.info(f"  Process memory: {memory_metrics.process_memory_mb:.1f}MB")
            self.logger.info(f"  Vector store: {vector_store_metrics.storage_size_mb:.1f}MB")
            self.logger.info(f"  Total documents: {vector_store_metrics.total_documents}")
            
        except Exception as e:
            self.logger.error(f"Initial memory assessment failed: {e}")
    
    async def execute_work_cycle(self) -> Dict[str, Any]:
        """Execute memory management work cycle"""
        work_start_time = time.time()
        
        try:
            # Get current memory metrics
            memory_metrics = await self.memory_tracker.get_current_memory_metrics()
            vector_store_metrics = await self.vector_store_manager.get_vector_store_metrics()
            
            # Detect memory leaks
            leaks = await self.leak_detector.detect_memory_leaks(
                self.memory_tracker.memory_history
            )
            
            # Check for cleanup needs
            cleanup_check = await self.vector_store_manager.check_cleanup_needed()
            
            # Generate alerts
            alerts = await self.generate_memory_alerts(
                memory_metrics, vector_store_metrics, leaks, cleanup_check
            )
            
            # Perform cleanup if needed
            cleanup_results = None
            if cleanup_check['cleanup_needed']:
                cleanup_results = await self.vector_store_manager.perform_cleanup()
                if cleanup_results['success']:
                    self.memory_stats['total_cleanups_performed'] += 1
                    self.memory_stats['total_memory_freed_mb'] += cleanup_results['size_reduction_mb']
                    self.memory_stats['last_cleanup_time'] = datetime.now(timezone.utc)
            
            # Update stats
            if leaks:
                self.memory_stats['leaks_detected'] += len(leaks)
                self.memory_stats['last_leak_detection_time'] = datetime.now(timezone.utc)
            
            if alerts:
                self.memory_stats['alerts_generated'] += len(alerts)
            
            processing_time = time.time() - work_start_time
            
            return {
                'success': True,
                'items_processed': 1,
                'processing_time': processing_time,
                'business_value': self.calculate_memory_business_value(
                    memory_metrics, vector_store_metrics, leaks, cleanup_results
                ),
                'memory_metrics': memory_metrics,
                'vector_store_metrics': vector_store_metrics,
                'leaks_detected': leaks,
                'alerts_generated': alerts,
                'cleanup_performed': cleanup_results is not None,
                'cleanup_results': cleanup_results
            }
            
        except Exception as e:
            self.logger.error(f"Memory management cycle failed: {e}")
            return {
                'success': False,
                'items_processed': 0,
                'processing_time': time.time() - work_start_time,
                'business_value': 0,
                'error_details': str(e)
            }
    
    async def generate_memory_alerts(self, memory_metrics: MemoryMetrics, 
                                   vector_store_metrics: VectorStoreMetrics,
                                   leaks: List[Dict], cleanup_check: Dict) -> List[Dict]:
        """Generate memory-related alerts"""
        alerts = []
        
        # Memory usage alert
        if memory_metrics.memory_usage_percent > self.alert_thresholds['memory_usage_percent']:
            alerts.append({
                'type': 'high_memory_usage',
                'severity': 'high' if memory_metrics.memory_usage_percent > 95 else 'medium',
                'message': f"System memory usage is {memory_metrics.memory_usage_percent:.1f}%",
                'value': memory_metrics.memory_usage_percent,
                'threshold': self.alert_thresholds['memory_usage_percent']
            })
        
        # Process memory alert
        if memory_metrics.process_memory_mb > self.alert_thresholds['process_memory_mb']:
            alerts.append({
                'type': 'high_process_memory',
                'severity': 'high' if memory_metrics.process_memory_mb > 1000 else 'medium',
                'message': f"Process memory usage is {memory_metrics.process_memory_mb:.1f}MB",
                'value': memory_metrics.process_memory_mb,
                'threshold': self.alert_thresholds['process_memory_mb']
            })
        
        # Vector store size alert
        if vector_store_metrics.storage_size_mb > self.alert_thresholds['vector_store_size_mb']:
            alerts.append({
                'type': 'large_vector_store',
                'severity': 'medium',
                'message': f"Vector store size is {vector_store_metrics.storage_size_mb:.1f}MB",
                'value': vector_store_metrics.storage_size_mb,
                'threshold': self.alert_thresholds['vector_store_size_mb']
            })
        
        # Memory leak alerts
        for leak in leaks:
            alerts.append({
                'type': 'memory_leak',
                'severity': leak.get('severity', 'medium'),
                'message': f"Memory leak detected: {leak.get('leak_type', 'unknown')}",
                'details': leak
            })
        
        # Cleanup needed alert
        if cleanup_check['cleanup_needed']:
            alerts.append({
                'type': 'cleanup_needed',
                'severity': 'medium',
                'message': f"Vector store cleanup needed: {cleanup_check['reason']}",
                'details': cleanup_check
            })
        
        return alerts
    
    def calculate_memory_business_value(self, memory_metrics: MemoryMetrics,
                                      vector_store_metrics: VectorStoreMetrics,
                                      leaks: List[Dict], cleanup_results: Dict) -> float:
        """Calculate business value of memory management activities"""
        base_value = 10.0  # Base value for monitoring
        
        # Value for preventing memory issues
        if memory_metrics.memory_usage_percent < 80:
            base_value += 20.0  # Good memory management
        
        # Value for cleanup activities
        if cleanup_results and cleanup_results.get('success'):
            size_freed = cleanup_results.get('size_reduction_mb', 0)
            base_value += size_freed * 0.1  # Value proportional to space freed
        
        # Value for leak detection
        if leaks:
            base_value += len(leaks) * 15.0  # Value for detecting issues
        
        # Value for efficient vector store
        if vector_store_metrics.storage_size_mb < 500:
            base_value += 10.0  # Efficient storage usage
        
        return round(base_value, 2)
    
    async def get_memory_dashboard_data(self) -> Dict[str, Any]:
        """Get data for memory management dashboard"""
        try:
            memory_metrics = await self.memory_tracker.get_current_memory_metrics()
            vector_store_metrics = await self.vector_store_manager.get_vector_store_metrics()
            
            return {
                'memory_metrics': memory_metrics,
                'vector_store_metrics': vector_store_metrics,
                'memory_stats': self.memory_stats,
                'alert_thresholds': self.alert_thresholds,
                'memory_history': self.memory_tracker.memory_history[-50:],  # Last 50 samples
                'timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)} 