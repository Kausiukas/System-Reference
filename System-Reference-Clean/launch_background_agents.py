#!/usr/bin/env python3
"""
Background Agents Launcher

Enterprise agent launcher with PostgreSQL integration,
comprehensive health monitoring, and automated recovery.
"""

import asyncio
import logging
import signal
import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

# Import coordination system
from background_agents.coordination.agent_coordinator import AgentCoordinator
from background_agents.coordination.system_initializer import SystemInitializer
from background_agents.coordination.shared_state import SharedState
from background_agents.coordination.postgresql_adapter import PostgreSQLAdapter, ConnectionConfig

# Import agents
from background_agents.monitoring.heartbeat_health_agent import HeartbeatHealthAgent
from background_agents.monitoring.performance_monitor import PerformanceMonitor
from background_agents.monitoring.langsmith_bridge import LangSmithBridge
from background_agents.ai_help.ai_help_agent import AIHelpAgent


class BackgroundAgentsLauncher:
    """
    Enterprise Background Agents Launcher
    
    Coordinates startup, monitoring, and lifecycle management of all background agents
    with PostgreSQL integration and automated recovery capabilities.
    """
    
    def __init__(self):
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger("background_agents_launcher")
        
        # System components
        self.postgresql_adapter = None
        self.shared_state = None
        self.agent_coordinator = None
        self.system_initializer = None
        
        # Agent instances
        self.agents = {}
        self.agent_tasks = {}
        
        # System state
        self.is_running = False
        self.startup_time = None
        self.shutdown_event = asyncio.Event()
        
        # Configuration
        self.config = self.load_configuration()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
    def setup_logging(self) -> None:
        """Setup comprehensive logging for the launcher"""
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(logs_dir / "background_agents_launcher.log"),
                logging.StreamHandler(sys.stdout)
            ]
            )
        
        # Set specific log levels
        logging.getLogger("background_agents").setLevel(logging.INFO)
        logging.getLogger("postgresql").setLevel(logging.WARNING)
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load system configuration"""
        
        config = {
            # Database configuration
            'database': {
                'host': os.getenv('POSTGRESQL_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRESQL_PORT', '5432')),
                'database': os.getenv('POSTGRESQL_DATABASE', 'background_agents'),
                'user': os.getenv('POSTGRESQL_USER', 'postgres'),
                'password': os.getenv('POSTGRESQL_PASSWORD', ''),
                'pool_size': int(os.getenv('POSTGRESQL_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('POSTGRESQL_MAX_OVERFLOW', '20'))
            },
            
            # Agent configuration
            'agents': {
                'startup_delay': float(os.getenv('AGENT_STARTUP_DELAY', '2.0')),
                'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
                'recovery_attempts': int(os.getenv('RECOVERY_ATTEMPTS', '3')),
                'recovery_delay': float(os.getenv('RECOVERY_DELAY', '5.0'))
            },
            
            # Monitoring configuration
            'monitoring': {
                'heartbeat_interval': int(os.getenv('HEARTBEAT_INTERVAL', '60')),
                'performance_interval': int(os.getenv('PERFORMANCE_INTERVAL', '120')),
                'langsmith_interval': int(os.getenv('LANGSMITH_INTERVAL', '300')),
                'ai_help_interval': int(os.getenv('AI_HELP_INTERVAL', '30'))
            },
            
            # System configuration
            'system': {
                'graceful_shutdown_timeout': int(os.getenv('SHUTDOWN_TIMEOUT', '30')),
                'startup_timeout': int(os.getenv('STARTUP_TIMEOUT', '60')),
                'health_check_timeout': int(os.getenv('HEALTH_CHECK_TIMEOUT', '10'))
            }
        }
        
        return config
        
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def initialize_system(self) -> None:
        """Initialize the complete system infrastructure"""
        
        self.logger.info("Initializing background agents system...")
        
        try:
            # Initialize PostgreSQL adapter
            self.logger.info("Initializing PostgreSQL adapter...")
            connection_config = ConnectionConfig(
                host=self.config['database']['host'],
                port=self.config['database']['port'],
                database=self.config['database']['database'],
                user=self.config['database']['user'],
                password=self.config['database']['password'],
                min_connections=self.config['database']['pool_size'] // 2,
                max_connections=self.config['database']['pool_size']
                )
            
            self.postgresql_adapter = PostgreSQLAdapter(connection_config)
            await self.postgresql_adapter.initialize()
            
            # Verify database health
            health_check = await self.postgresql_adapter.health_check()
            if health_check['status'] != 'healthy':
                raise RuntimeError(f"PostgreSQL health check failed: {health_check}")
                
            self.logger.info("PostgreSQL adapter initialized successfully")
            
            # Initialize shared state
            self.logger.info("Initializing shared state...")
            self.shared_state = SharedState(self.postgresql_adapter)
            await self.shared_state.initialize()
            self.logger.info("Shared state initialized successfully")
            
            # Initialize system initializer
            self.logger.info("Running system initialization...")
            self.system_initializer = SystemInitializer(self.shared_state)
            await self.system_initializer.initialize()
            self.logger.info("System initialization completed")
            
            # Initialize agent coordinator
            self.logger.info("Initializing agent coordinator...")
            self.agent_coordinator = AgentCoordinator(self.shared_state)
            await self.agent_coordinator.initialize()
            self.logger.info("Agent coordinator initialized successfully")
            
            self.logger.info("System infrastructure initialization completed")
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            raise
            
    async def create_agents(self) -> None:
        """Create and configure all agent instances"""
        
        self.logger.info("Creating agent instances...")
        
        try:
            # Create HeartbeatHealthAgent
            self.logger.info("Creating HeartbeatHealthAgent...")
            heartbeat_agent = HeartbeatHealthAgent(
                agent_id="heartbeat_health_agent",
                shared_state=self.shared_state
                )
            heartbeat_agent.work_interval = self.config['monitoring']['heartbeat_interval']
            self.agents['heartbeat_health_agent'] = heartbeat_agent
            
            # Create PerformanceMonitor
            self.logger.info("Creating PerformanceMonitor...")
            performance_monitor = PerformanceMonitor(
                agent_id="performance_monitor",
                shared_state=self.shared_state
                )
            performance_monitor.work_interval = self.config['monitoring']['performance_interval']
            self.agents['performance_monitor'] = performance_monitor
            
            # Create LangSmithBridge
            self.logger.info("Creating LangSmithBridge...")
            langsmith_bridge = LangSmithBridge(
                agent_id="langsmith_bridge",
                shared_state=self.shared_state
                )
            langsmith_bridge.work_interval = self.config['monitoring']['langsmith_interval']
            self.agents['langsmith_bridge'] = langsmith_bridge
            
            # Create AIHelpAgent
            self.logger.info("Creating AIHelpAgent...")
            ai_help_agent = AIHelpAgent(
                agent_id="ai_help_agent",
                shared_state=self.shared_state
                )
            ai_help_agent.work_interval = self.config['monitoring']['ai_help_interval']
            self.agents['ai_help_agent'] = ai_help_agent
            
            self.logger.info(f"Created {len(self.agents)} agent instances successfully")
            
        except Exception as e:
            self.logger.error(f"Agent creation failed: {e}")
            raise
            
    async def start_agents(self) -> None:
        """Start all agents with coordinated startup using the agent coordinator"""
        
        self.logger.info("Starting background agents...")
        
        try:
            # Register all agents with coordinator first
            for agent_id in ['heartbeat_health_agent', 'performance_monitor', 'langsmith_bridge', 'ai_help_agent']:
                if agent_id in self.agents:
                    self.logger.info(f"Registering {agent_id} with coordinator...")
                    await self.agent_coordinator.register_agent(self.agents[agent_id])
            
            # Use coordinator to start all agents (this uses our fixed startup logic)
            self.logger.info("Starting agents through coordinator...")
            startup_results = await self.agent_coordinator.start_all_agents()
            
            # Track successful startups
            successful_agents = [agent_id for agent_id, success in startup_results.items() if success]
            failed_agents = [agent_id for agent_id, success in startup_results.items() if not success]
            
            if successful_agents:
                self.logger.info(f"Successfully started agents: {', '.join(successful_agents)}")
            
            if failed_agents:
                self.logger.error(f"Failed to start agents: {', '.join(failed_agents)}")
                # Don't raise exception for partial failures - let the system run with available agents
            
            self.logger.info(f"Agent startup completed: {len(successful_agents)}/{len(startup_results)} agents started successfully")
            
        except Exception as e:
            self.logger.error(f"Agent startup failed: {e}")
            raise
            
    async def run_agent_with_recovery(self, agent_id: str) -> None:
        """Run agent with automatic recovery capabilities"""
        
        agent = self.agents[agent_id]
        recovery_attempts = 0
        max_attempts = self.config['agents']['recovery_attempts']
        
        self.logger.info(f"Starting recovery runner for agent {agent_id}")
        
        while self.is_running and recovery_attempts <= max_attempts:
            try:
                self.logger.info(f"Starting agent {agent_id} (attempt {recovery_attempts + 1})")
                self.logger.debug(f"Agent {agent_id} runner state - is_running: {self.is_running}")
                
                # Start the agent
                self.logger.debug(f"Calling startup() for agent {agent_id}...")
                await agent.startup()
                self.logger.warning(f"Agent {agent_id} startup() method completed - this indicates the agent's main loop exited")
                
                # Reset recovery attempts on successful start
                recovery_attempts = 0
                
                # Agent startup() includes main loop, so if we reach here, agent has stopped
                if self.is_running:
                    self.logger.warning(f"Agent {agent_id} stopped unexpectedly while system is still running")
                    self.logger.debug(f"Agent {agent_id} final state - is_running: {agent.is_running}, shutdown_requested: {getattr(agent, 'shutdown_requested', 'N/A')}")
                else:
                    self.logger.info(f"Agent {agent_id} stopped because system is shutting down")
                    
            except Exception as e:
                recovery_attempts += 1
                self.logger.error(f"Agent {agent_id} failed (attempt {recovery_attempts}): {e}")
                
                if recovery_attempts <= max_attempts and self.is_running:
                    self.logger.info(f"Attempting recovery for {agent_id} in {self.config['agents']['recovery_delay']} seconds...")
                    await asyncio.sleep(self.config['agents']['recovery_delay'])
                    
                    # Notify coordinator of agent failure
                    try:
                        await self.agent_coordinator.handle_agent_failure(agent_id, str(e))
                    except Exception as coord_error:
                        self.logger.error(f"Failed to notify coordinator of agent failure: {coord_error}")
                else:
                    self.logger.error(f"Agent {agent_id} exceeded maximum recovery attempts")
                    break
                    
        self.logger.info(f"Agent {agent_id} runner exiting")
        
    async def monitor_system_health(self) -> None:
        """Monitor overall system health"""
        
        self.logger.info("Starting system health monitoring...")
        
        health_check_interval = self.config['agents']['health_check_interval']
        
        while self.is_running:
            try:
                # Get system health
                health_data = await self.shared_state.get_system_health()
                
                # Log health summary
                health_score = health_data.get('overall_health_score', 0)
                active_agents = health_data.get('active_agents', 0)
                total_agents = health_data.get('total_agents', 0)
                
                self.logger.info(
                    f"System Health: {health_score:.1f}/100, "
                    f"Agents: {active_agents}/{total_agents} active"
                    )
                
                # Check for system issues
                if health_score < 70:
                    self.logger.warning(f"System health degraded: {health_score:.1f}/100")
                    
                    # Log system health event
                    await self.shared_state.log_system_event(
                        'system_health_check',
                        {
                            'health_score': health_score,
                            'active_agents': active_agents,
                            'total_agents': total_agents,
                            'status': 'degraded' if health_score < 70 else 'healthy'
                        },
                        severity='WARNING' if health_score < 70 else 'INFO'
                        )
                    
                # Wait for next health check
                await asyncio.sleep(health_check_interval)
                
            except Exception as e:
                self.logger.error(f"System health monitoring error: {e}")
                await asyncio.sleep(health_check_interval)
                
        self.logger.info("System health monitoring stopped")
        
    async def start(self) -> None:
        """Start the complete background agents system"""
        
        try:
            self.startup_time = datetime.now(timezone.utc)
            self.logger.info("Starting Background Agents System...")
            
            # Initialize system infrastructure
            await self.initialize_system()
            
            # Create agent instances
            await self.create_agents()
            
            # Start agents
            await self.start_agents()
            
            # Mark system as running
            self.is_running = True
            
            # Log successful startup
            await self.shared_state.log_system_event(
                'system_startup',
                {
                    'startup_time': self.startup_time.isoformat(),
                    'agents_started': len(self.agents),
                    'system_version': '1.0.0'
                },
                severity='INFO'
                )
            
            # Log business metric
            await self.shared_state.log_business_metric(
                'system_reliability',
                'successful_startup',
                1.0,
                {'startup_duration': (datetime.now(timezone.utc) - self.startup_time).total_seconds()}
                )
            
            self.logger.info("Background Agents System started successfully")
            
            # Start system health monitoring
            health_monitor_task = asyncio.create_task(self.monitor_system_health())
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Cancel health monitoring
            health_monitor_task.cancel()
            
        except Exception as e:
            self.logger.error(f"System startup failed: {e}")
            raise
            
    async def shutdown(self) -> None:
        """Gracefully shutdown the system"""
        
        if not self.is_running:
            return
            
        self.logger.info("Initiating graceful system shutdown...")
        shutdown_start = time.time()
        
        try:
            # Mark system as shutting down
            self.is_running = False
            
            # Log shutdown event
            if self.shared_state:
                await self.shared_state.log_system_event(
                    'system_shutdown_start',
                    {'shutdown_reason': 'graceful', 'uptime': self.get_uptime()},
                    severity='INFO'
                    )
            
            # Stop agents gracefully
            self.logger.info("Stopping agents...")
            stop_tasks = []
            
            for agent_id, agent in self.agents.items():
                self.logger.info(f"Stopping {agent_id}...")
                stop_task = asyncio.create_task(agent.shutdown())
                stop_tasks.append(stop_task)
                
            # Wait for agents to stop with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*stop_tasks, return_exceptions=True),
                    timeout=self.config['system']['graceful_shutdown_timeout']
                    )
                self.logger.info("All agents stopped successfully")
            except asyncio.TimeoutError:
                self.logger.warning("Agent shutdown timeout exceeded")
                
            # Cancel any remaining agent tasks
            for agent_id, task in self.agent_tasks.items():
                if not task.done():
                    self.logger.info(f"Cancelling task for {agent_id}")
                    task.cancel()
                    
            # Stop coordinator
            if self.agent_coordinator:
                self.logger.info("Stopping agent coordinator...")
                await self.agent_coordinator.shutdown()
                
            # Close shared state
            if self.shared_state:
                self.logger.info("Closing shared state...")
                
                # Log final shutdown event
                await self.shared_state.log_system_event(
                    'system_shutdown_complete',
                    {
                        'shutdown_duration': time.time() - shutdown_start,
                        'uptime': self.get_uptime()
                    },
                    severity='INFO'
                    )
                
                # Log business metric
                await self.shared_state.log_business_metric(
                    'system_reliability',
                    'graceful_shutdown',
                    1.0,
                    {'shutdown_duration': time.time() - shutdown_start}
                    )
                
                await self.shared_state.close()
                
            # Close PostgreSQL adapter
            if self.postgresql_adapter:
                self.logger.info("Closing PostgreSQL adapter...")
                await self.postgresql_adapter.close()
                
            shutdown_duration = time.time() - shutdown_start
            self.logger.info(f"System shutdown completed in {shutdown_duration:.2f} seconds")
            
            # Signal shutdown complete
            self.shutdown_event.set()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise
            
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        if self.startup_time:
            return (datetime.now(timezone.utc) - self.startup_time).total_seconds()
        return 0.0
        
    async def status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        try:
            status_data = {
                'system_running': self.is_running,
                'startup_time': self.startup_time.isoformat() if self.startup_time else None,
                'uptime_seconds': self.get_uptime(),
                'agents_configured': len(self.agents),
                'agent_tasks_running': len([t for t in self.agent_tasks.values() if not t.done()]),
                'postgresql_connected': bool(self.postgresql_adapter and 
                                           (await self.postgresql_adapter.health_check())['status'] == 'healthy'),
                'system_health': await self.shared_state.get_system_health() if self.shared_state else None
            }
            
            return status_data
            
        except Exception as e:
            return {
                'system_running': self.is_running,
                'error': str(e),
                'status': 'error'
            }


async def main():
    """Main entry point for the background agents launcher"""
    
    launcher = BackgroundAgentsLauncher()
    
    try:
        # Start the system
        await launcher.start()
        
    except KeyboardInterrupt:
        launcher.logger.info("Received keyboard interrupt")
    except Exception as e:
        launcher.logger.error(f"System error: {e}")
        sys.exit(1)
    finally:
        # Ensure clean shutdown
        await launcher.shutdown()


if __name__ == "__main__":
    # Check for environment file
    env_file = Path(".env")
    if env_file.exists():
        # Load environment variables from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"✅ Loaded environment variables from {env_file}")
        except ImportError:
            # Fallback to manual loading if python-dotenv not available
            print("⚠️  python-dotenv not available, loading .env manually...")
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes if present
                            value = value.strip().strip('"').strip("'")
                            os.environ[key.strip()] = value
                print(f"✅ Manually loaded environment variables from {env_file}")
            except Exception as e:
                print(f"⚠️  Could not load .env file: {e}")
        except Exception as e:
            print(f"⚠️  Error loading .env file: {e}")
    else:
        print("ℹ️  No .env file found, using system environment variables")
            
    # Run the main function
    asyncio.run(main()) 