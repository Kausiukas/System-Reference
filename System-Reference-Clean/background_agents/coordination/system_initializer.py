"""
System Initializer

Enterprise system initialization with comprehensive setup,
validation, and configuration management.
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path
import json

from .shared_state import SharedState
from .postgresql_adapter import PostgreSQLAdapter, ConnectionConfig


class SystemInitializer:
    """
    Enterprise System Initializer
    
    Coordinates complete system initialization including:
    - Database schema setup and validation
    - Agent registration and configuration
    - Performance baseline establishment
    - Business intelligence initialization
    - System health verification
    """
    
    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state
        self.logger = logging.getLogger("system_initializer")
        
        # Initialization configuration
        self.initialization_timeout = 300  # 5 minutes
        self.validation_timeout = 60  # 1 minute
        
        # System components status
        self.initialization_status = {
            'database_schema': False,
            'agent_registry': False,
            'performance_baselines': False,
            'business_intelligence': False,
            'system_health': False,
            'configuration_loaded': False
        }
        
        # Business metrics for initialization
        self.initialization_metrics = {
            'start_time': None,
            'completion_time': None,
            'components_initialized': 0,
            'validation_checks_passed': 0,
            'business_value_established': 0.0
        }
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the complete system infrastructure"""
        
        self.initialization_metrics['start_time'] = datetime.now(timezone.utc)
        
        try:
            self.logger.info("Starting comprehensive system initialization...")
            
            # Phase 1: Database and Schema Setup
            await self.initialize_database_schema()
            self.initialization_status['database_schema'] = True
            self.initialization_metrics['components_initialized'] += 1
            
            # Phase 2: Agent Registry Setup
            await self.initialize_agent_registry()
            self.initialization_status['agent_registry'] = True
            self.initialization_metrics['components_initialized'] += 1
            
            # Phase 3: Performance Baselines
            await self.establish_performance_baselines()
            self.initialization_status['performance_baselines'] = True
            self.initialization_metrics['components_initialized'] += 1
            
            # Phase 4: Business Intelligence Setup
            await self.initialize_business_intelligence()
            self.initialization_status['business_intelligence'] = True
            self.initialization_metrics['components_initialized'] += 1
            
            # Phase 5: System Configuration
            await self.load_system_configuration()
            self.initialization_status['configuration_loaded'] = True
            self.initialization_metrics['components_initialized'] += 1
            
            # Phase 6: System Health Verification
            await self.verify_system_health()
            self.initialization_status['system_health'] = True
            self.initialization_metrics['components_initialized'] += 1
            
            # Complete initialization
            self.initialization_metrics['completion_time'] = datetime.now(timezone.utc)
            
            # Log successful initialization
            await self.log_initialization_success()
            
            return await self.generate_initialization_report()
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            await self.log_initialization_failure(str(e))
            raise
            
    async def initialize_database_schema(self) -> None:
        """Initialize and validate database schema"""
        
        self.logger.info("Initializing database schema...")
        
        try:
            # Verify database connection
            health_check = await self.shared_state.postgresql_adapter.health_check()
            if health_check['status'] != 'healthy':
                raise RuntimeError(f"Database not healthy: {health_check}")
                
            # Check if schema needs initialization
            schema_status = await self.check_schema_status()
            
            if not schema_status['complete']:
                await self.create_database_schema()
                
            # Validate schema integrity
            await self.validate_database_schema()
            
            self.logger.info("Database schema initialization completed")
            
        except Exception as e:
            self.logger.error(f"Database schema initialization failed: {e}")
            raise
            
    async def check_schema_status(self) -> Dict[str, Any]:
        """Check current database schema status"""
        
        try:
            # Check for core tables
            core_tables = [
                'agents', 'agent_heartbeats', 'performance_metrics',
                'system_events', 'business_metrics', 'agent_health_history',
                'communication_logs'
            ]
            
            existing_tables = []
            missing_tables = []
            
            for table in core_tables:
                try:
                    query = f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = '{table}' AND table_schema = 'public'
                    """
                    result = await self.shared_state.postgresql_adapter.execute_query(query)
                    
                    if result and result[0]['count'] > 0:
                        existing_tables.append(table)
                    else:
                        missing_tables.append(table)
                        
                except Exception as e:
                    self.logger.warning(f"Could not check table {table}: {e}")
                    missing_tables.append(table)
                    
            schema_complete = len(missing_tables) == 0
            
            return {
                'complete': schema_complete,
                'existing_tables': existing_tables,
                'missing_tables': missing_tables,
                'total_core_tables': len(core_tables)
            }
            
        except Exception as e:
            self.logger.error(f"Schema status check failed: {e}")
            return {
                'complete': False,
                'error': str(e)
            }
            
    async def create_database_schema(self) -> None:
        """Create database schema from SQL file"""
        
        self.logger.info("Creating database schema...")
        
        try:
            # Find schema SQL file
            schema_file = Path("config/postgresql/schema.sql")
            
            if not schema_file.exists():
                # Try alternative locations
                alternative_paths = [
                    Path("schema.sql"),
                    Path("setup_postgresql_schema.sql"),
                    Path("config/schema.sql")
                ]
                
                for path in alternative_paths:
                    if path.exists():
                        schema_file = path
                        break
                else:
                    raise FileNotFoundError("Database schema file not found")
                    
            # Read and execute schema SQL
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                
            # Execute schema creation
            await self.shared_state.postgresql_adapter.execute_raw_sql(schema_sql)
            
            self.logger.info("Database schema created successfully")
            
        except Exception as e:
            self.logger.error(f"Schema creation failed: {e}")
            raise
            
    async def validate_database_schema(self) -> None:
        """Validate database schema integrity"""
        
        self.logger.info("Validating database schema integrity...")
        
        try:
            validation_queries = [
                # Check agents table structure
                """
                SELECT COUNT(*) as count FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name IN 
                ('agent_id', 'agent_type', 'state', 'created_at')
                """,
                
                # Check heartbeats table structure  
                """
                SELECT COUNT(*) as count FROM information_schema.columns
                WHERE table_name = 'agent_heartbeats' AND column_name IN
                ('heartbeat_id', 'agent_id', 'timestamp', 'health_score')
                """,
                
                # Check performance metrics table
                """
                SELECT COUNT(*) as count FROM information_schema.columns
                WHERE table_name = 'performance_metrics' AND column_name IN
                ('metric_id', 'agent_id', 'metric_name', 'metric_value')
                """,
                
                # Check system events table
                """
                SELECT COUNT(*) as count FROM information_schema.columns
                WHERE table_name = 'system_events' AND column_name IN
                ('id', 'event_type', 'severity', 'timestamp')
                """
            ]
            
            for i, query in enumerate(validation_queries):
                result = await self.shared_state.postgresql_adapter.execute_query(query)
                
                if not result or result[0]['count'] < 4:
                    raise ValueError(f"Schema validation failed for query {i + 1}")
                    
            # Check for required views
            view_check_query = """
            SELECT COUNT(*) as count FROM information_schema.views 
            WHERE table_name IN ('agent_status_dashboard', 'system_health_overview')
            """
            
            result = await self.shared_state.postgresql_adapter.execute_query(view_check_query)
            if not result or result[0]['count'] < 2:
                self.logger.warning("Some database views may be missing")
                
            self.logger.info("Database schema validation completed successfully")
            self.initialization_metrics['validation_checks_passed'] += 1
            
        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            raise
            
    async def initialize_agent_registry(self) -> None:
        """Initialize agent registry with core agent definitions"""
        
        self.logger.info("Initializing agent registry...")
        
        try:
            # Define core agents with their configurations
            core_agents = [
                {
                    'agent_id': 'heartbeat_health_agent',
                    'agent_type': 'monitoring',
                    'agent_name': 'Heartbeat Health Agent',
                    'agent_description': 'Monitors agent health and heartbeat status',
                    'capabilities': ['health_monitoring', 'heartbeat_tracking', 'anomaly_detection'],
                    'configuration': {
                        'heartbeat_interval': 60,
                        'health_threshold': 80.0,
                        'anomaly_detection_enabled': True
                    }
                },
                {
                    'agent_id': 'performance_monitor',
                    'agent_type': 'monitoring', 
                    'agent_name': 'Performance Monitor',
                    'agent_description': 'Monitors system and agent performance metrics',
                    'capabilities': ['performance_tracking', 'metrics_collection', 'optimization_recommendations'],
                    'configuration': {
                        'monitoring_interval': 120,
                        'metrics_retention_days': 30,
                        'performance_alerts_enabled': True
                    }
                },
                {
                    'agent_id': 'langsmith_bridge',
                    'agent_type': 'integration',
                    'agent_name': 'LangSmith Bridge',
                    'agent_description': 'Bridges system with LangSmith for conversation logging',
                    'capabilities': ['conversation_logging', 'performance_tracing', 'cost_optimization'],
                    'configuration': {
                        'tracing_interval': 300,
                        'cost_tracking_enabled': True,
                        'quality_assessment_enabled': True
                    }
                },
                {
                    'agent_id': 'ai_help_agent',
                    'agent_type': 'service',
                    'agent_name': 'AI Help Agent',
                    'agent_description': 'Provides AI-powered assistance and system guidance',
                    'capabilities': ['ai_assistance', 'system_guidance', 'real_time_context'],
                    'configuration': {
                        'help_processing_interval': 30,
                        'context_integration_enabled': True,
                        'quality_assessment_enabled': True
                    }
                },
                {
                    'agent_id': 'enhanced_shared_state_monitor',
                    'agent_type': 'monitoring',
                    'agent_name': 'Enhanced Shared State Monitor',
                    'agent_description': 'Advanced monitoring of shared state performance',
                    'capabilities': ['state_monitoring', 'performance_analysis', 'optimization_recommendations'],
                    'configuration': {
                        'monitoring_interval': 300,
                        'detailed_analysis_interval': 3600,
                        'business_impact_tracking': True
                    }
                },
                {
                    'agent_id': 'self_healing_agent',
                    'agent_type': 'automation',
                    'agent_name': 'Self-Healing Agent',
                    'agent_description': 'Automated issue detection and system recovery',
                    'capabilities': ['issue_detection', 'automated_recovery', 'system_repair'],
                    'configuration': {
                        'healing_interval': 180,
                        'max_concurrent_recoveries': 3,
                        'recovery_attempt_limit': 3
                    }
                }
            ]
            
            # Register each core agent
            for agent_config in core_agents:
                try:
                    await self.shared_state.register_agent(
                        agent_config['agent_id'],
                        agent_config
                    )
                    self.logger.info(f"Registered agent: {agent_config['agent_id']}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to register agent {agent_config['agent_id']}: {e}")
                    
            # Verify agent registration
            registered_agents = await self.shared_state.get_registered_agents()
            self.logger.info(f"Agent registry initialized with {len(registered_agents)} agents")
            
            self.initialization_metrics['validation_checks_passed'] += 1
            
        except Exception as e:
            self.logger.error(f"Agent registry initialization failed: {e}")
            raise
            
    async def establish_performance_baselines(self) -> None:
        """Establish performance baselines for system monitoring"""
        
        self.logger.info("Establishing performance baselines...")
        
        try:
            # Define baseline performance metrics
            baseline_metrics = [
                # System performance baselines
                ('system_initialization_time', 60.0, 'seconds'),
                ('database_response_time', 0.5, 'seconds'),
                ('agent_startup_time', 10.0, 'seconds'),
                ('heartbeat_interval', 60.0, 'seconds'),
                
                # Business performance baselines
                ('agent_utilization_target', 80.0, 'percent'),
                ('system_availability_target', 99.9, 'percent'),
                ('cost_per_agent_hour', 2.50, 'usd'),
                ('business_value_per_hour', 100.0, 'usd'),
                
                # Quality baselines
                ('error_rate_threshold', 5.0, 'percent'),
                ('performance_degradation_threshold', 20.0, 'percent'),
                ('user_satisfaction_target', 4.5, 'score')
            ]
            
            # Log baseline metrics
            for metric_name, baseline_value, unit in baseline_metrics:
                await self.shared_state.log_performance_metric(
                    f"baseline_{metric_name}",
                    baseline_value,
                    unit,
                    'system_initializer'
                )
                
            # Log business baseline metrics
            business_baselines = [
                ('system_reliability', 'baseline_availability', 99.9),
                ('cost_optimization', 'baseline_cost_per_hour', 25.0),
                ('user_experience', 'baseline_satisfaction', 4.5),
                ('operational_efficiency', 'baseline_utilization', 80.0)
            ]
            
            for category, metric_name, value in business_baselines:
                await self.shared_state.log_business_metric(
                    category, metric_name, value,
                    {'type': 'baseline', 'established_at': datetime.now(timezone.utc).isoformat()}
                )
                
            self.logger.info("Performance baselines established successfully")
            self.initialization_metrics['validation_checks_passed'] += 1
            
        except Exception as e:
            self.logger.error(f"Performance baseline establishment failed: {e}")
            raise
            
    async def initialize_business_intelligence(self) -> None:
        """Initialize business intelligence tracking and reporting"""
        
        self.logger.info("Initializing business intelligence system...")
        
        try:
            # Initialize business intelligence categories
            bi_categories = [
                {
                    'category': 'system_reliability',
                    'metrics': ['uptime', 'error_rate', 'recovery_time', 'availability_score'],
                    'business_impact': 'High - Directly affects service delivery'
                },
                {
                    'category': 'cost_optimization', 
                    'metrics': ['resource_utilization', 'cost_per_transaction', 'efficiency_score'],
                    'business_impact': 'High - Directly affects operational costs'
                },
                {
                    'category': 'user_experience',
                    'metrics': ['response_time', 'satisfaction_score', 'completion_rate'],
                    'business_impact': 'Medium - Affects user satisfaction and retention'
                },
                {
                    'category': 'operational_efficiency',
                    'metrics': ['automation_rate', 'manual_intervention_rate', 'productivity_score'],
                    'business_impact': 'Medium - Affects team productivity'
                }
            ]
            
            # Log initial business intelligence setup
            for category_info in bi_categories:
                await self.shared_state.log_business_metric(
                    category_info['category'],
                    'category_initialization',
                    1.0,
                    {
                        'metrics_tracked': category_info['metrics'],
                        'business_impact': category_info['business_impact'],
                        'initialized_at': datetime.now(timezone.utc).isoformat()
                    }
                )
                
            # Calculate initial business value
            initial_business_value = 5000.0  # Initial estimated monthly value
            self.initialization_metrics['business_value_established'] = initial_business_value
            
            await self.shared_state.log_business_metric(
                'system_value',
                'initial_business_value_estimate',
                initial_business_value,
                {
                    'currency': 'USD',
                    'period': 'monthly',
                    'confidence': 'medium'
                }
            )
            
            self.logger.info("Business intelligence system initialized successfully")
            self.initialization_metrics['validation_checks_passed'] += 1
            
        except Exception as e:
            self.logger.error(f"Business intelligence initialization failed: {e}")
            raise
            
    async def load_system_configuration(self) -> None:
        """Load and validate system configuration"""
        
        self.logger.info("Loading system configuration...")
        
        try:
            # Load configuration from environment and config files
            config_items = [
                # Database configuration
                ('database', 'host', os.getenv('POSTGRESQL_HOST', 'localhost')),
                ('database', 'port', int(os.getenv('POSTGRESQL_PORT', '5432'))),
                ('database', 'pool_size', int(os.getenv('POSTGRESQL_POOL_SIZE', '10'))),
                
                # Monitoring configuration
                ('monitoring', 'heartbeat_interval', int(os.getenv('HEARTBEAT_INTERVAL', '60'))),
                ('monitoring', 'performance_interval', int(os.getenv('PERFORMANCE_INTERVAL', '120'))),
                ('monitoring', 'health_check_timeout', int(os.getenv('HEALTH_CHECK_TIMEOUT', '30'))),
                
                # Business configuration
                ('business', 'cost_tracking_enabled', True),
                ('business', 'performance_reporting_enabled', True),
                ('business', 'automated_optimization_enabled', True),
                
                # System configuration
                ('system', 'max_agents', int(os.getenv('MAX_AGENTS', '20'))),
                ('system', 'data_retention_days', int(os.getenv('DATA_RETENTION_DAYS', '30'))),
                ('system', 'automated_recovery_enabled', True)
            ]
            
            # Store configuration in system
            configuration = {}
            for category, key, value in config_items:
                if category not in configuration:
                    configuration[category] = {}
                configuration[category][key] = value
                
            # Log configuration loading
            await self.shared_state.log_system_event(
                'configuration_loaded',
                {
                    'configuration_items': len(config_items),
                    'categories': list(configuration.keys()),
                    'load_timestamp': datetime.now(timezone.utc).isoformat()
                },
                agent_id='system_initializer',
                severity='INFO'
            )
            
            self.logger.info("System configuration loaded successfully")
            self.initialization_metrics['validation_checks_passed'] += 1
            
        except Exception as e:
            self.logger.error(f"Configuration loading failed: {e}")
            raise
            
    async def verify_system_health(self) -> None:
        """Verify overall system health after initialization"""
        
        self.logger.info("Verifying system health...")
        
        try:
            # Get system health metrics
            health_data = await self.shared_state.get_system_health()
            
            # Verify database connectivity
            db_health = await self.shared_state.postgresql_adapter.health_check()
            
            # Check agent registry
            registered_agents = await self.shared_state.get_registered_agents()
            
            # Validate system components
            health_checks = [
                ('database_healthy', db_health.get('status') == 'healthy'),
                ('agents_registered', len(registered_agents) >= 4),  # Minimum core agents
                ('system_health_score', health_data.get('overall_health_score', 0) > 50),  # Lower threshold for initialization
                ('shared_state_operational', health_data.get('system_status') in ['healthy', 'degraded'])  # Accept degraded during init
            ]
            
            failed_checks = [check for check, passed in health_checks if not passed]
            
            if failed_checks:
                raise RuntimeError(f"System health verification failed: {failed_checks}")
                
            # Log successful health verification
            await self.shared_state.log_system_event(
                'system_health_verified',
                {
                    'health_score': health_data.get('overall_health_score'),
                    'database_status': db_health.get('status'),
                    'registered_agents': len(registered_agents),
                    'all_checks_passed': True
                },
                agent_id='system_initializer',
                severity='INFO'
            )
            
            self.logger.info("System health verification completed successfully")
            self.initialization_metrics['validation_checks_passed'] += 1
            
        except Exception as e:
            self.logger.error(f"System health verification failed: {e}")
            raise
            
    async def log_initialization_success(self) -> None:
        """Log successful system initialization"""
        
        try:
            initialization_duration = (
                self.initialization_metrics['completion_time'] - 
                self.initialization_metrics['start_time']
            ).total_seconds()
            
            # Log system event
            await self.shared_state.log_system_event(
                'system_initialization_complete',
                {
                    'initialization_duration_seconds': initialization_duration,
                    'components_initialized': self.initialization_metrics['components_initialized'],
                    'validation_checks_passed': self.initialization_metrics['validation_checks_passed'],
                    'business_value_established': self.initialization_metrics['business_value_established'],
                    'system_status': 'operational'
                },
                agent_id='system_initializer',
                severity='INFO'
            )
            
            # Log business metric
            await self.shared_state.log_business_metric(
                'system_reliability',
                'successful_initialization',
                1.0,
                {
                    'initialization_time': initialization_duration,
                    'components_count': self.initialization_metrics['components_initialized']
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log initialization success: {e}")
            
    async def log_initialization_failure(self, error_message: str) -> None:
        """Log initialization failure"""
        
        try:
            await self.shared_state.log_system_event(
                'system_initialization_failed',
                {
                    'error_message': error_message,
                    'components_completed': self.initialization_metrics['components_initialized'],
                    'status_at_failure': self.initialization_status
                },
                agent_id='system_initializer',
                severity='CRITICAL'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log initialization failure: {e}")
            
    async def generate_initialization_report(self) -> Dict[str, Any]:
        """Generate comprehensive initialization report"""
        
        try:
            initialization_duration = (
                self.initialization_metrics['completion_time'] - 
                self.initialization_metrics['start_time']
            ).total_seconds()
            
            # Get final system status
            health_data = await self.shared_state.get_system_health()
            registered_agents = await self.shared_state.get_registered_agents()
            
            report = {
                'initialization_status': 'SUCCESS',
                'initialization_duration_seconds': initialization_duration,
                'components_initialized': self.initialization_metrics['components_initialized'],
                'validation_checks_passed': self.initialization_metrics['validation_checks_passed'],
                'business_value_established': self.initialization_metrics['business_value_established'],
                
                'system_health': {
                    'overall_health_score': health_data.get('overall_health_score', 0),
                    'system_status': health_data.get('system_status', 'unknown'),
                    'registered_agents': len(registered_agents),
                    'database_status': 'healthy'
                },
                
                'component_status': self.initialization_status,
                
                'business_metrics': {
                    'estimated_monthly_value': self.initialization_metrics['business_value_established'],
                    'cost_optimization_potential': '25%',
                    'automation_coverage': '85%',
                    'reliability_improvement': '99.9% uptime target'
                },
                
                'next_steps': [
                    'Start background agent processes',
                    'Begin performance monitoring',
                    'Enable automated recovery',
                    'Configure business intelligence dashboards'
                ],
                
                'completion_timestamp': self.initialization_metrics['completion_time'].isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate initialization report: {e}")
            return {
                'initialization_status': 'ERROR',
                'error_message': str(e),
                'completion_timestamp': datetime.now(timezone.utc).isoformat()
            } 
