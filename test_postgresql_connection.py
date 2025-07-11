#!/usr/bin/env python3
"""
Simple PostgreSQL Connection Test
Tests if PostgreSQL server is running and accessible using Python asyncpg
"""

import asyncio
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_postgresql_connection():
    """Test PostgreSQL connection using asyncpg"""
    print("🔍 Testing PostgreSQL Connection...")
    print("=" * 50)
    
    # Get database configuration from environment
    host = os.getenv('POSTGRESQL_HOST', 'localhost')
    port = int(os.getenv('POSTGRESQL_PORT', 5432))
    database = os.getenv('POSTGRESQL_DATABASE', 'background_agents')
    user = os.getenv('POSTGRESQL_USER', 'postgres')
    password = os.getenv('POSTGRESQL_PASSWORD', '')
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password) if password else '(empty)'}")
    print()
    
    try:
        import asyncpg
        
        # Test basic connection
        print("📋 Step 1: Testing basic PostgreSQL connection...")
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database='postgres'  # Connect to default postgres database first
                ), timeout=10.0
            )
            
            # Test server version
            version = await conn.fetchval('SELECT version()')
            print(f"✅ PostgreSQL server is running")
            print(f"   Version: {version.split()[1] if version else 'Unknown'}")
            await conn.close()
            
        except asyncio.TimeoutError:
            print("❌ FAILED: Connection timeout - PostgreSQL server not responding")
            return False
        except Exception as e:
            print(f"❌ FAILED: Cannot connect to PostgreSQL server - {e}")
            return False
        
        # Test database exists
        print(f"\n📋 Step 2: Testing {database} database exists...")
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                ), timeout=10.0
            )
            
            print(f"✅ Database '{database}' exists and accessible")
            
            # Test if tables exist
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            
            if tables:
                print(f"✅ Found {len(tables)} tables in database:")
                for table in tables[:5]:  # Show first 5 tables
                    print(f"   - {table['tablename']}")
                if len(tables) > 5:
                    print(f"   ... and {len(tables) - 5} more tables")
            else:
                print("⚠️  No tables found - database might need initialization")
            
            await conn.close()
            
        except Exception as e:
            print(f"❌ FAILED: Cannot access database '{database}' - {e}")
            print("   Possible causes:")
            print("   - Database doesn't exist")
            print("   - Insufficient permissions")
            print("   - Database not initialized")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 PostgreSQL CONNECTION TEST PASSED!")
        print("✅ Database server is running and accessible")
        print(f"✅ Database '{database}' is ready")
        return True
        
    except ImportError:
        print("❌ FAILED: asyncpg package not installed")
        print("   Install with: pip install asyncpg")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False

def main():
    """Main function"""
    print("🧪 PostgreSQL Connection Test")
    print("=" * 50)
    print("Testing direct PostgreSQL connectivity before running background agents")
    print()
    
    try:
        result = asyncio.run(test_postgresql_connection())
        
        if result:
            print("\n✅ PostgreSQL is ready!")
            print("📋 Next step: Test background agents connection")
            print("   Run: python test_connection_health.py")
            return True
        else:
            print("\n❌ PostgreSQL connection failed!")
            print("🔧 Possible solutions:")
            print("   1. Start PostgreSQL server")
            print("   2. Create 'background_agents' database")
            print("   3. Run: python setup_postgresql_environment.py")
            print("   4. Check .env database configuration")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {e}")
        return False

if __name__ == "__main__":
    main() 