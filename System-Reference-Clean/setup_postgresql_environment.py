#!/usr/bin/env python3
"""
PostgreSQL Environment Setup Script

Interactive setup script for configuring PostgreSQL database environment
for the background agents system. Handles database creation, schema setup,
environment configuration, and initial validation.
"""

import os
import sys
import subprocess
import getpass
import time
from pathlib import Path
import shutil

class PostgreSQLEnvironmentSetup:
    """
    Comprehensive PostgreSQL environment setup.
    
    Features:
    - Interactive configuration
    - Database creation and setup
    - Schema initialization
    - Environment file generation
    - Connection testing
    - Validation and verification
    """
    
    def __init__(self):
        """Initialize the setup script."""
        self.config = {}
        self.env_file_path = ".env"
        
    def print_banner(self):
        """Print setup banner."""
        print("=" * 70)
        print("PostgreSQL Environment Setup for Background Agents System")
        print("=" * 70)
        print()
        print("This script will help you set up PostgreSQL for the background")
        print("agents monitoring system. Please have your PostgreSQL server")
        print("information ready.")
        print()
    
    def check_prerequisites(self):
        """Check system prerequisites."""
        print("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print(f"❌ Python 3.8+ required, found {sys.version}")
            return False
        print("✅ Python version check passed")
        
        # Check for PostgreSQL client tools
        if not shutil.which('psql'):
            print("⚠️  Warning: psql not found in PATH")
            print("   You may need to install PostgreSQL client tools")
        else:
            print("✅ PostgreSQL client tools found")
        
        # Check for required Python packages
        required_packages = ['asyncpg', 'psycopg2-binary', 'python-dotenv']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing required packages: {missing_packages}")
            print("   Please install them with: pip install " + " ".join(missing_packages))
            return False
        print("✅ Required packages available")
        
        return True
    
    def get_database_config(self):
        """Interactive database configuration."""
        print("\n" + "-" * 50)
        print("Database Configuration")
        print("-" * 50)
        
        # Database host
        default_host = "localhost"
        host = input(f"PostgreSQL host [{default_host}]: ").strip()
        self.config['POSTGRESQL_HOST'] = host or default_host
        
        # Database port
        default_port = "5432"
        port = input(f"PostgreSQL port [{default_port}]: ").strip()
        self.config['POSTGRESQL_PORT'] = port or default_port
        
        # Database name
        default_db = "background_agents"
        db_name = input(f"Database name [{default_db}]: ").strip()
        self.config['POSTGRESQL_DATABASE'] = db_name or default_db
        
        # Database user
        default_user = "postgres"
        user = input(f"Database user [{default_user}]: ").strip()
        self.config['POSTGRESQL_USER'] = user or default_user
        
        # Database password
        password = getpass.getpass("Database password: ")
        self.config['POSTGRESQL_PASSWORD'] = password
        
        # SSL mode
        print("\nSSL Mode options: disable, allow, prefer, require, verify-ca, verify-full")
        default_ssl = "prefer"
        ssl_mode = input(f"SSL mode [{default_ssl}]: ").strip()
        self.config['POSTGRESQL_SSL_MODE'] = ssl_mode or default_ssl
    
    def test_database_connection(self):
        """Test database connection."""
        print("\nTesting database connection...")
        
        try:
            import psycopg2
            
            conn_string = (
                f"host={self.config['POSTGRESQL_HOST']} "
                f"port={self.config['POSTGRESQL_PORT']} "
                f"user={self.config['POSTGRESQL_USER']} "
                f"password={self.config['POSTGRESQL_PASSWORD']} "
                f"sslmode={self.config['POSTGRESQL_SSL_MODE']}"
            )
            
            # Test connection to default database first
            test_conn = psycopg2.connect(conn_string + " dbname=postgres")
            test_conn.close()
            print("✅ Connection to PostgreSQL server successful")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def create_database(self):
        """Create the database if it doesn't exist."""
        print(f"\nCreating database '{self.config['POSTGRESQL_DATABASE']}'...")
        
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Connect to default database
            conn_string = (
                f"host={self.config['POSTGRESQL_HOST']} "
                f"port={self.config['POSTGRESQL_PORT']} "
                f"user={self.config['POSTGRESQL_USER']} "
                f"password={self.config['POSTGRESQL_PASSWORD']} "
                f"sslmode={self.config['POSTGRESQL_SSL_MODE']} "
                f"dbname=postgres"
            )
            
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.config['POSTGRESQL_DATABASE'],)
            )
            
            if cursor.fetchone():
                print(f"✅ Database '{self.config['POSTGRESQL_DATABASE']}' already exists")
            else:
                # Create database
                cursor.execute(f'CREATE DATABASE "{self.config["POSTGRESQL_DATABASE"]}"')
                print(f"✅ Database '{self.config['POSTGRESQL_DATABASE']}' created successfully")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Database creation failed: {e}")
            return False
    
    def create_schema(self):
        """Create database schema."""
        print("\nCreating database schema...")
        
        schema_sql = '''
-- Background Agents System PostgreSQL Schema
-- Generated by setup script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Agents table
CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(255) PRIMARY KEY,
    state VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,
    config JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_state ON agents(state);
CREATE INDEX IF NOT EXISTS idx_agents_started_at ON agents(started_at);

-- 2. Agent heartbeats table
CREATE TABLE IF NOT EXISTS agent_heartbeats (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    state VARCHAR(50),
    error_count INTEGER DEFAULT 0,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_heartbeats_agent_timestamp ON agent_heartbeats(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_heartbeats_timestamp ON agent_heartbeats(timestamp DESC);

-- 3. Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value NUMERIC,
    unit VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metrics_agent_name_timestamp ON performance_metrics(agent_id, metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp DESC);

-- 4. System state table
CREATE TABLE IF NOT EXISTS system_state (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_system_state_key ON system_state(key);

-- 5. System events table
CREATE TABLE IF NOT EXISTS system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    agent_id VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'INFO'
);

CREATE INDEX IF NOT EXISTS idx_events_type_timestamp ON system_events(event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_agent_timestamp ON system_events(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity ON system_events(severity);

-- 6. Help requests table
CREATE TABLE IF NOT EXISTS help_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    context JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_help_requests_status ON help_requests(status);
CREATE INDEX IF NOT EXISTS idx_help_requests_user_id ON help_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_help_requests_created_at ON help_requests(created_at DESC);

-- 7. Help responses table
CREATE TABLE IF NOT EXISTS help_responses (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL,
    response_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    confidence_score NUMERIC,
    sources JSONB,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    agent_id VARCHAR(255),
    FOREIGN KEY (request_id) REFERENCES help_requests(request_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_help_responses_request_id ON help_responses(request_id);
CREATE INDEX IF NOT EXISTS idx_help_responses_confidence ON help_responses(confidence_score DESC);

-- 8. Agent communications table
CREATE TABLE IF NOT EXISTS agent_communications (
    id SERIAL PRIMARY KEY,
    from_agent VARCHAR(255) NOT NULL,
    to_agent VARCHAR(255) NOT NULL,
    message_type VARCHAR(100) NOT NULL,
    content JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent'
);

CREATE INDEX IF NOT EXISTS idx_communications_to_agent ON agent_communications(to_agent, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_communications_type ON agent_communications(message_type);

-- 9. LLM conversations table
CREATE TABLE IF NOT EXISTS llm_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255),
    prompt TEXT NOT NULL,
    response TEXT,
    model VARCHAR(100),
    tokens_used INTEGER,
    cost NUMERIC,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_llm_conversations_agent ON llm_conversations(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_conversations_model ON llm_conversations(model, timestamp DESC);

-- Insert initial system state
INSERT INTO system_state (key, value, updated_by) 
VALUES 
    ('system_initialized', 'true', 'setup_script'),
    ('schema_version', '1.0.0', 'setup_script'),
    ('setup_timestamp', to_jsonb(NOW()), 'setup_script')
ON CONFLICT (key) DO NOTHING;
'''
        
        try:
            import psycopg2
            
            conn_string = (
                f"host={self.config['POSTGRESQL_HOST']} "
                f"port={self.config['POSTGRESQL_PORT']} "
                f"user={self.config['POSTGRESQL_USER']} "
                f"password={self.config['POSTGRESQL_PASSWORD']} "
                f"sslmode={self.config['POSTGRESQL_SSL_MODE']} "
                f"dbname={self.config['POSTGRESQL_DATABASE']}"
            )
            
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            
            # Execute schema creation
            cursor.execute(schema_sql)
            conn.commit()
            
            print("✅ Database schema created successfully")
            
            # Verify tables were created
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Created {len(tables)} tables: {', '.join(tables)}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Schema creation failed: {e}")
            return False
    
    def configure_additional_settings(self):
        """Configure additional system settings."""
        print("\n" + "-" * 50)
        print("Additional Configuration")
        print("-" * 50)
        
        # OpenAI API Key
        openai_key = getpass.getpass("OpenAI API Key (optional, press Enter to skip): ")
        self.config['OPENAI_API_KEY'] = openai_key or 'your-openai-api-key-here'
        
        # LangSmith API Key
        langsmith_key = getpass.getpass("LangSmith API Key (optional, press Enter to skip): ")
        self.config['LANGSMITH_API_KEY'] = langsmith_key or 'your-langsmith-api-key-here'
        
        # Environment
        env = input("Environment [development]: ").strip()
        self.config['ENVIRONMENT'] = env or 'development'
        
        # Log level
        log_level = input("Log level [INFO]: ").strip()
        self.config['LOG_LEVEL'] = log_level or 'INFO'
        
        # Additional settings with defaults
        self.config.update({
            'LANGSMITH_ENDPOINT': 'https://api.smith.langchain.com',
            'LANGSMITH_PROJECT': 'background-agents-system',
            'LANGSMITH_TRACING': 'true',
            'OPENAI_MODEL': 'gpt-4',
            'OPENAI_TEMPERATURE': '0.7',
            'OPENAI_MAX_TOKENS': '2000',
            'DEBUG': 'false',
            'DATA_DIR': 'data',
            'LOGS_DIR': 'logs',
            'TEMP_DIR': 'temp',
            'DEFAULT_HEARTBEAT_INTERVAL': '60',
            'DEFAULT_MAX_RETRIES': '3',
            'DEFAULT_TIMEOUT': '30',
            'HEARTBEAT_HEALTH_AGENT_ENABLED': 'true',
            'PERFORMANCE_MONITOR_ENABLED': 'true',
            'LANGSMITH_BRIDGE_ENABLED': 'true',
            'AI_HELP_AGENT_ENABLED': 'true',
            'HEALTH_CHECK_INTERVAL': '30',
            'HEARTBEAT_TIMEOUT': '120',
            'PERFORMANCE_METRICS_INTERVAL': '60',
            'ALERT_EMAIL_ENABLED': 'false',
            'SECRET_KEY': 'your-secret-key-change-this-in-production',
            'CORS_ENABLED': 'true',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8501',
            'BACKUP_ENABLED': 'true',
            'BACKUP_INTERVAL': 'daily',
            'BACKUP_RETENTION_DAYS': '30',
            'BACKUP_LOCATION': 'backups'
        })
    
    def create_environment_file(self):
        """Create .env file with configuration."""
        print(f"\nCreating environment file: {self.env_file_path}")
        
        try:
            with open(self.env_file_path, 'w') as f:
                f.write("# Background Agents System Environment Configuration\n")
                f.write("# Generated by setup script\n")
                f.write(f"# Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Database configuration
                f.write("# Database Configuration\n")
                db_vars = ['POSTGRESQL_HOST', 'POSTGRESQL_PORT', 'POSTGRESQL_DATABASE', 'POSTGRESQL_USER', 'POSTGRESQL_PASSWORD', 'POSTGRESQL_SSL_MODE']
                for var in db_vars:
                    f.write(f"{var}={self.config[var]}\n")
                
                f.write("\n# API Keys\n")
                api_vars = ['OPENAI_API_KEY', 'LANGSMITH_API_KEY']
                for var in api_vars:
                    f.write(f"{var}={self.config[var]}\n")
                
                f.write("\n# System Settings\n")
                for key, value in self.config.items():
                    if key not in db_vars + api_vars:
                        f.write(f"{key}={value}\n")
            
            print(f"✅ Environment file created: {self.env_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create environment file: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories."""
        print("\nCreating directories...")
        
        directories = ['logs', 'data', 'temp', 'backups', 'config']
        
        for directory in directories:
            try:
                Path(directory).mkdir(exist_ok=True)
                print(f"✅ Created directory: {directory}")
            except Exception as e:
                print(f"❌ Failed to create directory {directory}: {e}")
                return False
        
        return True
    
    def run_validation_test(self):
        """Run validation test."""
        print("\nRunning validation test...")
        
        try:
            # Try to run the migration test
            result = subprocess.run([
                sys.executable, 'test_postgresql_migration.py'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Validation test passed!")
                return True
            else:
                print("❌ Validation test failed:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Validation test timed out")
            return False
        except FileNotFoundError:
            print("⚠️  test_postgresql_migration.py not found, skipping validation")
            return True
        except Exception as e:
            print(f"⚠️  Validation test error: {e}")
            return True  # Don't fail setup for validation issues
    
    def print_completion_message(self):
        """Print setup completion message."""
        print("\n" + "=" * 70)
        print("Setup Complete!")
        print("=" * 70)
        print()
        print("Your PostgreSQL environment is now configured for the")
        print("background agents system.")
        print()
        print("Next steps:")
        print("1. Review the .env file and adjust settings as needed")
        print("2. Run the test suite: python test_postgresql_migration.py")
        print("3. Start the system: python launch_background_agents.py")
        print("4. View the dashboard: streamlit run background_agents_dashboard.py")
        print()
        print("Configuration files created:")
        print(f"  - {self.env_file_path}")
        print()
        print("Database connection details:")
        print(f"  Host: {self.config['POSTGRESQL_HOST']}")
        print(f"  Port: {self.config['POSTGRESQL_PORT']}")
        print(f"  Database: {self.config['POSTGRESQL_DATABASE']}")
        print(f"  User: {self.config['POSTGRESQL_USER']}")
        print()
        print("For support, please refer to the documentation or")
        print("create an issue in the repository.")
        print("=" * 70)
    
    def run_setup(self):
        """Run the complete setup process."""
        self.print_banner()
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Get database configuration
        self.get_database_config()
        
        # Test connection
        if not self.test_database_connection():
            print("\nPlease check your database settings and try again.")
            return False
        
        # Create database
        if not self.create_database():
            return False
        
        # Create schema
        if not self.create_schema():
            return False
        
        # Configure additional settings
        self.configure_additional_settings()
        
        # Create environment file
        if not self.create_environment_file():
            return False
        
        # Create directories
        if not self.create_directories():
            return False
        
        # Run validation
        self.run_validation_test()
        
        # Print completion message
        self.print_completion_message()
        
        return True

def main():
    """Main entry point."""
    setup = PostgreSQLEnvironmentSetup()
    
    try:
        success = setup.run_setup()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nSetup failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 