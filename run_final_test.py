#!/usr/bin/env python3
"""
AI Help Agent - Final Test Launcher
==================================

Simple launcher script that:
1. Checks system readiness
2. Ensures background agents are running  
3. Launches the test interface
4. Provides guidance for testers

Usage: python run_final_test.py
"""

import os
import sys
import subprocess
import time
import asyncio
from pathlib import Path

def print_banner():
    """Print test banner"""
    print("=" * 70)
    print("🎯 AI HELP AGENT - FINAL PRODUCTION VALIDATION TEST")
    print("=" * 70)
    print("🚀 Senior Developer Assistant Capabilities Test")
    print("📋 Duration: 15-30 minutes")
    print("🎯 Success Criteria: 80+ Production Readiness Score")
    print("=" * 70)

def check_system_requirements():
    """Check basic system requirements"""
    print("\n🔍 Checking System Requirements...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 8:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python version too old: {python_version.major}.{python_version.minor}")
        return False
    
    # Check required files exist
    required_files = [
        "ai_help_agent_user_test.py",
        "background_agents/ai_help/ai_help_agent.py",
        "background_agents/coordination/shared_state.py",
        "launch_background_agents.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            return False
    
    # Check if streamlit is available
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not installed")
        print("   Install with: pip install streamlit")
        return False
    
    return True

def check_background_agents():
    """Check if background agents are running"""
    print("\n🔍 Checking Background Agents...")
    
    try:
        # Try to import and test database connection
        from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter
        from dotenv import load_dotenv
        
        load_dotenv()
        
        adapter = PostgreSQLAdapter({
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'background_agents'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        })
        
        if adapter.test_connection():
            print("✅ PostgreSQL Database Connected")
        else:
            print("❌ PostgreSQL Database Connection Failed")
            return False
            
        # Check for recent agent activity
        async def check_agents():
            try:
                agents = await adapter.get_all_agents()
                heartbeats = await adapter.get_recent_heartbeats(minutes=5)
                
                print(f"✅ Registered Agents: {len(agents)}")
                print(f"✅ Recent Heartbeats: {len(heartbeats)}")
                
                if len(agents) >= 5 and len(heartbeats) >= 3:
                    print("✅ Background Agents Active")
                    return True
                else:
                    print("⚠️ Background Agents may not be fully active")
                    print("   Consider running: python launch_background_agents.py")
                    return True  # Still allow test to proceed
                    
            except Exception as e:
                print(f"❌ Error checking agents: {e}")
                return False
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(check_agents())
        
    except Exception as e:
        print(f"❌ Error connecting to system: {e}")
        print("   Make sure background agents are running:")
        print("   python launch_background_agents.py")
        return False

def launch_test_interface():
    """Launch the Streamlit test interface"""
    print("\n🚀 Launching AI Help Agent Test Interface...")
    print("📋 Test Categories:")
    print("   1. System Status & Health Analysis")
    print("   2. Code Analysis & Explanation")
    print("   3. Performance & Error Analysis") 
    print("   4. Development Recommendations")
    print("   5. Goal Tracking & Suggestions")
    print("   6. New Agent Integration Guidance")
    print("\n🎯 Success Criteria:")
    print("   • 90%+ Success Rate")
    print("   • 80%+ Average Confidence")
    print("   • <2s Response Time")
    print("   • Multi-category Coverage")
    print("   • Production Readiness Score: 80+")
    
    print("\n" + "="*50)
    print("🌐 Opening test interface in browser...")
    print("📍 URL: http://localhost:8501")
    print("🔄 If port 8501 is busy, Streamlit will use next available port")
    print("="*50)
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ai_help_agent_user_test.py",
            "--server.headless", "false",
            "--server.enableCORS", "false"
        ])
    except KeyboardInterrupt:
        print("\n✅ Test session ended by user")
    except Exception as e:
        print(f"\n❌ Error launching test interface: {e}")

def main():
    """Main test launcher"""
    print_banner()
    
    # Step 1: Check system requirements
    if not check_system_requirements():
        print("\n❌ System requirements not met. Please fix issues above.")
        return False
    
    # Step 2: Check background agents
    if not check_background_agents():
        print("\n❌ Background agents not ready. Please ensure they are running:")
        print("   python launch_background_agents.py")
        
        # Ask if user wants to try launching them
        try:
            response = input("\n🤔 Would you like to try launching background agents now? (y/n): ")
            if response.lower() in ['y', 'yes']:
                print("\n🚀 Launching background agents...")
                subprocess.Popen([sys.executable, "launch_background_agents.py"])
                print("⏳ Waiting 10 seconds for agents to initialize...")
                time.sleep(10)
                
                # Re-check
                if not check_background_agents():
                    print("❌ Background agents still not ready")
                    return False
            else:
                return False
        except KeyboardInterrupt:
            print("\n❌ Test cancelled by user")
            return False
    
    # Step 3: All checks passed, launch test
    print("\n🎉 System Ready for Testing!")
    print("\n📋 Test Instructions:")
    print("   1. Click '🚀 Initialize AI Help Agent' in the web interface")
    print("   2. Select a test category from the sidebar")
    print("   3. Click predefined questions or enter custom questions")
    print("   4. Aim for 80+ Production Readiness Score")
    print("   5. Test at least 6 questions across different categories")
    print("   6. Validate new agent integration guidance capabilities")
    
    try:
        input("\n⏳ Press ENTER to launch the test interface...")
        launch_test_interface()
        return True
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Test completed successfully!")
        print("📊 Check your Production Readiness Score in the interface")
        print("🎯 Score 80+ = GREEN LIGHT for production deployment!")
    else:
        print("\n❌ Test setup failed. Please fix issues above and try again.")
        sys.exit(1) 