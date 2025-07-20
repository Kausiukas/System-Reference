"""
PostgreSQL-Based Performance Monitor Agent

Enterprise performance monitoring with ML analytics,
cost optimization, and business intelligence integration.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import json

from ..coordination.base_agent import BaseAgent
from ..coordination.shared_state import SharedState


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    agent_id: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    category: str = 'general'


class MetricDataValidator:
    """Validates and normalizes performance metric data"""
    
    @staticmethod
    def validate_metric_data(metric_data: Any) -> bool:
        """Validate if metric data is properly formatted"""
        if isinstance(metric_data, PerformanceMetric):
            return True
        elif isinstance(metric_data, dict):
            required_fields = ['metric_name', 'metric_value', 'timestamp']
            return all(field in metric_data for field in required_fields)
        return False
    
    @staticmethod
    def normalize_metric_data(metric_data: Any, agent_id: str = None) -> PerformanceMetric:
        """Convert any metric data format to PerformanceMetric object"""
        if isinstance(metric_data, PerformanceMetric):
            return metric_data
        elif isinstance(metric_data, dict):
            # Handle database row format
            return PerformanceMetric(
                agent_id=metric_data.get('agent_id', agent_id or 'unknown'),
                metric_name=metric_data.get('metric_name', 'unknown'),
                value=float(metric_data.get('metric_value', 0)),
                unit=metric_data.get('metric_unit', ''),
                timestamp=metric_data.get('timestamp', datetime.now(timezone.utc)),
                category=MetricDataValidator.categorize_metric(metric_data.get('metric_name', ''))
            )
        else:
            # Fallback for unknown formats
            return PerformanceMetric(
                agent_id=agent_id or 'unknown',
                metric_name='unknown',
                value=0.0,
                unit='',
                timestamp=datetime.now(timezone.utc),
                category='general'
            )
    
    @staticmethod
    def categorize_metric(metric_name: str) -> str:
        """Categorize metrics for analysis"""
        if 'cpu' in metric_name.lower():
            return 'resource'
        elif 'memory' in metric_name.lower():
            return 'resource'
        elif 'processing' in metric_name.lower() or 'time' in metric_name.lower():
            return 'performance'
        elif 'error' in metric_name.lower():
            return 'reliability'
        elif 'business' in metric_name.lower() or 'value' in metric_name.lower():
            return 'business'
        else:
            return 'general'


class MLAnomalyDetector:
    """Machine learning-based anomaly detection for performance metrics"""
    
    def __init__(self):
        self.baseline_data = {}
        self.anomaly_threshold = 2.0  # Standard deviations
        
    async def detect_anomalies(self, metrics: List[PerformanceMetric]) -> List[Dict]:
        """Detect anomalies in performance metrics"""
        anomalies = []
        
        # Group metrics by type
        metric_groups = {}
        for metric in metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.value)
            
        # Detect anomalies for each metric type
        for metric_name, values in metric_groups.items():
            if len(values) < 3:  # Need at least 3 data points
                continue
                
            anomaly_score = await self.calculate_anomaly_score(values)
            
            if anomaly_score > self.anomaly_threshold:
                anomalies.append({
                    'metric_name': metric_name,
                    'anomaly_score': anomaly_score,
                    'severity': self.determine_anomaly_severity(anomaly_score),
                    'current_value': values[-1],
                    'baseline_mean': statistics.mean(values[:-1]) if len(values) > 1 else values[0],
                    'baseline_std': statistics.stdev(values[:-1]) if len(values) > 2 else 0
                })
                
        return anomalies
        
    async def calculate_anomaly_score(self, values: List[float]) -> float:
        """Calculate anomaly score using statistical methods"""
        if len(values) < 3:
            return 0.0
            
        # Use last value vs historical baseline
        current_value = values[-1]
        historical_values = values[:-1]
        
        if not historical_values:
            return 0.0
            
        mean = statistics.mean(historical_values)
        std = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
        
        if std == 0:
            return 0.0
            
        # Z-score based anomaly detection
        z_score = abs(current_value - mean) / std
        return z_score
        
    def determine_anomaly_severity(self, anomaly_score: float) -> str:
        """Determine anomaly severity based on score"""
        if anomaly_score > 4.0:
            return 'critical'
        elif anomaly_score > 3.0:
            return 'high'
        elif anomaly_score > 2.0:
            return 'medium'
        else:
            return 'low'


class CostAnalyzer:
    """Advanced cost analysis and optimization engine"""
    
    def __init__(self):
        self.cost_factors = {
            'cpu_usage': 0.50,      # $0.50 per CPU hour
            'memory_usage': 0.30,   # $0.30 per GB hour
            'processing_time': 0.10, # $0.10 per processing hour
            'error_cost': 5.00      # $5.00 per error (support cost)
        }
        
    async def analyze_costs(self, performance_data: Dict) -> Dict:
        """Comprehensive cost analysis"""
        try:
            current_costs = await self.calculate_current_costs(performance_data)
            optimization_opportunities = await self.identify_cost_optimizations(performance_data)
            projected_savings = sum(opt.get('potential_savings', 0) for opt in optimization_opportunities)
            roi_analysis = await self.calculate_roi_analysis({
                'current_costs': current_costs,
                'projected_savings': projected_savings
            })
            
            return {
                'current_costs': current_costs,
                'optimization_opportunities': optimization_opportunities,
                'projected_savings': projected_savings,
                'roi_analysis': roi_analysis
            }
            
        except Exception as e:
            logging.error(f"Cost analysis failed: {e}")
            return {
                'current_costs': {'total_cost': 0, 'error': str(e)},
                'optimization_opportunities': [],
                'projected_savings': 0,
                'roi_analysis': {}
            }
        
    async def calculate_current_costs(self, performance_data: Dict) -> Dict:
        """Calculate current operational costs"""
        agent_metrics = performance_data.get('agent_metrics', {})
        
        total_cpu_cost = 0.0
        total_memory_cost = 0.0
        total_processing_cost = 0.0
        total_error_cost = 0.0
        
        for agent_id, metrics in agent_metrics.items():
            # Ensure metrics are PerformanceMetric objects
            normalized_metrics = []
            for metric in metrics:
                if MetricDataValidator.validate_metric_data(metric):
                    normalized_metrics.append(MetricDataValidator.normalize_metric_data(metric, agent_id))
                else:
                    logging.warning(f"Invalid metric data for agent {agent_id}: {metric}")
                    continue
            
            # CPU costs
            cpu_metrics = [m for m in normalized_metrics if m.metric_name == 'cpu_usage']
            if cpu_metrics:
                avg_cpu = statistics.mean([m.value for m in cpu_metrics])
                cpu_hours = len(cpu_metrics) / 60  # Assuming metrics every minute
                total_cpu_cost += avg_cpu / 100 * cpu_hours * self.cost_factors['cpu_usage']
                
            # Memory costs
            memory_metrics = [m for m in normalized_metrics if m.metric_name == 'memory_usage']
            if memory_metrics:
                avg_memory = statistics.mean([m.value for m in memory_metrics])
                memory_gb_hours = (avg_memory / 100) * 8 * len(memory_metrics) / 60  # Assuming 8GB system
                total_memory_cost += memory_gb_hours * self.cost_factors['memory_usage']
                
            # Processing costs
            processing_metrics = [m for m in normalized_metrics if m.metric_name == 'processing_time']
            if processing_metrics:
                total_processing_time = sum(m.value for m in processing_metrics) / 3600  # Convert to hours
                total_processing_cost += total_processing_time * self.cost_factors['processing_time']
                
        return {
            'cpu_cost': round(total_cpu_cost, 2),
            'memory_cost': round(total_memory_cost, 2),
            'processing_cost': round(total_processing_cost, 2),
            'error_cost': round(total_error_cost, 2),
            'total_cost': round(total_cpu_cost + total_memory_cost + total_processing_cost + total_error_cost, 2)
        }
        
    async def identify_cost_optimizations(self, performance_data: Dict) -> List[Dict]:
        """Identify cost optimization opportunities"""
        optimizations = []
        agent_metrics = performance_data.get('agent_metrics', {})
        
        for agent_id, metrics in agent_metrics.items():
            # Ensure metrics are PerformanceMetric objects
            normalized_metrics = []
            for metric in metrics:
                if MetricDataValidator.validate_metric_data(metric):
                    normalized_metrics.append(MetricDataValidator.normalize_metric_data(metric, agent_id))
                else:
                    continue
            
            # High CPU usage optimization
            cpu_metrics = [m for m in normalized_metrics if m.metric_name == 'cpu_usage']
            if cpu_metrics:
                avg_cpu = statistics.mean([m.value for m in cpu_metrics])
                if avg_cpu > 80:
                    optimizations.append({
                        'type': 'cpu_optimization',
                        'agent_id': agent_id,
                        'description': f'High CPU usage ({avg_cpu:.1f}%) - consider load balancing',
                        'potential_savings': 50.0,
                        'priority': 'high'
                    })
                    
            # Memory optimization
            memory_metrics = [m for m in normalized_metrics if m.metric_name == 'memory_usage']
            if memory_metrics:
                avg_memory = statistics.mean([m.value for m in memory_metrics])
                if avg_memory > 85:
                    optimizations.append({
                        'type': 'memory_optimization',
                        'agent_id': agent_id,
                        'description': f'High memory usage ({avg_memory:.1f}%) - optimize memory allocation',
                        'potential_savings': 30.0,
                        'priority': 'medium'
                    })
                    
            # Processing time optimization
            processing_metrics = [m for m in normalized_metrics if m.metric_name == 'processing_time']
            if processing_metrics:
                avg_processing = statistics.mean([m.value for m in processing_metrics])
                if avg_processing > 5.0:  # 5 seconds threshold
                    optimizations.append({
                        'type': 'processing_optimization',
                        'agent_id': agent_id,
                        'description': f'Slow processing ({avg_processing:.1f}s) - optimize algorithms',
                        'potential_savings': 75.0,
                        'priority': 'high'
                    })
                    
        return optimizations
        
    async def calculate_roi_analysis(self, cost_analysis: Dict) -> Dict:
        """Calculate ROI analysis for optimization investments"""
        current_costs = cost_analysis['current_costs']['total_cost']
        projected_savings = cost_analysis['projected_savings']
        
        # Assume 20% implementation cost of projected savings
        implementation_cost = projected_savings * 0.2
        
        monthly_savings = projected_savings
        annual_savings = monthly_savings * 12
        
        roi_percentage = ((annual_savings - implementation_cost) / implementation_cost * 100) if implementation_cost > 0 else 0
        payback_months = (implementation_cost / monthly_savings) if monthly_savings > 0 else float('inf')
        
        return {
            'monthly_savings': round(monthly_savings, 2),
            'annual_savings': round(annual_savings, 2),
            'implementation_cost': round(implementation_cost, 2),
            'roi_percentage': round(roi_percentage, 1),
            'payback_period_months': round(payback_months, 1) if payback_months != float('inf') else None
        }


class BusinessIntelligenceEngine:
    """Advanced business intelligence for performance data"""
    
    async def generate_executive_report(self, performance_data: Dict, cost_analysis: Dict, 
                                      anomalies: List[Dict]) -> Dict:
        """Generate executive-level performance report"""
        
        return {
            'executive_summary': {
                'system_performance_score': await self.calculate_system_performance_score(performance_data),
                'cost_efficiency_rating': await self.calculate_cost_efficiency_rating(cost_analysis),
                'monthly_savings_potential': cost_analysis.get('projected_savings', 0),
                'system_reliability': await self.calculate_system_reliability(performance_data),
                'business_impact': await self.calculate_business_impact(performance_data, cost_analysis)
            },
            'key_metrics': {
                'total_agents_monitored': len(performance_data.get('agent_metrics', {})),
                'anomalies_detected': len(anomalies),
                'cost_optimization_opportunities': len(cost_analysis.get('optimization_opportunities', [])),
                'average_response_time': await self.calculate_average_response_time(performance_data),
                'system_uptime_percentage': await self.calculate_system_uptime(performance_data)
            },
            'strategic_insights': {
                'performance_trends': await self.analyze_performance_trends(performance_data),
                'cost_trends': await self.analyze_cost_trends(cost_analysis),
                'scalability_assessment': await self.assess_scalability(performance_data),
                'competitive_advantages': await self.identify_competitive_advantages(performance_data)
            },
            'recommendations': {
                'immediate_actions': await self.generate_immediate_actions(anomalies, cost_analysis),
                'strategic_initiatives': await self.generate_strategic_initiatives(performance_data),
                'investment_priorities': await self.prioritize_investments(cost_analysis)
            }
        }
        
    async def calculate_system_performance_score(self, performance_data: Dict) -> float:
        """Calculate overall system performance score (0-100)"""
        agent_metrics = performance_data.get('agent_metrics', {})
        
        if not agent_metrics:
            return 100.0
            
        total_score = 0.0
        agent_count = 0
        
        for agent_id, metrics in agent_metrics.items():
            agent_score = await self.calculate_agent_performance_score(metrics)
            total_score += agent_score
            agent_count += 1
            
        return total_score / agent_count if agent_count > 0 else 100.0
        
    async def calculate_agent_performance_score(self, metrics: List[Any]) -> float:
        """Calculate individual agent performance score"""
        # Ensure metrics are PerformanceMetric objects
        normalized_metrics = []
        for metric in metrics:
            if MetricDataValidator.validate_metric_data(metric):
                normalized_metrics.append(MetricDataValidator.normalize_metric_data(metric))
            else:
                continue
        
        score_factors = {
            'cpu_efficiency': 0.25,
            'memory_efficiency': 0.25,
            'processing_speed': 0.30,
            'error_rate': 0.20
        }
        
        # CPU efficiency (lower usage = higher score)
        cpu_metrics = [m.value for m in normalized_metrics if m.metric_name == 'cpu_usage']
        cpu_score = max(100 - (statistics.mean(cpu_metrics) if cpu_metrics else 0), 0)
        
        # Memory efficiency
        memory_metrics = [m.value for m in normalized_metrics if m.metric_name == 'memory_usage']
        memory_score = max(100 - (statistics.mean(memory_metrics) if memory_metrics else 0), 0)
        
        # Processing speed (faster = higher score)
        processing_metrics = [m.value for m in normalized_metrics if m.metric_name == 'processing_time']
        if processing_metrics:
            avg_processing = statistics.mean(processing_metrics)
            processing_score = max(100 - (avg_processing * 10), 0)  # 10 seconds = 0 score
        else:
            processing_score = 100
            
        # Error rate (fewer errors = higher score)
        error_metrics = [m.value for m in normalized_metrics if 'error' in m.metric_name]
        error_score = max(100 - (len(error_metrics) * 5), 0)  # 20 errors = 0 score
        
        # Calculate weighted score
        total_score = (
            cpu_score * score_factors['cpu_efficiency'] +
            memory_score * score_factors['memory_efficiency'] +
            processing_score * score_factors['processing_speed'] +
            error_score * score_factors['error_rate']
        )
        
        return min(max(total_score, 0), 100)
        
    async def calculate_cost_efficiency_rating(self, cost_analysis: Dict) -> str:
        """Calculate cost efficiency rating"""
        current_costs = cost_analysis.get('current_costs', {}).get('total_cost', 0)
        projected_savings = cost_analysis.get('projected_savings', 0)
        
        if current_costs == 0:
            return 'Excellent'
        elif projected_savings / current_costs > 0.3:
            return 'Good'
        elif projected_savings / current_costs > 0.1:
            return 'Fair'
        else:
            return 'Poor'
            
    async def calculate_system_reliability(self, performance_data: Dict) -> float:
        """Calculate system reliability score (0-100)"""
        agent_metrics = performance_data.get('agent_metrics', {})
        
        if not agent_metrics:
            return 100.0
            
        total_reliability = 0.0
        agent_count = 0
        
        for agent_id, metrics in agent_metrics.items():
            # Ensure metrics are PerformanceMetric objects
            normalized_metrics = []
            for metric in metrics:
                if MetricDataValidator.validate_metric_data(metric):
                    normalized_metrics.append(MetricDataValidator.normalize_metric_data(metric))
                else:
                    continue
            
            # Calculate agent reliability based on error metrics
            error_metrics = [m for m in normalized_metrics if 'error' in m.metric_name]
            error_count = len(error_metrics)
            
            # Reliability decreases with errors
            agent_reliability = max(100 - (error_count * 10), 0)
            total_reliability += agent_reliability
            agent_count += 1
            
        return total_reliability / agent_count if agent_count > 0 else 100.0
        
    async def calculate_business_impact(self, performance_data: Dict, cost_analysis: Dict) -> Dict:
        """Calculate business impact of performance issues"""
        return {
            'cost_impact': cost_analysis.get('current_costs', {}).get('total_cost', 0),
            'savings_potential': cost_analysis.get('projected_savings', 0),
            'performance_impact': 'Low' if await self.calculate_system_performance_score(performance_data) > 80 else 'Medium',
            'reliability_impact': 'Low' if await self.calculate_system_reliability(performance_data) > 90 else 'High'
        }
        
    async def calculate_average_response_time(self, performance_data: Dict) -> float:
        """Calculate average response time across all agents"""
        agent_metrics = performance_data.get('agent_metrics', {})
        
        all_response_times = []
        for agent_id, metrics in agent_metrics.items():
            # Ensure metrics are PerformanceMetric objects
            normalized_metrics = []
            for metric in metrics:
                if MetricDataValidator.validate_metric_data(metric):
                    normalized_metrics.append(MetricDataValidator.normalize_metric_data(metric))
                else:
                    continue
            
            response_times = [m.value for m in normalized_metrics if 'processing_time' in m.metric_name]
            all_response_times.extend(response_times)
            
        return statistics.mean(all_response_times) if all_response_times else 0.0
        
    async def calculate_system_uptime(self, performance_data: Dict) -> float:
        """Calculate system uptime percentage"""
        # Simplified uptime calculation based on active agents
        agent_metrics = performance_data.get('agent_metrics', {})
        active_agents = len(agent_metrics)
        
        # Assume we should have at least 10 agents for full uptime
        expected_agents = 10
        uptime_percentage = min((active_agents / expected_agents) * 100, 100)
        
        return round(uptime_percentage, 1)
        
    async def analyze_performance_trends(self, performance_data: Dict) -> List[str]:
        """Analyze performance trends"""
        trends = []
        
        # Add trend analysis based on available data
        agent_count = len(performance_data.get('agent_metrics', {}))
        if agent_count > 0:
            trends.append(f"System monitoring {agent_count} active agents")
        else:
            trends.append("No active agents detected")
            
        return trends
        
    async def analyze_cost_trends(self, cost_analysis: Dict) -> List[str]:
        """Analyze cost trends"""
        trends = []
        
        current_costs = cost_analysis.get('current_costs', {}).get('total_cost', 0)
        savings_potential = cost_analysis.get('projected_savings', 0)
        
        if savings_potential > current_costs * 0.2:
            trends.append("Significant cost optimization opportunities identified")
        elif current_costs > 0:
            trends.append("Costs are within acceptable range")
            
        return trends
        
    async def assess_scalability(self, performance_data: Dict) -> str:
        """Assess system scalability"""
        agent_count = len(performance_data.get('agent_metrics', {}))
        
        if agent_count > 15:
            return "High scalability - system can handle increased load"
        elif agent_count > 10:
            return "Good scalability - room for moderate growth"
        else:
            return "Limited scalability - consider optimization"
            
    async def identify_competitive_advantages(self, performance_data: Dict) -> List[str]:
        """Identify competitive advantages"""
        advantages = []
        
        # Add advantages based on system capabilities
        advantages.append("Real-time performance monitoring")
        advantages.append("Automated cost optimization")
        advantages.append("ML-powered anomaly detection")
        
        return advantages
        
    async def generate_immediate_actions(self, anomalies: List[Dict], cost_analysis: Dict) -> List[str]:
        """Generate immediate action recommendations"""
        actions = []
        
        # High priority anomalies
        critical_anomalies = [a for a in anomalies if a.get('severity') == 'critical']
        if critical_anomalies:
            actions.append(f"Investigate {len(critical_anomalies)} critical performance anomalies")
            
        # Cost optimizations
        high_priority_optimizations = [
            opt for opt in cost_analysis.get('optimization_opportunities', [])
            if opt.get('priority') == 'high'
        ]
        if high_priority_optimizations:
            actions.append(f"Implement {len(high_priority_optimizations)} high-priority cost optimizations")
            
        return actions
        
    async def generate_strategic_initiatives(self, performance_data: Dict) -> List[str]:
        """Generate strategic initiative recommendations"""
        initiatives = []
        
        # Add strategic recommendations
        initiatives.append("Implement advanced ML-based predictive maintenance")
        initiatives.append("Develop comprehensive performance benchmarking")
        initiatives.append("Establish automated scaling policies")
        
        return initiatives
        
    async def prioritize_investments(self, cost_analysis: Dict) -> List[str]:
        """Prioritize investment recommendations"""
        priorities = []
        
        # Add investment priorities based on cost analysis
        priorities.append("Performance monitoring infrastructure")
        priorities.append("Automation and optimization tools")
        priorities.append("Training and skill development")
        
        return priorities


class PerformanceMonitor(BaseAgent):
    """Enterprise performance monitoring agent with ML analytics"""
    
    def __init__(self, agent_id: str = "performance_monitor", shared_state=None):
        super().__init__(agent_id, shared_state)
        self.anomaly_detector = MLAnomalyDetector()
        self.cost_analyzer = CostAnalyzer()
        self.bi_engine = BusinessIntelligenceEngine()
        self.metric_validator = MetricDataValidator()
        
    async def initialize(self) -> None:
        """Initialize performance monitoring components"""
        await super().initialize()
        self.logger.info("Performance monitoring agent initialized")
        
    async def execute_work_cycle(self) -> Dict[str, Any]:
        """Execute performance monitoring work cycle"""
        work_start_time = time.time()
        
        try:
            # Collect performance data
            performance_data = await self.collect_performance_data()
            
            if 'error' in performance_data:
                raise Exception(f"Data collection failed: {performance_data['error']}")
            
            # Convert to PerformanceMetric objects for processing
            all_metrics = self.convert_to_performance_metrics(performance_data)
            
            # Detect anomalies
            anomalies = await self.anomaly_detector.detect_anomalies(all_metrics)
            
            # Analyze costs
            cost_analysis = await self.cost_analyzer.analyze_costs(performance_data)
            
            # Generate business intelligence report
            bi_report = await self.bi_engine.generate_executive_report(
                performance_data, cost_analysis, anomalies
            )
            
            # Process alerts
            await self.process_performance_alerts(anomalies, cost_analysis)
            
            processing_time = time.time() - work_start_time
            
            return {
                'success': True,
                'items_processed': len(performance_data.get('agent_metrics', {})),
                'processing_time': processing_time,
                'business_value': self.calculate_monitoring_business_value(bi_report),
                'performance_data': performance_data,
                'anomalies': anomalies,
                'cost_analysis': cost_analysis,
                'bi_report': bi_report
            }
            
        except Exception as e:
            self.logger.error(f"Performance monitoring cycle failed: {e}")
            return {
                'success': False,
                'items_processed': 0,
                'processing_time': time.time() - work_start_time,
                'business_value': 0,
                'error_details': str(e)
            }
            
    async def collect_performance_data(self) -> Dict:
        """Collect comprehensive performance data from all agents"""
        try:
            # Get all registered agents
            agents = await self.shared_state.get_registered_agents()
            
            performance_data = {
                'timestamp': datetime.now(timezone.utc),
                'agent_metrics': {},
                'system_metrics': {}
            }
            
            # Collect metrics for each agent
            for agent in agents:
                agent_id = agent['agent_id']
                
                # Get performance metrics from the last hour (raw rows)
                raw_metrics = await self.shared_state.get_performance_metrics(
                    agent_id=agent_id,
                    hours=1
                )

                # Convert DB rows (dicts) to PerformanceMetric objects so downstream
                # analytics can safely access attribute-style fields.
                metric_objs = []
                for m in raw_metrics:
                    if self.metric_validator.validate_metric_data(m):
                        metric_objs.append(self.metric_validator.normalize_metric_data(m, agent_id))
                    else:
                        self.logger.warning(f"Invalid metric data for agent {agent_id}: {m}")

                performance_data['agent_metrics'][agent_id] = metric_objs
                
            # Collect system-wide metrics
            performance_data['system_metrics'] = await self.collect_system_metrics()
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect performance data: {e}")
            return {'error': str(e)}
            
    async def collect_system_metrics(self) -> Dict:
        """Collect system-wide performance metrics"""
        try:
            # Get database performance
            db_performance = await self.shared_state.postgresql_adapter.get_database_performance()
            
            # Get connection status
            connection_status = await self.shared_state.postgresql_adapter.get_connection_status()
            
            return {
                'database_performance': db_performance,
                'connection_status': connection_status,
                'timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e)}
            
    def convert_to_performance_metrics(self, performance_data: Dict) -> List[PerformanceMetric]:
        """Convert raw performance data to PerformanceMetric objects"""
        metrics = []
        
        agent_metrics = performance_data.get('agent_metrics', {})
        
        for agent_id, agent_metric_list in agent_metrics.items():
            for metric_data in agent_metric_list:
                # Validate and normalize metric data
                if self.metric_validator.validate_metric_data(metric_data):
                    normalized_metric = self.metric_validator.normalize_metric_data(metric_data, agent_id)
                    metrics.append(normalized_metric)
                else:
                    self.logger.warning(f"Invalid metric data in conversion: {metric_data}")
                
        return metrics
        
    async def process_performance_alerts(self, anomalies: List[Dict], cost_analysis: Dict) -> None:
        """Process performance alerts and notifications"""
        try:
            # Process anomaly alerts
            for anomaly in anomalies:
                if anomaly.get('severity') in ['critical', 'high']:
                    await self.send_performance_alert(anomaly)
                    
            # Process cost optimization alerts
            high_priority_optimizations = [
                opt for opt in cost_analysis.get('optimization_opportunities', [])
                if opt.get('priority') == 'high'
            ]
            
            if high_priority_optimizations:
                await self.send_cost_optimization_alert(high_priority_optimizations)
                
        except Exception as e:
            self.logger.error(f"Failed to process performance alerts: {e}")
            
    async def send_performance_alert(self, anomaly: Dict) -> None:
        """Send performance anomaly alert"""
        try:
            alert_data = {
                'alert_type': 'performance_anomaly',
                'agent_id': anomaly.get('agent_id'),
                'metric_name': anomaly.get('metric_name'),
                'anomaly_score': anomaly.get('anomaly_score'),
                'severity': anomaly.get('severity'),
                'current_value': anomaly.get('current_value'),
                'baseline_mean': anomaly.get('baseline_mean')
            }
            
            await self.shared_state.log_system_event(
                'performance_anomaly_alert',
                alert_data,
                agent_id=self.agent_id,
                severity='WARNING' if anomaly.get('severity') == 'high' else 'ERROR'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send performance alert: {e}")
            
    async def send_cost_optimization_alert(self, optimizations: List[Dict]) -> None:
        """Send cost optimization alert"""
        try:
            total_savings = sum(opt.get('potential_savings', 0) for opt in optimizations)
            
            alert_data = {
                'alert_type': 'cost_optimization',
                'optimization_count': len(optimizations),
                'total_potential_savings': total_savings,
                'optimizations': optimizations
            }
            
            await self.shared_state.log_system_event(
                'cost_optimization_alert',
                alert_data,
                agent_id=self.agent_id,
                severity='INFO'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send cost optimization alert: {e}")
            
    def calculate_monitoring_business_value(self, bi_report: Dict) -> float:
        """Calculate business value of performance monitoring"""
        executive_summary = bi_report.get('executive_summary', {})
        
        # Base value for monitoring activity
        base_value = 200.0
        
        # Additional value from cost savings potential
        savings_potential = executive_summary.get('monthly_savings_potential', 0)
        
        # Business value is 10% of identified savings potential
        savings_value = savings_potential * 0.1
        
        return base_value + savings_value 
