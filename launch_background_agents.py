#!/usr/bin/env python3
"""
Background Agents System Launcher

Comprehensive launcher for the PostgreSQL-based background agents monitoring system.
Provides agent lifecycle management, health monitoring, and graceful shutdown handling.
"""

import asyncio
import logging
import signal
import sys
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import traceback

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from background_agents.coordination.shared_state import SharedState
from background_agents.coordination.agent_coordinator import AgentCoordinator
from background_agents.coordination.system_initializer import SystemInitializer
from background_agents.monitoring.heartbeat_health_agent import HeartbeatHealthAgent
from background_agents.monitoring.performance_monitor import PerformanceMonitor
from background_agents.monitoring.langsmith_bridge import LangSmithBridge
from background_agents.ai_help.ai_help_agent import AIHelpAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BackgroundAgentsLauncher:
    """
    Main launcher class for the background agents system.
    
    Manages the complete lifecycle of the agent system including:
    - System initialization and database setup
    - Agent registration and startup
    - Health monitoring and coordination
    - Graceful shutdown and cleanup
    """
    
    def __init__(self):
        """Initialize the launcher."""
        self.shared_state = None
        self.system_initializer = None
        self.agent_coordinator = None
        self.agents = {}
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Configuration
        self.config = {
            'startup_timeout': 60,
            'shutdown_timeout': 30,
            'health_check_interval': 30,
            'max_startup_retries': 3
        }
        
        logger.info("Background Agents Launcher initialized")
    
    async def initialize_system(self):
        """Initialize the core system components."""
        try:
            logger.info("Initializing background agents system...")
            
            # Initialize shared state
            self.shared_state = SharedState()
            await self.shared_state.initialize()
            
            # Initialize system components
            self.system_initializer = SystemInitializer(self.shared_state)
            await self.system_initializer.initialize()
            
            # Initialize agent coordinator
            self.agent_coordinator = AgentCoordinator(self.shared_state)
            await self.agent_coordinator.initialize()
            
            # Log system initialization
            await self.shared_state.log_system_event(
                'system_initialized',
                {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'launcher_pid': os.getpid(),
                    'python_version': sys.version,
                    'platform': sys.platform
                },
                severity='INFO'
            )
            
            logger.info("System initialization completed successfully")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def create_agents(self):
        """Create and configure all agents."""
        try:
            logger.info("Creating background agents...")
            
            # Agent configurations
            agent_configs = {
                'heartbeat_health_agent': {
                    'class': HeartbeatHealthAgent,
                    'enabled': os.getenv('HEARTBEAT_HEALTH_AGENT_ENABLED', 'true').lower() == 'true',
                    'config': {
                        'heartbeat_interval': 30,
                        'max_retries': 5,
                        'work_interval': 60
                    }
                },
                'performance_monitor': {
                    'class': PerformanceMonitor,
                    'enabled': os.getenv('PERFORMANCE_MONITOR_ENABLED', 'true').lower() == 'true',
                    'config': {
                        'collection_interval': 60,
                        'heartbeat_interval': 60,
                        'max_retries': 3,
                        'work_interval': 30
                    }
                },
                'langsmith_bridge': {
                    'class': LangSmithBridge,
                    'enabled': os.getenv('LANGSMITH_BRIDGE_ENABLED', 'true').lower() == 'true',
                    'config': {
                        'api_key': os.getenv('LANGSMITH_API_KEY'),
                        'project': os.getenv('LANGSMITH_PROJECT', 'background-agents-system'),
                        'heartbeat_interval': 60,
                        'max_retries': 3,
                        'work_interval': 45
                    }
                },
                'ai_help_agent': {
                    'class': AIHelpAgent,
                    'enabled': os.getenv('AI_HELP_AGENT_ENABLED', 'true').lower() == 'true',
                    'config': {
                        'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                        'temperature': 0.7,
                        'max_tokens': 2000,
                        'heartbeat_interval': 60,
                        'max_retries': 3,
                        'work_interval': 30
                    }
                }
            }
            
            # Create enabled agents
            for agent_id, agent_info in agent_configs.items():
                if agent_info['enabled']:
                    try:
                        agent_class = agent_info['class']
                        agent_config = agent_info['config']
                        
                        # Create agent instance
                        agent = agent_class(agent_id, self.shared_state, **agent_config)
                        self.agents[agent_id] = agent
                        
                        # Register with coordinator
                        await self.agent_coordinator.register_agent(agent)
                        
                        logger.info(f"Agent {agent_id} created and registered")
                        
                    except Exception as e:
                        logger.error(f"Failed to create agent {agent_id}: {e}")
                        # Continue with other agents
                else:
                    logger.info(f"Agent {agent_id} is disabled, skipping")
            
            logger.info(f"Created {len(self.agents)} agents successfully")
            
        except Exception as e:
            logger.error(f"Agent creation failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def start_agents(self):
        """Start all created agents."""
        try:
            logger.info("Starting background agents...")
            
            # Start agents through coordinator
            startup_tasks = []
            for agent_id, agent in self.agents.items():
                task = asyncio.create_task(
                    self._start_agent_with_retry(agent_id, agent)
                )
                startup_tasks.append(task)
            
            # Wait for all agents to start
            results = await asyncio.gather(*startup_tasks, return_exceptions=True)
            
            # Check results
            successful_starts = 0
            for i, result in enumerate(results):
                agent_id = list(self.agents.keys())[i]
                if isinstance(result, Exception):
                    logger.error(f"Failed to start agent {agent_id}: {result}")
                else:
                    successful_starts += 1
                    logger.info(f"Agent {agent_id} started successfully")
            
            if successful_starts == 0:
                raise RuntimeError("No agents started successfully")
            
            logger.info(f"Started {successful_starts}/{len(self.agents)} agents successfully")
            
            # Log system startup completion
            await self.shared_state.log_system_event(
                'system_startup_completed',
                {
                    'agents_started': successful_starts,
                    'total_agents': len(self.agents),
                    'startup_time': time.time()
                },
                severity='INFO'
            )
            
        except Exception as e:
            logger.error(f"Agent startup failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def _start_agent_with_retry(self, agent_id: str, agent, max_retries: int = 3):
        """Start an agent with retry logic."""
        for attempt in range(max_retries):
            try:
                await agent.start()
                return True
            except Exception as e:
                logger.warning(f"Agent {agent_id} start attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
    
    async def monitor_system(self):
        """Monitor system health and manage agents."""
        logger.info("Starting system monitoring...")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Check system health
                health_status = await self.shared_state.get_system_health()
                
                # Log health summary
                logger.debug(f"System health: {health_status['health_percentage']:.1f}% "
                           f"({health_status['healthy_agents']}/{health_status['active_agents']} agents healthy)")
                
                # Check for failed agents and restart if needed
                await self._check_and_restart_failed_agents()
                
                # Wait for next monitoring cycle
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=self.config['health_check_interval']
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Continue monitoring
                    
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _check_and_restart_failed_agents(self):
        """Check for failed agents and restart them."""
        try:
            agents_status = await self.shared_state.get_registered_agents()
            
            for agent_status in agents_status:
                agent_id = agent_status['agent_id']
                state = agent_status.get('state')
                
                if state == 'error' and agent_id in self.agents:
                    logger.warning(f"Agent {agent_id} is in error state, attempting restart...")
                    
                    try:
                        # Stop the failed agent
                        await self.agents[agent_id].stop()
                        
                        # Wait a moment
                        await asyncio.sleep(5)
                        
                        # Restart the agent
                        await self.agents[agent_id].start()
                        
                        logger.info(f"Agent {agent_id} restarted successfully")
                        
                        # Log restart event
                        await self.shared_state.log_system_event(
                            'agent_restarted',
                            {'agent_id': agent_id, 'reason': 'error_state'},
                            agent_id=agent_id,
                            severity='INFO'
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to restart agent {agent_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error checking failed agents: {e}")
    
    async def shutdown_system(self):
        """Gracefully shutdown the system."""
        logger.info("Initiating system shutdown...")
        
        try:
            # Signal shutdown
            self.running = False
            self.shutdown_event.set()
            
            # Stop all agents
            if self.agents:
                logger.info("Stopping agents...")
                stop_tasks = []
                
                for agent_id, agent in self.agents.items():
                    task = asyncio.create_task(self._stop_agent_safely(agent_id, agent))
                    stop_tasks.append(task)
                
                # Wait for all agents to stop
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*stop_tasks, return_exceptions=True),
                        timeout=self.config['shutdown_timeout']
                    )
                except asyncio.TimeoutError:
                    logger.warning("Some agents did not stop within timeout")
            
            # Stop coordinator
            if self.agent_coordinator:
                await self.agent_coordinator.shutdown()
            
            # Log shutdown event
            if self.shared_state:
                await self.shared_state.log_system_event(
                    'system_shutdown',
                    {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'agents_count': len(self.agents)
                    },
                    severity='INFO'
                )
                
                # Close shared state
                await self.shared_state.close()
            
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            logger.error(traceback.format_exc())
    
    async def _stop_agent_safely(self, agent_id: str, agent):
        """Safely stop an agent with error handling."""
        try:
            await agent.stop()
            logger.info(f"Agent {agent_id} stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown_system())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Windows doesn't have SIGUSR1
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, signal_handler)
    
    async def run(self):
        """Main run method for the launcher."""
        try:
            logger.info("Starting Background Agents System...")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Initialize system
            await self.initialize_system()
            
            # Create agents
            await self.create_agents()
            
            # Start agents
            await self.start_agents()
            
            # Mark system as running
            self.running = True
            
            logger.info("Background Agents System is now running!")
            logger.info(f"System PID: {os.getpid()}")
            logger.info(f"Active agents: {list(self.agents.keys())}")
            
            # Start monitoring
            await self.monitor_system()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"System error: {e}")
            logger.error(traceback.format_exc())
        finally:
            await self.shutdown_system()

def create_directories():
    """Create necessary directories."""
    directories = ['logs', 'data', 'temp', 'backups']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def check_environment():
    """Check environment prerequisites."""
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set up your environment variables. See config_template.env for reference.")
        return False
    
    return True

async def main():
    """Main entry point."""
    print("=" * 60)
    print("Background Agents System Launcher")
    print("PostgreSQL-based Agent Coordination & Monitoring")
    print("=" * 60)
    
    # Create directories
    create_directories()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create and run launcher
    launcher = BackgroundAgentsLauncher()
    
    try:
        await launcher.run()
    except Exception as e:
        logger.error(f"Launcher failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 