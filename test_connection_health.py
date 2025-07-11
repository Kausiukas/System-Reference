#!/usr/bin/env python3
"""
Test Connection Health Script
Verifies if background agents system is working properly before running full tests.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_system_connection():
    """Test connection to background agents system"""
    print("🔍 Testing background agents system connection...")
    print("=" * 60)
    
    try:
        # Import required modules
        from background_agents.coordination.shared_state import SharedState
        from background_agents.ai_help.ai_help_agent import AIHelpAgent, HelpRequest
        from datetime import datetime
        
        # Initialize SharedState
        print("📋 Step 1: Initializing SharedState...")
        shared_state = SharedState()
        
        # Test initialization with detailed error reporting
        try:
            await shared_state.initialize()
            
            # Check if initialization was successful
            if not shared_state.is_initialized:
                print("❌ FAILED: SharedState initialization completed but is_initialized flag is False")
                return False
                
            print("✅ SharedState initialized successfully")
        except Exception as e:
            print(f"❌ FAILED: SharedState initialization threw exception: {e}")
            print(f"   Exception type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return False
        
        # Test 2: Get registered agents
        print("\n📋 Step 2: Testing agent registry access...")
        try:
            agents = await asyncio.wait_for(shared_state.get_registered_agents(), timeout=5.0)
            if agents:
                active_agents = len([a for a in agents if a.get('state') in ['active', 'running']])
                print(f"✅ Found {len(agents)} registered agents ({active_agents} active)")
                
                # Show agent details
                for agent in agents[:5]:  # Show first 5
                    state = agent.get('state', 'unknown')
                    name = agent.get('agent_id', 'unnamed')
                    print(f"   - {name}: {state}")
                if len(agents) > 5:
                    print(f"   ... and {len(agents) - 5} more agents")
            else:
                print("⚠️  No agents found in registry")
                return False
        except Exception as e:
            print(f"❌ FAILED: Cannot access agent registry - {e}")
            return False
        
        # Test 3: Get performance metrics
        print("\n📋 Step 3: Testing performance metrics access...")
        try:
            metrics = await asyncio.wait_for(shared_state.get_performance_metrics(), timeout=5.0)
            if metrics:
                print(f"✅ Found {len(metrics)} performance metrics")
                # Show sample metric
                if metrics:
                    sample = metrics[0]
                    print(f"   Sample: {sample.get('metric_type', 'unknown')} = {sample.get('value', 'N/A')}")
            else:
                print("⚠️  No performance metrics available")
        except Exception as e:
            print(f"❌ WARNING: Cannot access performance metrics - {e}")
        
        # Test 4: Get system events
        print("\n📋 Step 4: Testing system events access...")
        try:
            events = await asyncio.wait_for(shared_state.get_system_events(), timeout=5.0)
            if events:
                print(f"✅ Found {len(events)} system events")
                # Show most recent event
                if events:
                    recent = events[0]
                    event_type = recent.get('event_type', 'unknown')
                    timestamp = recent.get('timestamp', 'unknown')
                    print(f"   Most recent: {event_type} at {timestamp}")
            else:
                print("⚠️  No system events available")
        except Exception as e:
            print(f"❌ WARNING: Cannot access system events - {e}")
        
        # Test 5: Initialize AI Help Agent
        print("\n📋 Step 5: Testing AI Help Agent initialization...")
        try:
            ai_help_agent = AIHelpAgent(shared_state)
            await ai_help_agent.initialize()
            print("✅ AI Help Agent initialized successfully")
        except Exception as e:
            print(f"❌ FAILED: AI Help Agent initialization failed - {e}")
            return False
        
        # Test 6: Simple question processing
        print("\n📋 Step 6: Testing question processing...")
        try:
            test_request = HelpRequest(
                request_id="connection_test",
                user_id="test_user",
                query="What is the current system status?",
                context={},
                timestamp=datetime.now(),
                priority="normal"
            )
            
            response = await asyncio.wait_for(
                ai_help_agent.process_single_request(test_request), timeout=10.0
            )
            
            if response and hasattr(response, 'response_text'):
                print("✅ Question processing successful")
                print(f"   Response length: {len(response.response_text)} characters")
                print(f"   Confidence: {getattr(response, 'confidence_score', 'N/A')}")
            else:
                print("❌ FAILED: Invalid response from AI Help Agent")
                return False
                
        except Exception as e:
            print(f"❌ FAILED: Question processing failed - {e}")
            return False
        
        # Cleanup
        print("\n📋 Step 7: Cleanup...")
        try:
            await shared_state.close()
            print("✅ SharedState closed successfully")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 CONNECTION TEST PASSED!")
        print("✅ Background agents system is working properly")
        print("✅ Ready for full AI Help Agent testing")
        print("\n📋 Next step: Run `streamlit run ai_help_agent_user_test.py`")
        return True
        
    except ImportError as e:
        print(f"❌ FAILED: Cannot import required modules - {e}")
        print("\n🔧 Possible solutions:")
        print("   - Ensure virtual environment is activated")
        print("   - Run: pip install -r requirements.txt")
        print("   - Check if background agents are properly installed")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        print("\n🔧 Possible solutions:")
        print("   - Start background agents: python launch_background_agents.py")
        print("   - Check PostgreSQL connection")
        print("   - Verify environment configuration")
        return False

def main():
    """Main function"""
    print("🧪 AI Help Agent Connection Health Test")
    print("=" * 60)
    print("This script verifies if the background agents system is working")
    print("properly before running the full user interface test.")
    print()
    
    try:
        # Run the connection test
        result = asyncio.run(test_system_connection())
        
        if result:
            print("\n✅ ALL TESTS PASSED - System is ready!")
            sys.exit(0)
        else:
            print("\n❌ TESTS FAILED - Please fix issues before testing")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 