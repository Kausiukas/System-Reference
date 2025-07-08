"""
Complete System Validation Test Suite

Comprehensive testing framework for the PostgreSQL-based
background agents system validation and live testing support.
"""

import asyncio
import logging
import time
import sys
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path
import json
import os

# Import system components
from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter, ConnectionConfig
from background_agents.coordination.shared_state import SharedState
from background_agents.coordination.system_initializer import SystemInitializer
from background_agents.coordination.agent_coordinator import AgentCoordinator

# Import agents for testing
from background_agents.monitoring.heartbeat_health_agent import HeartbeatHealthAgent
from background_agents.monitoring.performance_monitor import PerformanceMonitor
from background_agents.monitoring.langsmith_bridge import LangSmithBridge
from background_agents.ai_help.ai_help_agent import AIHelpAgent


class SystemValidator:
    """Comprehensive system validation"""
    
    def __init__(self):
        self.logger = logging.getLogger("system_validator")
        self.test_results = []
        self.start_time = None
        
        # System components
        self.postgresql_adapter = None
        self.shared_state = None
        self.system_initializer = None
        self.agent_coordinator = None
        
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete system validation"""
        
        self.start_time = datetime.now(timezone.utc)
        self.logger.info("Starting complete system validation...")
        
        try:
            # Test 1: Database Connectivity
            await self.test_database_connectivity()
            
            # Test 2: Schema Validation
            await self.test_database_schema()
            
            # Test 3: Shared State Operations
            await self.test_shared_state_operations()
            
            # Test 4: Agent Registration
            await self.test_agent_registration()
            
            # Test 5: System Initialization
            await self.test_system_initialization()
            
            # Test 6: Agent Coordination
            await self.test_agent_coordination()
            
            # Test 7: Performance Monitoring
            await self.test_performance_monitoring()
            
            # Test 8: Business Intelligence
            await self.test_business_intelligence()
            
            # Test 9: Live System Integration
            await self.test_live_system_integration()
            
            return self.generate_validation_report()
            
        except Exception as e:
            self.logger.error(f"System validation failed: {e}")
            return self.generate_error_report(str(e))
            
    async def test_database_connectivity(self) -> None:
        """Test PostgreSQL database connectivity"""
        
        test_name = "Database Connectivity"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Initialize PostgreSQL adapter
                    connection_config = ConnectionConfig(
            host=os.getenv('POSTGRESQL_HOST', 'localhost'),
            port=int(os.getenv('POSTGRESQL_PORT', '5432')),
            database=os.getenv('POSTGRESQL_DATABASE', 'background_agents'),
            user=os.getenv('POSTGRESQL_USER', 'postgres'),
            password=os.getenv('POSTGRESQL_PASSWORD', ''),
            min_connections=5,
            max_connections=10
        )
            
            self.postgresql_adapter = PostgreSQLAdapter(connection_config)
            await self.postgresql_adapter.initialize()
            
            # Test health check
            health_check = await self.postgresql_adapter.health_check()
            
            if health_check.get('status') == 'healthy':
                self.add_test_result(test_name, True, "Database connection successful")
            else:
                self.add_test_result(test_name, False, f"Database unhealthy: {health_check}")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"Database connection failed: {e}")
            raise
            
    async def test_database_schema(self) -> None:
        """Test database schema validity"""
        
        test_name = "Database Schema"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Check core tables
            core_tables = [
                'agents', 'agent_heartbeats', 'performance_metrics',
                'system_events', 'business_metrics'
            ]
            
            missing_tables = []
            
            for table in core_tables:
                query = f"""
                SELECT COUNT(*) as count FROM information_schema.tables 
                WHERE table_name = '{table}' AND table_schema = 'public'
                """
                result = await self.postgresql_adapter.execute_query(query)
                
                if not result or result[0]['count'] == 0:
                    missing_tables.append(table)
                    
            if not missing_tables:
                self.add_test_result(test_name, True, "All core tables present")
            else:
                self.add_test_result(test_name, False, f"Missing tables: {missing_tables}")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"Schema validation failed: {e}")
            
    async def test_shared_state_operations(self) -> None:
        """Test shared state operations"""
        
        test_name = "Shared State Operations"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Initialize shared state
            self.shared_state = SharedState(self.postgresql_adapter)
            await self.shared_state.initialize()
            
            # Test agent registration
            test_agent_data = {
                'agent_type': 'test',
                'agent_name': 'Test Agent',
                'capabilities': ['testing']
            }
            
            await self.shared_state.register_agent('test_agent_validation', test_agent_data)
            
            # Test agent retrieval
            agent_status = await self.shared_state.get_agent_status('test_agent_validation')
            
            # Test performance metric logging
            await self.shared_state.log_performance_metric(
                'test_metric', 42.0, 'test_unit', 'test_agent_validation'
            )
            
            # Test system event logging
            await self.shared_state.log_system_event(
                'validation_test', {'test': True}, 'test_agent_validation'
            )
            
            # Test business metric logging
            await self.shared_state.log_business_metric(
                'test_category', 'test_metric', 100.0
            )
            
            # Cleanup test data
            await self.cleanup_test_data()
            
            self.add_test_result(test_name, True, "All shared state operations successful")
            
        except Exception as e:
            self.add_test_result(test_name, False, f"Shared state operations failed: {e}")
            
    async def test_agent_registration(self) -> None:
        """Test agent registration process"""
        
        test_name = "Agent Registration"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Test registering core agents
            core_agents = [
                'heartbeat_health_agent',
                'performance_monitor', 
                'langsmith_bridge',
                'ai_help_agent'
            ]
            
            for agent_id in core_agents:
                agent_data = {
                    'agent_type': 'test',
                    'agent_name': f'Test {agent_id}',
                    'capabilities': ['testing']
                }
                
                await self.shared_state.register_agent(agent_id, agent_data)
                
            # Verify registrations
            registered_agents = await self.shared_state.get_registered_agents()
            registered_ids = [a.get('agent_id') for a in registered_agents]
            
            missing_agents = [aid for aid in core_agents if aid not in registered_ids]
            
            if not missing_agents:
                self.add_test_result(test_name, True, f"All {len(core_agents)} agents registered")
            else:
                self.add_test_result(test_name, False, f"Missing agents: {missing_agents}")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"Agent registration failed: {e}")
            
    async def test_system_initialization(self) -> None:
        """Test system initialization"""
        
        test_name = "System Initialization"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Initialize system initializer
            self.system_initializer = SystemInitializer(self.shared_state)
            
            # Run initialization (this is comprehensive)
            init_result = await self.system_initializer.initialize()
            
            if init_result.get('initialization_status') == 'SUCCESS':
                self.add_test_result(test_name, True, "System initialization successful")
            else:
                self.add_test_result(test_name, False, f"Initialization failed: {init_result}")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"System initialization failed: {e}")
            
    async def test_agent_coordination(self) -> None:
        """Test agent coordination"""
        
        test_name = "Agent Coordination"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Initialize agent coordinator
            self.agent_coordinator = AgentCoordinator(self.shared_state)
            await self.agent_coordinator.initialize()
            
            # Create test agent instance
            test_agent = HeartbeatHealthAgent(
                agent_id="test_heartbeat_agent",
                shared_state=self.shared_state
            )
            
            # Register with coordinator
            await self.agent_coordinator.register_agent(test_agent)
            
            # Test coordination operations
            agent_status = await self.agent_coordinator.get_agent_status("test_heartbeat_agent")
            
            if agent_status:
                self.add_test_result(test_name, True, "Agent coordination working")
            else:
                self.add_test_result(test_name, False, "Agent coordination failed")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"Agent coordination failed: {e}")
            
    async def test_performance_monitoring(self) -> None:
        """Test performance monitoring capabilities"""
        
        test_name = "Performance Monitoring"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Log various performance metrics
            test_metrics = [
                ('processing_time', 1.5, 'seconds'),
                ('memory_usage', 75.0, 'percent'),
                ('cpu_usage', 45.0, 'percent'),
                ('business_value_generated', 250.0, 'usd')
            ]
            
            for metric_name, value, unit in test_metrics:
                await self.shared_state.log_performance_metric(
                    metric_name, value, unit, 'test_agent'
                )
                
            # Retrieve performance metrics
            metrics = await self.shared_state.get_performance_metrics(hours=1)
            
            if len(metrics) >= len(test_metrics):
                self.add_test_result(test_name, True, f"Performance monitoring working - {len(metrics)} metrics")
            else:
                self.add_test_result(test_name, False, f"Metrics not logged properly: {len(metrics)}")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"Performance monitoring failed: {e}")
            
    async def test_business_intelligence(self) -> None:
        """Test business intelligence features"""
        
        test_name = "Business Intelligence"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Log business metrics
            business_test_data = [
                ('cost_optimization', 'efficiency_score', 85.0),
                ('system_reliability', 'uptime_percentage', 99.9),
                ('user_experience', 'satisfaction_score', 4.7),
                ('revenue_impact', 'monthly_value', 15000.0)
            ]
            
            for category, metric_name, value in business_test_data:
                await self.shared_state.log_business_metric(
                    category, metric_name, value, {'test': True}
                )
                
            # Retrieve business metrics
            business_metrics = await self.shared_state.get_business_metrics(hours=1)
            
            if len(business_metrics) >= len(business_test_data):
                self.add_test_result(test_name, True, f"Business intelligence working - {len(business_metrics)} metrics")
            else:
                self.add_test_result(test_name, False, f"Business metrics not logged properly")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"Business intelligence failed: {e}")
            
    async def test_live_system_integration(self) -> None:
        """Test live system integration capabilities"""
        
        test_name = "Live System Integration"
        
        try:
            self.logger.info(f"Testing: {test_name}")
            
            # Test system health check
            health_data = await self.shared_state.get_system_health()
            
            # Test performance summary
            performance_summary = await self.shared_state.get_system_performance_summary()
            
            # Test agent listing
            agents = await self.shared_state.get_registered_agents()
            
            # Test event retrieval
            events = await self.shared_state.get_system_events(hours=1)
            
            # Validate all components working
            if (health_data and performance_summary and 
                isinstance(agents, list) and isinstance(events, list)):
                self.add_test_result(test_name, True, "Live system integration successful")
            else:
                self.add_test_result(test_name, False, "Some integration components failed")
                
        except Exception as e:
            self.add_test_result(test_name, False, f"Live system integration failed: {e}")
            
    async def cleanup_test_data(self) -> None:
        """Clean up test data from database"""
        
        try:
            # Clean up test agents
            cleanup_query = """
            DELETE FROM agents WHERE agent_id LIKE 'test_%' OR agent_id = 'test_agent_validation'
            """
            await self.postgresql_adapter.execute_raw_sql(cleanup_query)
            
            # Clean up test metrics
            cleanup_query = """
            DELETE FROM performance_metrics WHERE agent_id LIKE 'test_%' OR metric_name = 'test_metric'
            """
            await self.postgresql_adapter.execute_raw_sql(cleanup_query)
            
            # Clean up test events
            cleanup_query = """
            DELETE FROM system_events WHERE event_type = 'validation_test'
            """
            await self.postgresql_adapter.execute_raw_sql(cleanup_query)
            
            # Clean up test business metrics
            cleanup_query = """
            DELETE FROM business_metrics WHERE category = 'test_category'
            """
            await self.postgresql_adapter.execute_raw_sql(cleanup_query)
            
        except Exception as e:
            self.logger.warning(f"Test data cleanup failed: {e}")
            
    def add_test_result(self, test_name: str, success: bool, message: str) -> None:
        """Add test result to results list"""
        
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} - {test_name}: {message}")
        
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / max(total_tests, 1)) * 100
        
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        report = {
            'validation_status': 'SUCCESS' if failed_tests == 0 else 'FAILED',
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'duration_seconds': duration,
            'test_results': self.test_results,
            'summary': {
                'database_connectivity': any(r['test_name'] == 'Database Connectivity' and r['success'] for r in self.test_results),
                'schema_validation': any(r['test_name'] == 'Database Schema' and r['success'] for r in self.test_results),
                'shared_state_ops': any(r['test_name'] == 'Shared State Operations' and r['success'] for r in self.test_results),
                'agent_registration': any(r['test_name'] == 'Agent Registration' and r['success'] for r in self.test_results),
                'system_initialization': any(r['test_name'] == 'System Initialization' and r['success'] for r in self.test_results),
                'agent_coordination': any(r['test_name'] == 'Agent Coordination' and r['success'] for r in self.test_results),
                'performance_monitoring': any(r['test_name'] == 'Performance Monitoring' and r['success'] for r in self.test_results),
                'business_intelligence': any(r['test_name'] == 'Business Intelligence' and r['success'] for r in self.test_results),
                'live_integration': any(r['test_name'] == 'Live System Integration' and r['success'] for r in self.test_results)
            },
            'recommendations': self.generate_recommendations(),
            'live_test_readiness': self.assess_live_test_readiness(),
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        return report
        
    def generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """Generate error report for failed validation"""
        
        return {
            'validation_status': 'ERROR',
            'error_message': error_message,
            'test_results': self.test_results,
            'failed_at': datetime.now(timezone.utc).isoformat()
        }
        
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r['success']]
        
        if not failed_tests:
            recommendations.append("✅ All tests passed - system ready for production use")
            recommendations.append("🚀 Proceed with live testing as documented in live_test.md")
            recommendations.append("📊 Enable monitoring dashboards for ongoing oversight")
        else:
            recommendations.append("⚠️ Address failed tests before proceeding to live testing")
            
            for test in failed_tests:
                if 'Database' in test['test_name']:
                    recommendations.append("🔧 Check PostgreSQL configuration and connectivity")
                elif 'Schema' in test['test_name']:
                    recommendations.append("📋 Run database schema creation script")
                elif 'Agent' in test['test_name']:
                    recommendations.append("🤖 Verify agent implementation and dependencies")
                elif 'Performance' in test['test_name']:
                    recommendations.append("📈 Check performance monitoring configuration")
                elif 'Business' in test['test_name']:
                    recommendations.append("💼 Validate business intelligence setup")
                    
        return recommendations
        
    def assess_live_test_readiness(self) -> Dict[str, Any]:
        """Assess readiness for live testing"""
        
        failed_tests = [r for r in self.test_results if not r['success']]
        critical_failures = []
        
        # Identify critical failures that block live testing
        critical_test_names = [
            'Database Connectivity',
            'Database Schema', 
            'Shared State Operations',
            'System Initialization'
        ]
        
        for test in failed_tests:
            if test['test_name'] in critical_test_names:
                critical_failures.append(test['test_name'])
                
        if not critical_failures:
            readiness_status = 'READY'
            readiness_message = "System is ready for live testing"
        else:
            readiness_status = 'NOT_READY'
            readiness_message = f"Critical failures prevent live testing: {critical_failures}"
            
        return {
            'status': readiness_status,
            'message': readiness_message,
            'critical_failures': critical_failures,
            'live_test_confidence': 'HIGH' if not critical_failures else 'LOW'
        }


async def main():
    """Main test execution"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/system_validation.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    print("🚀 Starting Complete System Validation")
    print("=" * 50)
    
    # Run validation
    validator = SystemValidator()
    report = await validator.run_complete_validation()
    
    # Display results
    print("\n📊 VALIDATION RESULTS")
    print("=" * 50)
    
    status_emoji = "✅" if report['validation_status'] == 'SUCCESS' else "❌"
    print(f"{status_emoji} Status: {report['validation_status']}")
    print(f"📋 Tests: {report['passed_tests']}/{report['total_tests']} passed ({report['success_rate']:.1f}%)")
    print(f"⏱️ Duration: {report['duration_seconds']:.1f} seconds")
    
    # Show individual test results
    print("\n📝 INDIVIDUAL TEST RESULTS")
    print("-" * 30)
    
    for result in report['test_results']:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test_name']}: {result['message']}")
        
    # Show recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 20)
    
    for rec in report['recommendations']:
        print(f"  {rec}")
        
    # Show live test readiness
    print("\n🔬 LIVE TEST READINESS")
    print("-" * 22)
    
    readiness = report['live_test_readiness']
    readiness_emoji = "✅" if readiness['status'] == 'READY' else "⚠️"
    print(f"{readiness_emoji} {readiness['message']}")
    print(f"🎯 Confidence: {readiness['live_test_confidence']}")
    
    # Save detailed report
    report_file = Path("logs/validation_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
        
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Clean up
    try:
        if validator.shared_state:
            await validator.shared_state.close()
        if validator.postgresql_adapter:
            await validator.postgresql_adapter.close()
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
        
    print("\n🎉 Validation Complete!")
    
    return report['validation_status'] == 'SUCCESS'


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
