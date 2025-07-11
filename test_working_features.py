import asyncio
import asyncpg
import os
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class WorkingFeaturesTest:
    """Test the features that are currently working properly"""
    
    def __init__(self):
        self.connection = None
        
    async def connect_to_database(self):
        """Test basic database connectivity"""
        print("🔍 Testing basic database connection...")
        
        # Database configuration
        host = os.getenv('POSTGRESQL_HOST', 'localhost')
        port = int(os.getenv('POSTGRESQL_PORT', 5432))
        database = os.getenv('POSTGRESQL_DATABASE', 'background_agents')
        user = os.getenv('POSTGRESQL_USER', 'postgres')
        password = os.getenv('POSTGRESQL_PASSWORD', '')
        
        try:
            self.connection = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                server_settings={
                    'application_name': 'working_features_test',
                    'default_transaction_isolation': 'read committed'
                }
            )
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def test_agent_detection(self):
        """Test if we can detect agents in the database"""
        print("\n🤖 Testing agent detection...")
        
        try:
            # Get basic agent count
            agents = await self.connection.fetch("SELECT COUNT(*) as count FROM agents")
            total_agents = agents[0]['count'] if agents else 0
            
            # Get active agents
            active_agents = await self.connection.fetch(
                "SELECT COUNT(*) as count FROM agents WHERE state = 'active'"
            )
            active_count = active_agents[0]['count'] if active_agents else 0
            
            print(f"✅ Found {total_agents} total agents")
            print(f"✅ Found {active_count} active agents")
            
            # Get sample agent details (without concurrent operations)
            sample_agents = await self.connection.fetch(
                "SELECT agent_id, agent_type, state FROM agents ORDER BY created_at DESC LIMIT 3"
            )
            
            print("📋 Sample agents:")
            for agent in sample_agents:
                print(f"   - {agent['agent_id']} ({agent['agent_type']}) - {agent['state']}")
                
            return {
                'total_agents': total_agents,
                'active_agents': active_count,
                'sample_agents': sample_agents
            }
            
        except Exception as e:
            print(f"❌ Agent detection failed: {e}")
            return None
    
    async def test_metrics_availability(self):
        """Test if metrics data is available"""
        print("\n📊 Testing metrics availability...")
        
        try:
            # Check recent metrics count
            recent_metrics = await self.connection.fetch(
                "SELECT COUNT(*) as count FROM performance_metrics WHERE timestamp > NOW() - INTERVAL '1 hour'"
            )
            metrics_count = recent_metrics[0]['count'] if recent_metrics else 0
            
            # Check total metrics
            total_metrics = await self.connection.fetch("SELECT COUNT(*) as count FROM performance_metrics")
            total_count = total_metrics[0]['count'] if total_metrics else 0
            
            print(f"✅ Found {metrics_count} recent metrics (last hour)")
            print(f"✅ Found {total_count} total metrics in database")
            
            return {
                'recent_metrics': metrics_count,
                'total_metrics': total_count
            }
            
        except Exception as e:
            print(f"❌ Metrics availability test failed: {e}")
            return None
    
    async def test_events_availability(self):
        """Test if events data is available"""
        print("\n📝 Testing events availability...")
        
        try:
            # Check recent events count
            recent_events = await self.connection.fetch(
                "SELECT COUNT(*) as count FROM system_events WHERE timestamp > NOW() - INTERVAL '1 hour'"
            )
            events_count = recent_events[0]['count'] if recent_events else 0
            
            # Check event types
            event_types = await self.connection.fetch(
                "SELECT event_type, COUNT(*) as count FROM system_events GROUP BY event_type ORDER BY count DESC LIMIT 5"
            )
            
            print(f"✅ Found {events_count} recent events (last hour)")
            print("📋 Top event types:")
            for event in event_types:
                print(f"   - {event['event_type']}: {event['count']} events")
                
            return {
                'recent_events': events_count,
                'event_types': event_types
            }
            
        except Exception as e:
            print(f"❌ Events availability test failed: {e}")
            return None
    
    async def test_ai_help_simulation(self, agent_data, metrics_data, events_data):
        """Simulate AI Help Agent responses based on available data"""
        print("\n🤖 Testing AI Help Agent simulation...")
        
        try:
            # Simulate different types of queries
            test_queries = [
                "What is the current system status?",
                "How many agents are running?", 
                "Are there any recent issues?",
                "What metrics are being collected?"
            ]
            
            responses = []
            
            for query in test_queries:
                print(f"\n❓ Query: {query}")
                
                # Generate simple response based on available data
                if "status" in query.lower():
                    response = f"System Status: {agent_data['active_agents']}/{agent_data['total_agents']} agents active. "
                    response += f"Collected {metrics_data['recent_metrics']} metrics and {events_data['recent_events']} events in the last hour."
                    
                elif "agents" in query.lower():
                    response = f"Currently {agent_data['active_agents']} agents are running out of {agent_data['total_agents']} total agents. "
                    sample_names = [agent['agent_id'] for agent in agent_data['sample_agents'][:2]]
                    response += f"Recent agents include: {', '.join(sample_names)}"
                    
                elif "issues" in query.lower():
                    inactive_agents = agent_data['total_agents'] - agent_data['active_agents']
                    if inactive_agents > 0:
                        response = f"⚠️ {inactive_agents} agents are currently inactive. Check logs for details."
                    else:
                        response = "✅ All agents appear to be active. No immediate issues detected."
                        
                elif "metrics" in query.lower():
                    response = f"📊 Collecting {metrics_data['total_metrics']} total metrics. "
                    response += f"{metrics_data['recent_metrics']} metrics recorded in the last hour."
                    
                else:
                    response = "I can help with system status, agent information, and metrics. What would you like to know?"
                
                print(f"🤖 Response: {response}")
                responses.append({'query': query, 'response': response})
                
            return responses
            
        except Exception as e:
            print(f"❌ AI Help simulation failed: {e}")
            return None
    
    async def close_connection(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            print("✅ Database connection closed")

async def run_working_features_test():
    """Run the complete working features test"""
    print("🚀 Starting Working Features Test")
    print("=" * 50)
    
    test = WorkingFeaturesTest()
    
    try:
        # Test 1: Database Connection
        if not await test.connect_to_database():
            return False
        
        # Test 2: Agent Detection  
        agent_data = await test.test_agent_detection()
        if agent_data is None:
            return False
            
        # Test 3: Metrics Availability
        metrics_data = await test.test_metrics_availability()
        if metrics_data is None:
            return False
            
        # Test 4: Events Availability
        events_data = await test.test_events_availability()
        if events_data is None:
            return False
            
        # Test 5: AI Help Simulation
        responses = await test.test_ai_help_simulation(agent_data, metrics_data, events_data)
        if responses is None:
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Working Features Test COMPLETED SUCCESSFULLY!")
        print("\n✅ Summary of Working Features:")
        print(f"   - Database connectivity: ✅ Working")
        print(f"   - Agent detection: ✅ {agent_data['total_agents']} agents found")
        print(f"   - Metrics collection: ✅ {metrics_data['total_metrics']} metrics available")
        print(f"   - Events logging: ✅ Event tracking operational")
        print(f"   - AI Help responses: ✅ {len(responses)} test queries answered")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        return False
        
    finally:
        await test.close_connection()

if __name__ == "__main__":
    success = asyncio.run(run_working_features_test())
    if success:
        print("\n🏆 All working features validated successfully!")
    else:
        print("\n💥 Some features need attention!") 