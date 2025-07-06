"""
Enhanced Shared State Monitor Agent

Advanced monitoring agent for comprehensive shared state analysis,
performance optimization, and business intelligence integration.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import statistics

from ..coordination.base_agent import BaseAgent


@dataclass
class StateMetrics:
    """Shared state metrics data structure"""
    timestamp: datetime
    total_agents: int
    active_agents: int
    database_connections: int
    query_performance: float
    cache_hit_ratio: float
    state_consistency_score: float
    error_rate: float


@dataclass
class PerformanceAlert:
    """Performance alert data structure"""
    alert_id: str
    severity: str
    metric_name: str
    threshold: float
    actual_value: float
    recommendation: str
    business_impact: str


class SharedStateAnalyzer:
    """Advanced analyzer for shared state metrics and patterns"""
    
    def __init__(self, shared_state):
        self.shared_state = shared_state
        self.logger = logging.getLogger("state_analyzer")
        
        # Analysis configuration
        self.analysis_window_hours = 24
        self.performance_thresholds = {
            'query_performance': 1.0,  # seconds
            'cache_hit_ratio': 85.0,   # percent
            'error_rate': 5.0,         # percent
            'consistency_score': 90.0  # percent
        }
        
    async def analyze_state_performance(self) -> Dict[str, Any]:
        """Analyze comprehensive shared state performance"""
        
        try:
            # Get current state metrics
            current_metrics = await self.gather_current_metrics()
            
            # Get historical metrics for trend analysis
            historical_metrics = await self.gather_historical_metrics()
            
            # Analyze performance trends
            trends = await self.analyze_performance_trends(historical_metrics)
            
            # Identify performance issues
            issues = await self.identify_performance_issues(current_metrics, trends)
            
            # Generate optimization recommendations
            recommendations = await self.generate_optimization_recommendations(
                current_metrics, trends, issues
            )
            
            # Calculate business impact
            business_impact = await self.calculate_business_impact(
                current_metrics, issues
            )
            
            return {
                'analysis_timestamp': datetime.now(timezone.utc),
                'current_metrics': current_metrics,
                'performance_trends': trends,
                'identified_issues': issues,
                'optimization_recommendations': recommendations,
                'business_impact': business_impact,
                'overall_health_score': self.calculate_overall_health(current_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"State performance analysis failed: {e}")
            return {'error': str(e), 'analysis_timestamp': datetime.now(timezone.utc)}
            
    async def gather_current_metrics(self) -> StateMetrics:
        """Gather current shared state metrics"""
        
        try:
            # Get agent statistics
            agents = await self.shared_state.get_registered_agents()
            total_agents = len(agents)
            active_agents = len([a for a in agents if a.get('state') == 'active'])
            
            # Get database performance metrics
            db_health = await self.shared_state.postgresql_adapter.health_check()
            query_performance = db_health.get('response_time_seconds', 0)
            database_connections = db_health.get('active_connections', 0)
            
            # Calculate cache hit ratio
            cache_hit_ratio = await self.calculate_cache_hit_ratio()
            
            # Calculate state consistency score
            consistency_score = await self.calculate_state_consistency()
            
            # Calculate error rate
            error_rate = await self.calculate_error_rate()
            
            return StateMetrics(
                timestamp=datetime.now(timezone.utc),
                total_agents=total_agents,
                active_agents=active_agents,
                database_connections=database_connections,
                query_performance=query_performance,
                cache_hit_ratio=cache_hit_ratio,
                state_consistency_score=consistency_score,
                error_rate=error_rate
            )
            
        except Exception as e:
            self.logger.error(f"Failed to gather current metrics: {e}")
            return StateMetrics(
                timestamp=datetime.now(timezone.utc),
                total_agents=0, active_agents=0, database_connections=0,
                query_performance=999.0, cache_hit_ratio=0.0,
                state_consistency_score=0.0, error_rate=100.0
            )
            
    async def calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio for shared state operations"""
        
        try:
            # Get recent performance metrics
            metrics = await self.shared_state.get_performance_metrics(
                metric_name='cache_hit_ratio', hours=1
            )
            
            if metrics:
                values = [m['metric_value'] for m in metrics]
                return statistics.mean(values)
            else:
                # Estimate based on system behavior
                return 75.0  # Default reasonable cache hit ratio
                
        except Exception as e:
            self.logger.error(f"Failed to calculate cache hit ratio: {e}")
            return 50.0
            
    async def calculate_state_consistency(self) -> float:
        """Calculate state consistency score"""
        
        try:
            # Check for agent state inconsistencies
            agents = await self.shared_state.get_registered_agents()
            consistency_checks = []
            
            for agent in agents:
                agent_id = agent.get('agent_id')
                if agent_id:
                    # Check heartbeat consistency
                    recent_heartbeats = await self.shared_state.get_recent_heartbeats(
                        agent_id, minutes=5
                    )
                    
                    # Score based on heartbeat regularity
                    if len(recent_heartbeats) >= 3:
                        consistency_checks.append(100.0)
                    elif len(recent_heartbeats) >= 1:
                        consistency_checks.append(70.0)
                    else:
                        consistency_checks.append(0.0)
                        
            if consistency_checks:
                return statistics.mean(consistency_checks)
            else:
                return 90.0  # Default good consistency
                
        except Exception as e:
            self.logger.error(f"Failed to calculate state consistency: {e}")
            return 50.0
            
    async def calculate_error_rate(self) -> float:
        """Calculate system error rate"""
        
        try:
            # Get recent system events
            events = await self.shared_state.get_system_events(hours=1)
            
            if not events:
                return 0.0
                
            # Count error events
            error_events = len([e for e in events if e.get('severity') in ['ERROR', 'CRITICAL']])
            total_events = len(events)
            
            return (error_events / total_events) * 100 if total_events > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to calculate error rate: {e}")
            return 5.0
            
    async def gather_historical_metrics(self) -> List[StateMetrics]:
        """Gather historical metrics for trend analysis"""
        
        historical_metrics = []
        
        try:
            # Get performance metrics from the last 24 hours
            performance_data = await self.shared_state.get_performance_metrics(
                hours=self.analysis_window_hours
            )
            
            # Group metrics by hour for trend analysis
            hourly_groups = {}
            for metric in performance_data:
                timestamp = metric.get('timestamp')
                if timestamp:
                    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                    if hour_key not in hourly_groups:
                        hourly_groups[hour_key] = []
                    hourly_groups[hour_key].append(metric)
                    
            # Create StateMetrics for each hour
            for hour_timestamp, metrics in hourly_groups.items():
                # Aggregate metrics for this hour
                state_metrics = await self.aggregate_hourly_metrics(hour_timestamp, metrics)
                if state_metrics:
                    historical_metrics.append(state_metrics)
                    
            return sorted(historical_metrics, key=lambda x: x.timestamp)
            
        except Exception as e:
            self.logger.error(f"Failed to gather historical metrics: {e}")
            return []
            
    async def aggregate_hourly_metrics(self, timestamp: datetime, 
                                     metrics: List[Dict]) -> Optional[StateMetrics]:
        """Aggregate metrics for a specific hour"""
        
        try:
            # Extract relevant metrics
            query_times = [m['metric_value'] for m in metrics 
                          if m['metric_name'] == 'query_performance']
            cache_ratios = [m['metric_value'] for m in metrics 
                           if m['metric_name'] == 'cache_hit_ratio']
            
            # Use current values or defaults for missing data
            return StateMetrics(
                timestamp=timestamp,
                total_agents=10,  # Estimated
                active_agents=8,  # Estimated
                database_connections=5,  # Estimated
                query_performance=statistics.mean(query_times) if query_times else 0.5,
                cache_hit_ratio=statistics.mean(cache_ratios) if cache_ratios else 80.0,
                state_consistency_score=95.0,  # Estimated
                error_rate=2.0  # Estimated
            )
            
        except Exception as e:
            self.logger.error(f"Failed to aggregate hourly metrics: {e}")
            return None
            
    async def analyze_performance_trends(self, historical_metrics: List[StateMetrics]) -> Dict[str, Any]:
        """Analyze performance trends from historical data"""
        
        if len(historical_metrics) < 2:
            return {'trend_analysis': 'insufficient_data'}
            
        try:
            trends = {}
            
            # Query performance trend
            query_times = [m.query_performance for m in historical_metrics]
            trends['query_performance'] = {
                'trend_direction': self.calculate_trend_direction(query_times),
                'average': statistics.mean(query_times),
                'trend_strength': self.calculate_trend_strength(query_times)
            }
            
            # Cache hit ratio trend
            cache_ratios = [m.cache_hit_ratio for m in historical_metrics]
            trends['cache_hit_ratio'] = {
                'trend_direction': self.calculate_trend_direction(cache_ratios),
                'average': statistics.mean(cache_ratios),
                'trend_strength': self.calculate_trend_strength(cache_ratios)
            }
            
            # Error rate trend
            error_rates = [m.error_rate for m in historical_metrics]
            trends['error_rate'] = {
                'trend_direction': self.calculate_trend_direction(error_rates),
                'average': statistics.mean(error_rates),
                'trend_strength': self.calculate_trend_strength(error_rates)
            }
            
            # Overall trend assessment
            trends['overall_assessment'] = self.assess_overall_trends(trends)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Failed to analyze performance trends: {e}")
            return {'error': str(e)}
            
    def calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        
        if len(values) < 2:
            return 'stable'
            
        # Simple linear trend calculation
        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])
        
        difference = second_half - first_half
        threshold = statistics.stdev(values) * 0.5 if len(values) > 2 else 0.1
        
        if difference > threshold:
            return 'increasing'
        elif difference < -threshold:
            return 'decreasing'
        else:
            return 'stable'
            
    def calculate_trend_strength(self, values: List[float]) -> float:
        """Calculate trend strength (0-100)"""
        
        if len(values) < 3:
            return 0.0
            
        # Calculate correlation coefficient with time
        x_values = list(range(len(values)))
        correlation = self.pearson_correlation(x_values, values)
        
        return abs(correlation) * 100
        
    def pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        
        n = len(x)
        if n < 2:
            return 0.0
            
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator
        
    def assess_overall_trends(self, trends: Dict[str, Any]) -> str:
        """Assess overall system trends"""
        
        concerning_trends = 0
        
        # Check for concerning trends
        if trends.get('query_performance', {}).get('trend_direction') == 'increasing':
            concerning_trends += 1
            
        if trends.get('cache_hit_ratio', {}).get('trend_direction') == 'decreasing':
            concerning_trends += 1
            
        if trends.get('error_rate', {}).get('trend_direction') == 'increasing':
            concerning_trends += 1
            
        if concerning_trends >= 2:
            return 'degrading'
        elif concerning_trends == 1:
            return 'mixed'
        else:
            return 'improving'
            
    async def identify_performance_issues(self, current_metrics: StateMetrics, 
                                        trends: Dict[str, Any]) -> List[PerformanceAlert]:
        """Identify performance issues and generate alerts"""
        
        alerts = []
        
        try:
            # Check query performance
            if current_metrics.query_performance > self.performance_thresholds['query_performance']:
                alerts.append(PerformanceAlert(
                    alert_id=f"query_perf_{int(time.time())}",
                    severity='HIGH' if current_metrics.query_performance > 2.0 else 'MEDIUM',
                    metric_name='query_performance',
                    threshold=self.performance_thresholds['query_performance'],
                    actual_value=current_metrics.query_performance,
                    recommendation='Optimize database queries and consider connection pooling',
                    business_impact='Reduced system responsiveness affecting user experience'
                ))
                
            # Check cache hit ratio
            if current_metrics.cache_hit_ratio < self.performance_thresholds['cache_hit_ratio']:
                alerts.append(PerformanceAlert(
                    alert_id=f"cache_ratio_{int(time.time())}",
                    severity='MEDIUM',
                    metric_name='cache_hit_ratio',
                    threshold=self.performance_thresholds['cache_hit_ratio'],
                    actual_value=current_metrics.cache_hit_ratio,
                    recommendation='Review caching strategy and increase cache size',
                    business_impact='Increased database load and slower response times'
                ))
                
            # Check error rate
            if current_metrics.error_rate > self.performance_thresholds['error_rate']:
                alerts.append(PerformanceAlert(
                    alert_id=f"error_rate_{int(time.time())}",
                    severity='HIGH',
                    metric_name='error_rate',
                    threshold=self.performance_thresholds['error_rate'],
                    actual_value=current_metrics.error_rate,
                    recommendation='Investigate error sources and improve error handling',
                    business_impact='System reliability concerns affecting operations'
                ))
                
            # Check state consistency
            if current_metrics.state_consistency_score < self.performance_thresholds['consistency_score']:
                alerts.append(PerformanceAlert(
                    alert_id=f"consistency_{int(time.time())}",
                    severity='HIGH',
                    metric_name='state_consistency',
                    threshold=self.performance_thresholds['consistency_score'],
                    actual_value=current_metrics.state_consistency_score,
                    recommendation='Review agent synchronization and state management',
                    business_impact='Data integrity concerns affecting business operations'
                ))
                
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to identify performance issues: {e}")
            return []
            
    async def generate_optimization_recommendations(self, current_metrics: StateMetrics,
                                                  trends: Dict[str, Any], 
                                                  issues: List[PerformanceAlert]) -> List[str]:
        """Generate optimization recommendations"""
        
        recommendations = []
        
        try:
            # Database optimization recommendations
            if current_metrics.query_performance > 1.0:
                recommendations.append(
                    "Database Optimization: Consider query optimization, index tuning, "
                    "and connection pool configuration improvements"
                )
                
            # Caching recommendations
            if current_metrics.cache_hit_ratio < 85.0:
                recommendations.append(
                    "Caching Strategy: Implement more aggressive caching policies "
                    "and consider distributed caching for better performance"
                )
                
            # Error handling recommendations
            if current_metrics.error_rate > 3.0:
                recommendations.append(
                    "Error Management: Implement circuit breakers, better retry logic, "
                    "and comprehensive error logging for improved reliability"
                )
                
            # Trend-based recommendations
            if trends.get('overall_assessment') == 'degrading':
                recommendations.append(
                    "System Health: Implement proactive monitoring and automated "
                    "recovery procedures to prevent further degradation"
                )
                
            # High-level recommendations
            if len(issues) > 2:
                recommendations.append(
                    "Architecture Review: Consider system architecture review "
                    "to address multiple performance concerns"
                )
                
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error"]
            
    async def calculate_business_impact(self, current_metrics: StateMetrics, 
                                      issues: List[PerformanceAlert]) -> Dict[str, Any]:
        """Calculate business impact of performance metrics"""
        
        try:
            # Base business metrics
            impact = {
                'performance_cost': 0.0,
                'reliability_risk': 'LOW',
                'user_experience_impact': 'MINIMAL',
                'operational_efficiency': 'HIGH'
            }
            
            # Calculate performance cost impact
            if current_metrics.query_performance > 2.0:
                impact['performance_cost'] += 500.0  # $500/day for slow queries
                
            if current_metrics.error_rate > 5.0:
                impact['performance_cost'] += 1000.0  # $1000/day for high error rate
                
            # Assess reliability risk
            high_severity_issues = len([i for i in issues if i.severity == 'HIGH'])
            if high_severity_issues >= 2:
                impact['reliability_risk'] = 'HIGH'
            elif high_severity_issues == 1:
                impact['reliability_risk'] = 'MEDIUM'
                
            # User experience impact
            if (current_metrics.query_performance > 1.5 or 
                current_metrics.error_rate > 3.0):
                impact['user_experience_impact'] = 'SIGNIFICANT'
            elif (current_metrics.query_performance > 1.0 or 
                  current_metrics.error_rate > 1.0):
                impact['user_experience_impact'] = 'MODERATE'
                
            # Operational efficiency
            if len(issues) >= 3:
                impact['operational_efficiency'] = 'DEGRADED'
            elif len(issues) >= 1:
                impact['operational_efficiency'] = 'REDUCED'
                
            return impact
            
        except Exception as e:
            self.logger.error(f"Failed to calculate business impact: {e}")
            return {'error': str(e)}
            
    def calculate_overall_health(self, metrics: StateMetrics) -> float:
        """Calculate overall health score (0-100)"""
        
        try:
            # Component scores
            query_score = max(100 - (metrics.query_performance * 50), 0)
            cache_score = metrics.cache_hit_ratio
            consistency_score = metrics.state_consistency_score
            error_score = max(100 - (metrics.error_rate * 10), 0)
            
            # Weighted average
            overall_score = (
                query_score * 0.3 +
                cache_score * 0.25 +
                consistency_score * 0.25 +
                error_score * 0.2
            )
            
            return min(max(overall_score, 0), 100)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate overall health: {e}")
            return 50.0


