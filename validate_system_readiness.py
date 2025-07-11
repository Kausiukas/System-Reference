#!/usr/bin/env python3
"""
System Readiness Validation

Comprehensive validation script to verify system readiness for deployment.
Tests file structure, environment configuration, dependencies, database connectivity,
and system component initialization.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Unicode-safe printing for Windows console compatibility
def safe_print(text):
    """Print text with fallback for Windows console encoding issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: replace ALL Unicode characters with ASCII equivalents
        fallback_text = (text
                        .replace('🚀', '[*]')
                        .replace('✅', '[+]')
                        .replace('❌', '[X]')
                        .replace('⚠️', '[!]')
                        .replace('💡', '[i]')
                        .replace('🎉', '[*]')
                        .replace('📊', '[=]')
                        .replace('🗄️', '[D]')
                        .replace('⚙️', '[*]')
                        .replace('📁', '[F]')
                        .replace('🔧', '[T]')
                        .replace('🐍', '[P]')
                        .replace('📄', '[R]')
                        .replace('🤖', '[A]')
                        .replace('🔍', '[S]')  # magnifying glass for search
                        .replace('📋', '[L]')  # clipboard for list
                        .replace('📝', '[N]'))  # memo for notes
        try:
            print(fallback_text)
        except UnicodeEncodeError:
            # Ultimate fallback: encode to ASCII and ignore errors
            ascii_text = text.encode('ascii', 'ignore').decode('ascii')
            print(ascii_text)

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def check_file_structure():
    """Check that all required files are present"""
    
    safe_print("🔍 Checking file structure...")
    
    required_files = [
        # Core coordination files
        "background_agents/__init__.py",
        "background_agents/coordination/__init__.py", 
        "background_agents/coordination/base_agent.py",
        "background_agents/coordination/postgresql_adapter.py",
        "background_agents/coordination/shared_state.py",
        "background_agents/coordination/agent_coordinator.py",
        "background_agents/coordination/system_initializer.py",
        
        # Monitoring agents
        "background_agents/monitoring/__init__.py",
        "background_agents/monitoring/heartbeat_health_agent.py",
        "background_agents/monitoring/performance_monitor.py", 
        "background_agents/monitoring/langsmith_bridge.py",
        "background_agents/monitoring/enhanced_shared_state_monitor.py",
        "background_agents/monitoring/self_healing_agent.py",
        
        # AI help agent
        "background_agents/ai_help/__init__.py",
        "background_agents/ai_help/ai_help_agent.py",
        
        # Configuration files
        "config/postgresql/schema.sql",
        "config/monitoring.yml",
        "config_template.env",
        
        # System files
        "launch_background_agents.py",
        "background_agents_dashboard.py",
        "test_complete_system.py",
        
        # Documentation
        "live_test.md",
        "shared_state_database_psql.md",
        "MIGRATION_SUMMARY.md"
    ]
    
    missing_files = []
    present_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            present_files.append(file_path)
        else:
            missing_files.append(file_path)
            
    safe_print(f"  ✅ Present: {len(present_files)} files")
    safe_print(f"  ❌ Missing: {len(missing_files)} files")
    
    if missing_files:
        safe_print("  Missing files:")
        for file in missing_files:
            safe_print(f"    - {file}")
        return False
    else:
        safe_print("  🎉 All required files present!")
        return True

def check_environment_variables():
    """Check essential environment variables"""
    
    safe_print("\n🔧 Checking environment configuration...")
    
    required_env_vars = [
        'POSTGRESQL_HOST',
        'POSTGRESQL_PORT', 
        'POSTGRESQL_DATABASE',
        'POSTGRESQL_USER'
    ]
    
    optional_env_vars = [
        'POSTGRESQL_PASSWORD',
        'HEARTBEAT_INTERVAL',
        'PERFORMANCE_INTERVAL',
        'DATA_RETENTION_DAYS'
    ]
    
    missing_required = []
    present_vars = {}
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            present_vars[var] = value
        else:
            missing_required.append(var)
            
    for var in optional_env_vars:
        value = os.getenv(var)
        if value:
            present_vars[var] = value
            
    safe_print(f"  ✅ Present: {len(present_vars)} environment variables")
    safe_print(f"  ❌ Missing required: {len(missing_required)} variables")
    
    if missing_required:
        safe_print("  Missing required environment variables:")
        for var in missing_required:
            safe_print(f"    - {var}")
        safe_print("  💡 Create a .env file or set these variables")
        return False
    else:
        safe_print("  🎉 All required environment variables present!")
        return True

