#!/usr/bin/env python3
"""
Automated Test Runner

Comprehensive automated test suite that:
1. Installs required dependencies
2. Loads environment variables from .env file
3. Executes validate_system_readiness.py
4. Runs PostgreSQL migration tests
5. Provides detailed reporting

This script enables one-command testing for the entire system.
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomatedTestRunner:
    """
    Automated test runner for the Background Agents System.
    
    Provides comprehensive testing capabilities including dependency management,
    environment setup, and execution of all validation tests.
    """
    
    def __init__(self):
        """Initialize the automated test runner."""
        self.project_root = Path(__file__).parent
        self.results = {}
        self.start_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        logger.info("Automated Test Runner initialized")
    
    async def run_complete_test_suite(self) -> bool:
        """
        Run the complete automated test suite.
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        self.start_time = time.time()
        
        print("\n" + "=" * 80)
        print("BACKGROUND AGENTS SYSTEM - AUTOMATED TEST SUITE")
        print("=" * 80)
        
        test_phases = [
            ("Environment Setup", self.setup_environment),
            ("Dependency Installation", self.install_dependencies),
            ("Environment Validation", self.validate_environment),
            ("System Readiness", self.run_system_readiness_tests),
            ("PostgreSQL Migration", self.run_postgresql_migration_tests),
            ("Integration Validation", self.run_integration_tests)
        ]
        
        for phase_name, phase_method in test_phases:
            success = await self._run_test_phase(phase_name, phase_method)
            if not success:
                print(f"\n❌ Test suite aborted at phase: {phase_name}")
                self._print_final_summary()
                return False
        
        self._print_final_summary()
        return self.failed_tests == 0
    
    async def _run_test_phase(self, phase_name: str, phase_method) -> bool:
        """
        Run a single test phase with error handling.
        
        Args:
            phase_name: Name of the test phase
            phase_method: Method to execute for this phase
            
        Returns:
            bool: True if phase passes, False otherwise
        """
        print(f"\n[PHASE] {phase_name}")
        print("-" * 50)
        
        try:
            result = await phase_method()
            
            if result:
                print(f"✅ {phase_name}: PASSED")
                self.results[phase_name] = {"status": "PASSED", "error": None}
                self.passed_tests += 1
            else:
                print(f"❌ {phase_name}: FAILED")
                self.results[phase_name] = {"status": "FAILED", "error": "Phase returned False"}
                self.failed_tests += 1
                
            self.total_tests += 1
            return result
            
        except Exception as e:
            print(f"❌ {phase_name}: FAILED - {str(e)}")
            self.results[phase_name] = {"status": "FAILED", "error": str(e)}
            self.failed_tests += 1
            self.total_tests += 1
            logger.error(f"Phase {phase_name} failed: {e}")
            return False
    
    async def setup_environment(self) -> bool:
        """
        Phase 1: Environment Setup
        
        Sets up the testing environment and validates basic requirements.
        """
        try:
            # Check Python version
            if sys.version_info < (3, 8):
                print(f"❌ Python version {sys.version} is too old (requires 3.8+)")
                return False
            
            print(f"✅ Python version: {sys.version.split()[0]}")
            
            # Check if project root exists
            if not self.project_root.exists():
                print(f"❌ Project root not found: {self.project_root}")
                return False
            
            print(f"✅ Project root: {self.project_root}")
            
            # Check for critical files
            critical_files = [
                "requirements.txt",
                "validate_system_readiness.py",
                "test_postgresql_migration.py",
                "background_agents/coordination/shared_state.py"
            ]
            
            missing_files = []
            for file_path in critical_files:
                if not (self.project_root / file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                print(f"❌ Missing critical files: {missing_files}")
                return False
            
            print("✅ All critical files present")
            
            # Load environment variables from .env if it exists
            env_file = self.project_root / ".env"
            if env_file.exists():
                self._load_env_file(env_file)
                print("✅ Loaded .env file")
            else:
                print("⚠️  No .env file found - using system environment variables")
            
            return True
            
        except Exception as e:
            print(f"❌ Environment setup error: {e}")
            return False
    
    def _load_env_file(self, env_file: Path) -> None:
        """Load environment variables from .env file."""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        os.environ[key.strip()] = value
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
    
    async def install_dependencies(self) -> bool:
        """
        Phase 2: Dependency Installation
        
        Installs required Python packages from requirements.txt.
        """
        try:
            requirements_file = self.project_root / "requirements.txt"
            
            if not requirements_file.exists():
                print("❌ requirements.txt not found")
                return False
            
            print("Installing dependencies from requirements.txt...")
            
            # Run pip install
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, cwd=str(self.project_root))
            
            if result.returncode != 0:
                print(f"❌ Dependency installation failed:")
                print(result.stderr)
                return False
            
            print("✅ Dependencies installed successfully")
            
            # Verify key packages
            key_packages = ["asyncpg", "psycopg2-binary", "python-dotenv", "streamlit"]
            
            for package in key_packages:
                try:
                    __import__(package.replace("-", "_"))
                    print(f"✅ {package} available")
                except ImportError:
                    print(f"⚠️  {package} not available (may be optional)")
            
            return True
            
        except Exception as e:
            print(f"❌ Dependency installation error: {e}")
            return False
    
    async def validate_environment(self) -> bool:
        """
        Phase 3: Environment Validation
        
        Validates that all required environment variables are present.
        """
        try:
            # Check for required PostgreSQL variables
            required_vars = [
                'POSTGRESQL_HOST',
                'POSTGRESQL_PORT', 
                'POSTGRESQL_DATABASE',
                'POSTGRESQL_USER',
                'POSTGRESQL_PASSWORD'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
                else:
                    print(f"✅ {var}: {os.getenv(var)}")
            
            if missing_vars:
                print(f"❌ Missing required environment variables: {missing_vars}")
                print("\n💡 Create a .env file with the required variables. Use env.example as a template.")
                return False
            
            # Check optional but recommended variables
            optional_vars = [
                'OPENAI_API_KEY',
                'LANGSMITH_API_KEY',
                'SECRET_KEY'
            ]
            
            for var in optional_vars:
                if os.getenv(var):
                    print(f"✅ {var}: configured")
                else:
                    print(f"⚠️  {var}: not configured (optional)")
            
            return True
            
        except Exception as e:
            print(f"❌ Environment validation error: {e}")
            return False
    
    async def run_system_readiness_tests(self) -> bool:
        """
        Phase 4: System Readiness Tests
        
        Executes validate_system_readiness.py to check system components.
        """
        try:
            script_path = self.project_root / "validate_system_readiness.py"
            
            print("Running system readiness validation...")
            
            # Execute the validation script
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=str(self.project_root))
            
            # Print the output
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print("✅ System readiness validation passed")
                return True
            else:
                print(f"❌ System readiness validation failed (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ System readiness test error: {e}")
            return False
    
    async def run_postgresql_migration_tests(self) -> bool:
        """
        Phase 5: PostgreSQL Migration Tests
        
        Executes test_postgresql_migration.py for comprehensive database testing.
        """
        try:
            script_path = self.project_root / "test_postgresql_migration.py"
            
            print("Running PostgreSQL migration tests...")
            
            # Execute the migration test script
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=str(self.project_root))
            
            # Print the output
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print("✅ PostgreSQL migration tests passed")
                return True
            else:
                print(f"❌ PostgreSQL migration tests failed (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ PostgreSQL migration test error: {e}")
            return False
    
    async def run_integration_tests(self) -> bool:
        """
        Phase 6: Integration Tests
        
        Runs additional integration tests to verify end-to-end functionality.
        """
        try:
            print("Running integration validation...")
            
            # Test if we can import key modules
            sys.path.insert(0, str(self.project_root))
            
            try:
                from background_agents.coordination.shared_state import SharedState
                from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter
                print("✅ Core modules import successfully")
            except ImportError as e:
                print(f"❌ Module import failed: {e}")
                return False
            
            # Test basic instantiation (without actually connecting)
            try:
                adapter = PostgreSQLAdapter()
                print("✅ PostgreSQL adapter instantiation successful")
            except Exception as e:
                print(f"❌ PostgreSQL adapter instantiation failed: {e}")
                return False
            
            # Check if dashboard script exists and is importable
            dashboard_script = self.project_root / "background_agents_dashboard.py"
            if dashboard_script.exists():
                print("✅ Dashboard script available")
            else:
                print("⚠️  Dashboard script not found (optional)")
            
            print("✅ Integration validation completed")
            return True
            
        except Exception as e:
            print(f"❌ Integration test error: {e}")
            return False
    
    def _print_final_summary(self) -> None:
        """Print the final test summary."""
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 80)
        print("AUTOMATED TEST SUITE SUMMARY")
        print("=" * 80)
        
        print(f"Total Phases: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        
        if self.total_tests > 0:
            success_rate = (self.passed_tests / self.total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"Duration: {duration:.2f} seconds")
        
        if self.failed_tests > 0:
            print("\nFAILED PHASES:")
            for phase_name, result in self.results.items():
                if result['status'] == 'FAILED':
                    print(f"  ❌ {phase_name}: {result['error']}")
        
        print("\nDETAILED RESULTS:")
        for phase_name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"  {status_icon} {phase_name}")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
            print("\n📋 Next steps:")
            print("   1. Start the system: python launch_background_agents.py")
            print("   2. Open dashboard: streamlit run background_agents_dashboard.py")
            print("   3. Monitor logs in the logs/ directory")
        else:
            print(f"\n⚠️  {self.failed_tests} phase(s) failed. Please review and fix issues before deployment.")
            print("\n💡 Common fixes:")
            print("   - Ensure .env file is configured with correct database credentials")
            print("   - Verify PostgreSQL server is running and accessible")
            print("   - Check that all required dependencies are installed")
        
        print("=" * 80)

async def main():
    """Main entry point for the automated test runner."""
    try:
        runner = AutomatedTestRunner()
        success = await runner.run_complete_test_suite()
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error in test runner: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 