class EnhancedSharedStateMonitor(BaseAgent):
    """
    Enhanced Shared State Monitor Agent
    
    Provides comprehensive monitoring and analysis of shared state performance,
    identifying optimization opportunities and business impact.
    """
    
    def __init__(self, agent_id: str = "enhanced_shared_state_monitor", shared_state=None):
        super().__init__(agent_id, shared_state)
        self.agent_name = "EnhancedSharedStateMonitor"
        
        # Initialize analyzer
        self.analyzer = SharedStateAnalyzer(shared_state)
        
        # Configuration
        self.monitoring_interval = 300  # 5 minutes
        self.detailed_analysis_interval = 3600  # 1 hour
        
        # Performance tracking
        self.monitor_stats = {
            'analyses_completed': 0,
            'issues_identified': 0,
            'recommendations_generated': 0,
            'business_value_calculated': 0
        }
        
    async def initialize(self) -> None:
        """Initialize enhanced shared state monitor"""
        self.logger.info("Initializing Enhanced Shared State Monitor")
        
        # Set work interval
        self.work_interval = self.monitoring_interval
        
    async def execute_work_cycle(self) -> Dict[str, Any]:
        """Execute shared state monitoring cycle"""
        work_start_time = time.time()
        
        try:
            # Perform comprehensive state analysis
            analysis_results = await self.analyzer.analyze_state_performance()
            
            # Log analysis results
            await self.log_analysis_results(analysis_results)
            
            # Generate alerts for issues
            issues = analysis_results.get('identified_issues', [])
            await self.generate_alerts(issues)
            
            # Update monitoring statistics
            await self.update_monitor_statistics(analysis_results)
            
            processing_time = time.time() - work_start_time
            
            return {
                'success': True,
                'processing_time': processing_time,
                'analyses_performed': 1,
                'issues_identified': len(issues),
                'business_value': self.calculate_monitoring_business_value(analysis_results),
                'overall_health_score': analysis_results.get('overall_health_score', 0),
                'recommendations_count': len(analysis_results.get('optimization_recommendations', []))
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced state monitoring cycle failed: {e}")
            return {
                'success': False,
                'processing_time': time.time() - work_start_time,
                'error_details': str(e)
            }
            
    async def log_analysis_results(self, analysis_results: Dict[str, Any]) -> None:
        """Log comprehensive analysis results"""
        try:
            # Log system event with analysis summary
            await self.shared_state.log_system_event(
                'state_analysis_complete',
                {
                    'analysis_timestamp': analysis_results.get('analysis_timestamp'),
                    'overall_health_score': analysis_results.get('overall_health_score'),
                    'issues_count': len(analysis_results.get('identified_issues', [])),
                    'recommendations_count': len(analysis_results.get('optimization_recommendations', [])),
                    'business_impact': analysis_results.get('business_impact', {})
                },
                agent_id=self.agent_id,
                severity='INFO'
            )
            
            # Log performance metrics
            health_score = analysis_results.get('overall_health_score', 0)
            await self.shared_state.log_performance_metric(
                'shared_state_health_score', health_score, 'score', self.agent_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log analysis results: {e}")
            
    async def generate_alerts(self, issues: List[PerformanceAlert]) -> None:
        """Generate alerts for identified issues"""
        try:
            for issue in issues:
                # Log high severity issues as system events
                if issue.severity == 'HIGH':
                    await self.shared_state.log_system_event(
                        'performance_alert',
                        {
                            'alert_id': issue.alert_id,
                            'metric_name': issue.metric_name,
                            'threshold': issue.threshold,
                            'actual_value': issue.actual_value,
                            'recommendation': issue.recommendation,
                            'business_impact': issue.business_impact
                        },
                        agent_id=self.agent_id,
                        severity='WARNING'
                    )
                    
                # Log business metric for alert tracking
                await self.shared_state.log_business_metric(
                    'system_reliability',
                    'performance_alert',
                    1.0,
                    {
                        'severity': issue.severity,
                        'metric_name': issue.metric_name,
                        'impact': issue.business_impact
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Failed to generate alerts: {e}")
            
    async def update_monitor_statistics(self, analysis_results: Dict[str, Any]) -> None:
        """Update monitoring statistics"""
        
        self.monitor_stats['analyses_completed'] += 1
        self.monitor_stats['issues_identified'] += len(
            analysis_results.get('identified_issues', [])
        )
        self.monitor_stats['recommendations_generated'] += len(
            analysis_results.get('optimization_recommendations', [])
        )
        
        # Calculate business value
        business_impact = analysis_results.get('business_impact', {})
        cost_savings = business_impact.get('performance_cost', 0)
        self.monitor_stats['business_value_calculated'] += cost_savings
        
    def calculate_monitoring_business_value(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate business value of monitoring activities"""
        
        base_value = 200.0  # Base value for monitoring
        
        # Additional value from issue identification
        issues_count = len(analysis_results.get('identified_issues', []))
        issue_value = issues_count * 150.0
        
        # Value from optimization recommendations
        recommendations_count = len(analysis_results.get('optimization_recommendations', []))
        recommendation_value = recommendations_count * 100.0
        
        # Health score bonus
        health_score = analysis_results.get('overall_health_score', 0)
        if health_score > 90:
            health_bonus = 50.0
        elif health_score > 80:
            health_bonus = 25.0
        else:
            health_bonus = 0.0
            
        return base_value + issue_value + recommendation_value + health_bonus 