#!/usr/bin/env python3
"""
PostgreSQL Migration Test Suite

Comprehensive test suite for validating the PostgreSQL migration and system functionality.
Tests all critical components including database operations, agent lifecycle, and system integration.
"""

import asyncio
import logging
import os
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from background_agents.coordination.shared_state import SharedState
from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgreSQLMigrationTester:
    """
    Comprehensive test suite for PostgreSQL migration validation.
    
    Tests include:
    1. Environment validation
    2. Database connectivity
    3. Schema validation
    4. Shared state operations
    5. Agent lifecycle management
    6. Performance metrics
    7. AI help system
    8. Dashboard compatibility
    9. System integration
    """
    
    def __init__(self):
        """Initialize the test suite."""
        self.results = {}
        self.shared_state = None
        self.adapter = None
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        
        logger.info("PostgreSQL Migration Test Suite initialized")
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        print("\n" + "=" * 80)
        print("PostgreSQL Migration Test Suite")
        print("=" * 80)
        
        test_methods = [
            self.test_environment_validation,
            self.test_database_connectivity,
            self.test_schema_validation,
            self.test_shared_state_operations,
            self.test_agent_lifecycle_management,
            self.test_performance_metrics,
            self.test_ai_help_system,
            self.test_dashboard_compatibility,
            self.test_system_integration
        ]
        
        start_time = time.time()
        
        for test_method in test_methods:
            await self._run_test(test_method)
        
        end_time = time.time()
        
        # Print final results
        self._print_test_summary(end_time - start_time)
        
        return self.passed_count == self.test_count
    
    async def _run_test(self, test_method):
        """Run a single test method with error handling."""
        test_name = test_method.__name__
        self.test_count += 1
        
        print(f"\n[{self.test_count}/9] Running {test_name}...")
        
        try:
            result = await test_method()
            if result:
                print(f"✅ {test_name}: PASSED")
                self.passed_count += 1
                self.results[test_name] = {"status": "PASSED", "error": None}
            else:
                print(f"❌ {test_name}: FAILED")
                self.failed_count += 1
                self.results[test_name] = {"status": "FAILED", "error": "Test returned False"}
                
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            self.failed_count += 1
            self.results[test_name] = {"status": "FAILED", "error": str(e)}
            logger.error(f"Test {test_name} failed: {e}")
            logger.error(traceback.format_exc())
    
    async def test_environment_validation(self) -> bool:
        """Test 1: Environment Validation"""
        try:
            required_vars = [
                'POSTGRESQL_HOST', 'POSTGRESQL_PORT', 'POSTGRESQL_DB', 'POSTGRESQL_USER', 'POSTGRESQL_PASSWORD'
            ]
            
            missing_vars = []
            for var in required_vars:
                value = os.getenv(var)
                if not value:
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"   Missing environment variables: {missing_vars}")
                return False
            
            # Check Python version
            if sys.version_info < (3, 8):
                print(f"   Python version {sys.version} is too old (requires 3.8+)")
                return False
            
            # Check required packages
            try:
                import asyncpg
                import psycopg2
                print("   ✓ Required packages available")
            except ImportError as e:
                print(f"   Missing required package: {e}")
                return False
            
            print("   ✓ Environment validation successful")
            return True
            
        except Exception as e:
            print(f"   Environment validation error: {e}")
            return False
    
    async def test_database_connectivity(self) -> bool:
        """Test 2: Database Connectivity"""
        try:
            # Create PostgreSQL adapter
            self.adapter = PostgreSQLAdapter()
            await self.adapter.initialize()
            
            # Test basic connectivity
            health_check = await self.adapter.health_check()
            if not health_check:
                print("   Database health check failed")
                return False
            
            # Test version query
            version = await self.adapter.execute_query(
                "SELECT version()", 
                fetch_mode='val'
            )
            print(f"   ✓ Connected to: {version[:50]}...")
            
            # Test connection pool
            stats = await self.adapter.get_database_stats()
            print(f"   ✓ Connection pool: {stats.get('pool_size', 0)} connections")
            
            return True
            
        except Exception as e:
            print(f"   Database connectivity error: {e}")
            return False
    
    async def test_schema_validation(self) -> bool:
        """Test 3: Schema Validation"""
        try:
            if not self.adapter:
                print("   No database adapter available")
                return False
            
            # Check required tables
            required_tables = [
                'agents', 'agent_heartbeats', 'performance_metrics',
                'system_state', 'system_events', 'help_requests',
                'help_responses', 'agent_communications', 'llm_conversations'
            ]
            
            existing_tables = await self.adapter.execute_query("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """, fetch_mode='all')
            
            existing_table_names = [row['table_name'] for row in existing_tables]
            
            missing_tables = []
            for table in required_tables:
                if table not in existing_table_names:
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"   Missing tables: {missing_tables}")
                return False
            
            print(f"   ✓ All {len(required_tables)} required tables exist")
            
            # Check indexes
            indexes = await self.adapter.execute_query("""
                SELECT COUNT(*) FROM pg_indexes 
                WHERE schemaname = 'public'
            """, fetch_mode='val')
            
            print(f"   ✓ Database has {indexes} indexes")
            
            return True
            
        except Exception as e:
            print(f"   Schema validation error: {e}")
            return False
    
    async def test_shared_state_operations(self) -> bool:
        """Test 4: Shared State Operations"""
        try:
            # Initialize shared state
            self.shared_state = SharedState(self.adapter)
            await self.shared_state.initialize()
            
            # Test agent registration
            test_agent_id = f"test_agent_{uuid.uuid4().hex[:8]}"
            await self.shared_state.register_agent(
                test_agent_id, 
                {'test': True, 'timestamp': datetime.now(timezone.utc).isoformat()}
            )
            
            # Test agent state update
            await self.shared_state.update_agent_state(
                test_agent_id, 
                'running',
                {'status': 'test_running'}
            )
            
            # Test getting agent status
            agent_status = await self.shared_state.get_agent_status(test_agent_id)
            if not agent_status or agent_status.get('state') != 'running':
                print("   Agent state update failed")
                return False
            
            # Test system state operations
            test_key = f"test_key_{uuid.uuid4().hex[:8]}"
            test_value = {'test': True, 'timestamp': time.time()}
            
            await self.shared_state.set_system_state(test_key, test_value, 'test_suite')
            retrieved_value = await self.shared_state.get_system_state(test_key)
            
            if retrieved_value != test_value:
                print("   System state operations failed")
                return False
            
            print("   ✓ Agent registration and state management working")
            print("   ✓ System state operations working")
            
            return True
            
        except Exception as e:
            print(f"   Shared state operations error: {e}")
            return False
    
    async def test_agent_lifecycle_management(self) -> bool:
        """Test 5: Agent Lifecycle Management"""
        try:
            if not self.shared_state:
                print("   No shared state available")
                return False
            
            # Test heartbeat logging
            test_agent_id = f"lifecycle_test_{uuid.uuid4().hex[:8]}"
            
            await self.shared_state.register_agent(test_agent_id, {'test_type': 'lifecycle'})
            
            # Test heartbeat
            heartbeat_data = {
                'state': 'running',
                'error_count': 0,
                'work_cycles_completed': 5,
                'uptime_seconds': 300,
                'metrics': {'cpu_usage': 25.5, 'memory_usage': 45.2}
            }
            
            await self.shared_state.update_agent_heartbeat(
                test_agent_id,
                datetime.now(timezone.utc),
                heartbeat_data
            )
            
            # Verify heartbeat was logged
            recent_heartbeats = await self.shared_state.get_recent_heartbeats(test_agent_id, minutes=1)
            if not recent_heartbeats:
                print("   Heartbeat logging failed")
                return False
            
            # Test health check
            is_healthy = await self.shared_state.check_agent_health(test_agent_id)
            if not is_healthy:
                print("   Agent health check failed")
                return False
            
            print("   ✓ Agent lifecycle management working")
            print("   ✓ Heartbeat system operational")
            
            return True
            
        except Exception as e:
            print(f"   Agent lifecycle management error: {e}")
            return False
    
    async def test_performance_metrics(self) -> bool:
        """Test 6: Performance Metrics"""
        try:
            if not self.shared_state:
                print("   No shared state available")
                return False
            
            test_agent_id = f"perf_test_{uuid.uuid4().hex[:8]}"
            
            # Log various performance metrics
            metrics_to_log = [
                ('cpu_usage', 65.5, 'percent'),
                ('memory_usage', 72.3, 'percent'),
                ('disk_usage', 45.8, 'percent'),
                ('response_time', 250.5, 'milliseconds'),
                ('throughput', 1250.0, 'requests_per_second')
            ]
            
            for metric_name, value, unit in metrics_to_log:
                await self.shared_state.log_performance_metric(
                    test_agent_id,
                    metric_name,
                    value,
                    unit,
                    {'test': True}
                )
            
            # Retrieve metrics
            metrics = await self.shared_state.get_performance_metrics(test_agent_id, hours=1)
            if len(metrics) != len(metrics_to_log):
                print(f"   Expected {len(metrics_to_log)} metrics, got {len(metrics)}")
                return False
            
            # Test performance summary
            summary = await self.shared_state.get_performance_summary(test_agent_id, hours=1)
            if not summary or len(summary) != len(metrics_to_log):
                print("   Performance summary generation failed")
                return False
            
            print(f"   ✓ Performance metrics logging working ({len(metrics)} metrics)")
            print("   ✓ Performance summary generation working")
            
            return True
            
        except Exception as e:
            print(f"   Performance metrics error: {e}")
            return False
    
    async def test_ai_help_system(self) -> bool:
        """Test 7: AI Help System"""
        try:
            if not self.shared_state:
                print("   No shared state available")
                return False
            
            # Test help request creation
            request_id = await self.shared_state.create_help_request(
                'test_user',
                'This is a test help request for system validation',
                {'test': True, 'priority': 'medium'}
            )
            
            if not request_id:
                print("   Help request creation failed")
                return False
            
            # Test help response creation
            response_id = await self.shared_state.create_help_response(
                request_id,
                'This is a test response to validate the help system functionality.',
                confidence_score=0.85,
                sources=['test_doc_1', 'test_doc_2'],
                agent_id='test_ai_agent'
            )
            
            if not response_id:
                print("   Help response creation failed")
                return False
            
            # Test retrieval
            requests = await self.shared_state.get_help_requests()
            responses = await self.shared_state.get_help_responses(request_id)
            
            if not requests or not responses:
                print("   Help request/response retrieval failed")
                return False
            
            print("   ✓ Help request/response system working")
            print(f"   ✓ Created request {request_id[:8]}... and response {response_id[:8]}...")
            
            return True
            
        except Exception as e:
            print(f"   AI help system error: {e}")
            return False
    
    async def test_dashboard_compatibility(self) -> bool:
        """Test 8: Dashboard Compatibility"""
        try:
            if not self.shared_state:
                print("   No shared state available")
                return False
            
            # Test data retrieval for dashboard
            agents = await self.shared_state.get_registered_agents()
            active_agents = await self.shared_state.get_active_agents()
            recent_heartbeats = await self.shared_state.get_recent_heartbeats(minutes=10)
            performance_metrics = await self.shared_state.get_performance_metrics(hours=1)
            system_events = await self.shared_state.get_system_events(hours=24)
            
            print(f"   ✓ Agents: {len(agents)} registered, {len(active_agents)} active")
            print(f"   ✓ Recent heartbeats: {len(recent_heartbeats)}")
            print(f"   ✓ Performance metrics: {len(performance_metrics)}")
            print(f"   ✓ System events: {len(system_events)}")
            
            # Test system health
            health_status = await self.shared_state.get_system_health()
            if not health_status or 'health_percentage' not in health_status:
                print("   System health check failed")
                return False
            
            print(f"   ✓ System health: {health_status['health_percentage']:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"   Dashboard compatibility error: {e}")
            return False
    
    async def test_system_integration(self) -> bool:
        """Test 9: System Integration"""
        try:
            if not self.shared_state:
                print("   No shared state available")
                return False
            
            # Test end-to-end workflow
            test_agent_id = f"integration_test_{uuid.uuid4().hex[:8]}"
            
            # 1. Register agent
            await self.shared_state.register_agent(test_agent_id, {'integration_test': True})
            
            # 2. Update state to running
            await self.shared_state.update_agent_state(test_agent_id, 'running')
            
            # 3. Log heartbeat
            await self.shared_state.update_agent_heartbeat(
                test_agent_id,
                datetime.now(timezone.utc),
                {'state': 'running', 'error_count': 0}
            )
            
            # 4. Log performance metrics
            await self.shared_state.log_performance_metric(
                test_agent_id, 'integration_test_metric', 42.0, 'units'
            )
            
            # 5. Log system event
            await self.shared_state.log_system_event(
                'integration_test_event',
                {'test': True, 'agent_id': test_agent_id},
                agent_id=test_agent_id
            )
            
            # 6. Create help request
            help_request_id = await self.shared_state.create_help_request(
                'integration_user',
                'Integration test help request'
            )
            
            # 7. Create help response
            await self.shared_state.create_help_response(
                help_request_id,
                'Integration test response',
                agent_id=test_agent_id
            )
            
            # 8. Get system statistics
            stats = await self.shared_state.get_statistics()
            if not stats:
                print("   System statistics retrieval failed")
                return False
            
            # 9. Get system context
            context = await self.shared_state.get_system_context()
            if not context:
                print("   System context retrieval failed")
                return False
            
            print("   ✓ End-to-end workflow completed successfully")
            print(f"   ✓ Database stats: {stats.get('agents', 0)} agents, {stats.get('heartbeats', 0)} heartbeats")
            
            return True
            
        except Exception as e:
            print(f"   System integration error: {e}")
            return False
    
    def _print_test_summary(self, duration: float):
        """Print test results summary."""
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {self.passed_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Success Rate: {(self.passed_count/self.test_count)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if self.failed_count > 0:
            print("\nFAILED TESTS:")
            for test_name, result in self.results.items():
                if result['status'] == 'FAILED':
                    print(f"  ❌ {test_name}: {result['error']}")
        
        print("\nDETAILED RESULTS:")
        for test_name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"  {status_icon} {test_name}: {result['status']}")
        
        if self.passed_count == self.test_count:
            print("\n🎉 ALL TESTS PASSED! PostgreSQL migration is successful.")
        else:
            print(f"\n⚠️  {self.failed_count} test(s) failed. Please review and fix issues.")
        
        print("=" * 80)
    
    async def cleanup(self):
        """Cleanup test resources."""
        try:
            if self.shared_state:
                await self.shared_state.close()
            if self.adapter:
                await self.adapter.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

async def main():
    """Main test runner."""
    tester = PostgreSQLMigrationTester()
    
    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"\nFatal error: {e}")
        logger.error(traceback.format_exc())
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 