def check_python_imports():
    """Check that all Python modules can be imported"""
    
    safe_print("\n🐍 Checking Python imports...")
    
    import_tests = [
        ("PostgreSQL Adapter", "background_agents.coordination.postgresql_adapter"),
        ("Shared State", "background_agents.coordination.shared_state"),
        ("Base Agent", "background_agents.coordination.base_agent"), 
        ("Agent Coordinator", "background_agents.coordination.agent_coordinator"),
        ("System Initializer", "background_agents.coordination.system_initializer"),
        ("Heartbeat Agent", "background_agents.monitoring.heartbeat_health_agent"),
        ("Performance Monitor", "background_agents.monitoring.performance_monitor"),
        ("LangSmith Bridge", "background_agents.monitoring.langsmith_bridge"),
        ("AI Help Agent", "background_agents.ai_help.ai_help_agent")
    ]
    
    import_failures = []
    import_successes = []
    
    for name, module_path in import_tests:
        try:
            __import__(module_path)
            import_successes.append(name)
        except ImportError as e:
            import_failures.append((name, str(e)))
            
    safe_print(f"  ✅ Successful imports: {len(import_successes)}")
    safe_print(f"  ❌ Failed imports: {len(import_failures)}")
    
    if import_failures:
        safe_print("  Import failures:")
        for name, error in import_failures:
            safe_print(f"    - {name}: {error}")
        return False
    else:
        safe_print("  🎉 All imports successful!")
        return True

async def check_database_connection():
    """Check database connectivity"""
    
    safe_print("\n🗄️ Checking database connectivity...")
    
    try:
        from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter, ConnectionConfig
        
        connection_config = ConnectionConfig(
            host=os.getenv('POSTGRESQL_HOST', 'localhost'),
            port=int(os.getenv('POSTGRESQL_PORT', '5432')),
            database=os.getenv('POSTGRESQL_DATABASE', 'background_agents'),
            user=os.getenv('POSTGRESQL_USER', 'postgres'),
            password=os.getenv('POSTGRESQL_PASSWORD', ''),
            min_connections=2,
            max_connections=5
        )
        
        adapter = PostgreSQLAdapter(connection_config)
        await adapter.initialize()
        
        health_check = await adapter.health_check()
        await adapter.close()
        
        if health_check.get('status') == 'healthy':
            safe_print(f"  ✅ Database connection successful")
            safe_print(f"  📊 Response time: {health_check.get('response_time_seconds', 0):.3f}s")
            return True
        else:
            safe_print(f"  ❌ Database unhealthy: {health_check}")
            return False
            
    except Exception as e:
        safe_print(f"  ❌ Database connection failed: {e}")
        return False

async def check_system_components():
    """Check that system components can be initialized"""
    
    safe_print("\n⚙️ Checking system components...")
    
    try:
        from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter, ConnectionConfig
        from background_agents.coordination.shared_state import SharedState
        
        # Initialize components
        connection_config = ConnectionConfig(
            host=os.getenv('POSTGRESQL_HOST', 'localhost'),
            port=int(os.getenv('POSTGRESQL_PORT', '5432')),
            database=os.getenv('POSTGRESQL_DATABASE', 'background_agents'),
            user=os.getenv('POSTGRESQL_USER', 'postgres'),
            password=os.getenv('POSTGRESQL_PASSWORD', ''),
            min_connections=2,
            max_connections=5
        )
        
        adapter = PostgreSQLAdapter(connection_config)
        await adapter.initialize()
        
        shared_state = SharedState(adapter)
        await shared_state.initialize()
        
        # Test basic operations
        await shared_state.log_system_event(
            'system_readiness_check',
            {'test': True, 'timestamp': datetime.now(timezone.utc).isoformat()},
            severity='INFO'
        )
        
        # Cleanup
        await shared_state.close()
        await adapter.close()
        
        safe_print("  ✅ System components working correctly")
        return True
        
    except Exception as e:
        safe_print(f"  ❌ System component check failed: {e}")
        return False

