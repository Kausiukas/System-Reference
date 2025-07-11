import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_database_connection():
    """Simple test to verify database connectivity"""
    print("🔍 Testing database connection...")
    
    # Database configuration
    host = os.getenv('POSTGRESQL_HOST', 'localhost')
    port = int(os.getenv('POSTGRESQL_PORT', 5432))
    database = os.getenv('POSTGRESQL_DATABASE', 'background_agents')
    user = os.getenv('POSTGRESQL_USER', 'postgres')
    password = os.getenv('POSTGRESQL_PASSWORD', '')
    
    try:
        # Test basic connection
        connection = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            server_settings={
                'application_name': 'test_client',
                'default_transaction_isolation': 'read committed'
            }
        )
        
        print("✅ Database connection successful")
        
        # Test agents query
        agents = await connection.fetch("SELECT agent_id, agent_type, state FROM agents ORDER BY created_at DESC LIMIT 5")
        print(f"✅ Found {len(agents)} agents in database")
        
        for agent in agents:
            print(f"   - {agent['agent_id']} ({agent['agent_type']}) - {agent['state']}")
        
        # Test metrics query
        metrics = await connection.fetch("SELECT COUNT(*) as count FROM performance_metrics WHERE timestamp > NOW() - INTERVAL '1 hour'")
        metrics_count = metrics[0]['count'] if metrics else 0
        print(f"✅ Found {metrics_count} recent performance metrics")
        
        # Test events query
        events = await connection.fetch("SELECT COUNT(*) as count FROM system_events WHERE timestamp > NOW() - INTERVAL '1 hour'")
        events_count = events[0]['count'] if events else 0
        print(f"✅ Found {events_count} recent system events")
        
        await connection.close()
        print("✅ Database connection closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    if success:
        print("\n🎉 Database connectivity test PASSED!")
    else:
        print("\n💥 Database connectivity test FAILED!") 