def generate_readiness_report(checks_results):
    """Generate comprehensive readiness report"""
    
    total_checks = len(checks_results)
    passed_checks = sum(1 for result in checks_results.values() if result)
    
    success_rate = (passed_checks / total_checks) * 100
    
    report = {
        'readiness_status': 'READY' if passed_checks == total_checks else 'NOT_READY',
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'success_rate': success_rate,
        'check_results': checks_results,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    return report

async def main():
    """Main validation function"""
    
    setup_logging()
    
    safe_print("🚀 System Readiness Validation")
    safe_print("=" * 40)
    safe_print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    safe_print("")
    
    # Run all checks
    checks_results = {}
    
    # File structure check
    checks_results['file_structure'] = check_file_structure()
    
    # Environment variables check
    checks_results['environment_config'] = check_environment_variables()
    
    # Python imports check
    checks_results['python_imports'] = check_python_imports()
    
    # Database connectivity check (only if previous checks pass)
    if checks_results['python_imports'] and checks_results['environment_config']:
        checks_results['database_connectivity'] = await check_database_connection()
    else:
        checks_results['database_connectivity'] = False
        safe_print("\n🗄️ Skipping database check due to previous failures")
        
    # System components check (only if database check passes)
    if checks_results.get('database_connectivity'):
        checks_results['system_components'] = await check_system_components()
    else:
        checks_results['system_components'] = False
        safe_print("\n⚙️ Skipping system components check due to database issues")
        
    # Generate report
    report = generate_readiness_report(checks_results)
    
    # Display results
    safe_print("\n📊 READINESS SUMMARY")
    safe_print("=" * 30)
    
    status_emoji = "✅" if report['readiness_status'] == 'READY' else "❌"
    safe_print(f"{status_emoji} Status: {report['readiness_status']}")
    safe_print(f"📋 Checks: {report['passed_checks']}/{report['total_checks']} passed ({report['success_rate']:.1f}%)")
    
    # Show individual check results
    safe_print("\n📝 CHECK RESULTS")
    safe_print("-" * 20)
    
    check_names = {
        'file_structure': 'File Structure',
        'environment_config': 'Environment Config',
        'python_imports': 'Python Imports', 
        'database_connectivity': 'Database Connectivity',
        'system_components': 'System Components'
    }
    
    for check_key, result in checks_results.items():
        status = "✅" if result else "❌"
        name = check_names.get(check_key, check_key)
        safe_print(f"{status} {name}")
        
    # Recommendations
    safe_print("\n💡 RECOMMENDATIONS")
    safe_print("-" * 20)
    
    if report['readiness_status'] == 'READY':
        safe_print("  ✅ System is ready for live testing!")
        safe_print("  🚀 Run: python test_complete_system.py")
        safe_print("  📊 Start dashboard: streamlit run background_agents_dashboard.py")
        safe_print("  🤖 Launch agents: python launch_background_agents.py")
    else:
        safe_print("  ⚠️ Address failed checks before proceeding")
        
        if not checks_results.get('file_structure'):
            safe_print("  📁 Ensure all required files are present")
        if not checks_results.get('environment_config'):
            safe_print("  🔧 Configure environment variables")
        if not checks_results.get('python_imports'):
            safe_print("  🐍 Check Python dependencies and imports")
        if not checks_results.get('database_connectivity'):
            safe_print("  🗄️ Verify PostgreSQL database setup")
        if not checks_results.get('system_components'):
            safe_print("  ⚙️ Check system component initialization")
            
    # Save report
    report_path = Path("logs/readiness_report.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    safe_print(f"\n📄 Report saved: {report_path}")
    safe_print("\n🎉 Readiness validation complete!")
    
    return report['readiness_status'] == 'READY'

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 