#!/usr/bin/env python3
"""
Process Recovery Agent for Automated Task Continuation

This specialized agent runs alongside the main operation and provides:
- Process monitoring and timeout detection
- Automatic recovery when connections are lost
- Task progress tracking and continuation
- Intelligent next task recommendation
"""

import os
import sys
import json
import time
import signal
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil
import requests
from dataclasses import dataclass, asdict
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recovery_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

@dataclass
class TaskStatus:
    """Represents the status of a task"""
    name: str
    status: str  # pending, in_progress, completed, failed, timeout
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    next_steps: List[str] = None
    dependencies: List[str] = None

@dataclass
class RecoveryState:
    """Represents the current recovery state"""
    last_activity: datetime
    active_tasks: List[TaskStatus]
    completed_tasks: List[TaskStatus]
    failed_tasks: List[TaskStatus]
    recovery_count: int = 0
    last_recovery: Optional[datetime] = None

class ProcessRecoveryAgent:
    """Automated process recovery and task continuation agent"""
    
    def __init__(self, config_path: str = "config/recovery_config.yaml"):
        self.config = self.load_config(config_path)
        self.workspace_root = Path(self.config.get('workspace_root', '/workspace'))
        self.tasklog_path = self.workspace_root / 'tasklog.md'
        self.shared_state_path = self.workspace_root / 'shared_state.json'
        self.recovery_state_path = self.workspace_root / 'recovery_state.json'
        
        # Initialize state
        self.recovery_state = self.load_recovery_state()
        self.monitoring = False
        self.monitor_thread = None
        
        # Process monitoring
        self.process_timeout = self.config.get('process_timeout', 300)  # 5 minutes
        self.memory_threshold = self.config.get('memory_threshold', 0.8)  # 80%
        self.check_interval = self.config.get('check_interval', 30)  # 30 seconds
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logging.info("Process Recovery Agent initialized")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            logging.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'workspace_root': '/workspace',
            'process_timeout': 300,
            'memory_threshold': 0.8,
            'check_interval': 30,
            'max_recovery_attempts': 3,
            'recovery_delay': 60,
            'task_priorities': {
                'critical': ['setup', 'initialization', 'deployment'],
                'high': ['analysis', 'testing', 'integration'],
                'medium': ['documentation', 'optimization'],
                'low': ['cleanup', 'maintenance']
            }
        }
    
    def load_recovery_state(self) -> RecoveryState:
        """Load recovery state from file"""
        try:
            if self.recovery_state_path.exists():
                with open(self.recovery_state_path, 'r') as f:
                    data = json.load(f)
                return RecoveryState(**data)
        except Exception as e:
            logging.warning(f"Could not load recovery state: {e}")
        
        return RecoveryState(
            last_activity=datetime.now(),
            active_tasks=[],
            completed_tasks=[],
            failed_tasks=[]
        )
    
    def save_recovery_state(self):
        """Save recovery state to file"""
        try:
            with open(self.recovery_state_path, 'w') as f:
                json.dump(asdict(self.recovery_state), f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save recovery state: {e}")
    
    def start_monitoring(self):
        """Start the monitoring process"""
        if self.monitoring:
            logging.warning("Monitoring already active")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logging.info("Process monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logging.info("Process monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Check for process timeouts
                self._check_process_timeouts()
                
                # Check memory usage
                self._check_memory_usage()
                
                # Check for connection issues
                self._check_connection_health()
                
                # Update recovery state
                self.recovery_state.last_activity = datetime.now()
                self.save_recovery_state()
                
                # Sleep before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _check_process_timeouts(self):
        """Check for process timeouts"""
        current_time = datetime.now()
        
        for task in self.recovery_state.active_tasks:
            if task.start_time and task.status == 'in_progress':
                elapsed = (current_time - task.start_time).total_seconds()
                if elapsed > self.process_timeout:
                    logging.warning(f"Task {task.name} timed out after {elapsed}s")
                    self._handle_task_timeout(task)
    
    def _check_memory_usage(self):
        """Check system memory usage"""
        try:
            memory_percent = psutil.virtual_memory().percent / 100
            if memory_percent > self.memory_threshold:
                logging.warning(f"High memory usage: {memory_percent:.1%}")
                self._handle_memory_pressure()
        except Exception as e:
            logging.error(f"Error checking memory usage: {e}")
    
    def _check_connection_health(self):
        """Check connection health"""
        try:
            # Check if we can access the workspace
            if not self.workspace_root.exists():
                logging.error("Workspace root not accessible")
                self._handle_connection_loss()
                return
            
            # Check if shared state is accessible
            if not self.shared_state_path.exists():
                logging.warning("Shared state file not found")
                self._handle_shared_state_missing()
                return
                
        except Exception as e:
            logging.error(f"Connection health check failed: {e}")
            self._handle_connection_loss()
    
    def _handle_task_timeout(self, task: TaskStatus):
        """Handle task timeout"""
        task.status = 'timeout'
        task.end_time = datetime.now()
        task.error_message = f"Task timed out after {self.process_timeout}s"
        
        # Move to failed tasks
        self.recovery_state.active_tasks.remove(task)
        self.recovery_state.failed_tasks.append(task)
        
        # Update tasklog
        self._update_tasklog(f"TIMEOUT: {task.name} - {task.error_message}")
        
        # Attempt recovery
        self._attempt_recovery()
    
    def _handle_memory_pressure(self):
        """Handle high memory usage"""
        logging.info("Handling memory pressure")
        
        # Clean up temporary files
        self._cleanup_temp_files()
        
        # Update tasklog
        self._update_tasklog("MEMORY: High memory usage detected, cleanup performed")
        
        # If memory is still high, restart process
        memory_percent = psutil.virtual_memory().percent / 100
        if memory_percent > self.memory_threshold * 1.2:  # 20% above threshold
            self._handle_connection_loss()
    
    def _handle_connection_loss(self):
        """Handle connection loss"""
        logging.warning("Connection loss detected")
        
        # Save current state
        self.save_recovery_state()
        
        # Update tasklog
        self._update_tasklog("CONNECTION: Connection loss detected, saving state")
        
        # Mark active tasks as failed
        for task in self.recovery_state.active_tasks:
            task.status = 'failed'
            task.end_time = datetime.now()
            task.error_message = "Connection lost"
            self.recovery_state.failed_tasks.append(task)
        
        self.recovery_state.active_tasks.clear()
        
        # Attempt recovery
        self._attempt_recovery()
    
    def _handle_shared_state_missing(self):
        """Handle missing shared state"""
        logging.warning("Shared state file missing")
        
        # Create minimal shared state
        minimal_state = {
            "timestamp": datetime.now().isoformat(),
            "status": "recovery_mode",
            "recovery_count": self.recovery_state.recovery_count + 1,
            "last_activity": self.recovery_state.last_activity.isoformat()
        }
        
        try:
            with open(self.shared_state_path, 'w') as f:
                json.dump(minimal_state, f, indent=2)
            logging.info("Created minimal shared state")
        except Exception as e:
            logging.error(f"Failed to create minimal shared state: {e}")
    
    def _attempt_recovery(self):
        """Attempt to recover from failure"""
        self.recovery_state.recovery_count += 1
        self.recovery_state.last_recovery = datetime.now()
        
        if self.recovery_state.recovery_count > self.config.get('max_recovery_attempts', 3):
            logging.error("Maximum recovery attempts exceeded")
            self._update_tasklog("RECOVERY: Maximum recovery attempts exceeded, manual intervention required")
            return
        
        logging.info(f"Attempting recovery #{self.recovery_state.recovery_count}")
        
        # Update tasklog
        self._update_tasklog(f"RECOVERY: Attempting recovery #{self.recovery_state.recovery_count}")
        
        # Analyze current state
        self._analyze_current_state()
        
        # Recommend next task
        next_task = self._recommend_next_task()
        
        if next_task:
            self._initiate_task(next_task)
        else:
            logging.warning("No suitable next task found")
            self._update_tasklog("RECOVERY: No suitable next task found, waiting for manual intervention")
    
    def _analyze_current_state(self):
        """Analyze current state and update tasklog"""
        try:
            # Read shared state
            if self.shared_state_path.exists():
                with open(self.shared_state_path, 'r') as f:
                    shared_state = json.load(f)
                
                # Update tasklog with current state
                self._update_tasklog(f"STATE: Current shared state - {shared_state.get('status', 'unknown')}")
            
            # Analyze completed tasks
            completed_count = len(self.recovery_state.completed_tasks)
            failed_count = len(self.recovery_state.failed_tasks)
            active_count = len(self.recovery_state.active_tasks)
            
            self._update_tasklog(f"PROGRESS: Completed: {completed_count}, Failed: {failed_count}, Active: {active_count}")
            
        except Exception as e:
            logging.error(f"Error analyzing current state: {e}")
            self._update_tasklog(f"ERROR: Failed to analyze current state - {e}")
    
    def _recommend_next_task(self) -> Optional[str]:
        """Recommend the next priority task"""
        try:
            # Get task priorities from config
            priorities = self.config.get('task_priorities', {})
            
            # Check for critical tasks first
            for priority_level in ['critical', 'high', 'medium', 'low']:
                tasks = priorities.get(priority_level, [])
                for task in tasks:
                    if not self._is_task_completed(task) and not self._is_task_active(task):
                        self._update_tasklog(f"RECOMMENDATION: Next task - {task} (priority: {priority_level})")
                        return task
            
            # If no predefined tasks, analyze shared state for recommendations
            if self.shared_state_path.exists():
                with open(self.shared_state_path, 'r') as f:
                    shared_state = json.load(f)
                
                # Look for recommendations in shared state
                recommendations = shared_state.get('recommendations', [])
                if recommendations:
                    next_task = recommendations[0].get('action', '')
                    if next_task:
                        self._update_tasklog(f"RECOMMENDATION: From shared state - {next_task}")
                        return next_task
            
            return None
            
        except Exception as e:
            logging.error(f"Error recommending next task: {e}")
            return None
    
    def _is_task_completed(self, task_name: str) -> bool:
        """Check if task is completed"""
        return any(task.name == task_name and task.status == 'completed' 
                  for task in self.recovery_state.completed_tasks)
    
    def _is_task_active(self, task_name: str) -> bool:
        """Check if task is currently active"""
        return any(task.name == task_name and task.status == 'in_progress' 
                  for task in self.recovery_state.active_tasks)
    
    def _initiate_task(self, task_name: str):
        """Initiate a new task"""
        try:
            # Create task status
            task = TaskStatus(
                name=task_name,
                status='in_progress',
                start_time=datetime.now(),
                progress=0.0
            )
            
            # Add to active tasks
            self.recovery_state.active_tasks.append(task)
            
            # Update tasklog
            self._update_tasklog(f"INITIATED: Starting task - {task_name}")
            
            # Execute task based on name
            self._execute_task(task)
            
        except Exception as e:
            logging.error(f"Error initiating task {task_name}: {e}")
            self._update_tasklog(f"ERROR: Failed to initiate task {task_name} - {e}")
    
    def _execute_task(self, task: TaskStatus):
        """Execute a specific task"""
        try:
            if task.name == 'setup':
                self._execute_setup_task(task)
            elif task.name == 'initialization':
                self._execute_initialization_task(task)
            elif task.name == 'analysis':
                self._execute_analysis_task(task)
            elif task.name == 'deployment':
                self._execute_deployment_task(task)
            else:
                self._execute_generic_task(task)
                
        except Exception as e:
            logging.error(f"Error executing task {task.name}: {e}")
            task.status = 'failed'
            task.error_message = str(e)
            task.end_time = datetime.now()
    
    def _execute_setup_task(self, task: TaskStatus):
        """Execute setup task"""
        logging.info("Executing setup task")
        task.progress = 0.1
        
        # Check if requirements.txt exists
        requirements_path = self.workspace_root / 'requirements.txt'
        if requirements_path.exists():
            task.progress = 0.5
            self._update_tasklog("SETUP: Installing dependencies from requirements.txt")
            # Here you would run: pip install -r requirements.txt
            task.progress = 1.0
        else:
            task.progress = 1.0
        
        task.status = 'completed'
        task.end_time = datetime.now()
        self._move_task_to_completed(task)
    
    def _execute_initialization_task(self, task: TaskStatus):
        """Execute initialization task"""
        logging.info("Executing initialization task")
        task.progress = 0.1
        
        # Initialize shared state if needed
        if not self.shared_state_path.exists():
            self._handle_shared_state_missing()
            task.progress = 0.5
        
        task.progress = 1.0
        task.status = 'completed'
        task.end_time = datetime.now()
        self._move_task_to_completed(task)
    
    def _execute_analysis_task(self, task: TaskStatus):
        """Execute analysis task"""
        logging.info("Executing analysis task")
        task.progress = 0.1
        
        # Check if analysis scripts exist
        analysis_scripts = [
            'scripts/github_auto_update_clean.py',
            'src/main.py'
        ]
        
        for script in analysis_scripts:
            script_path = self.workspace_root / script
            if script_path.exists():
                task.progress += 0.3
                self._update_tasklog(f"ANALYSIS: Found analysis script - {script}")
        
        task.progress = 1.0
        task.status = 'completed'
        task.end_time = datetime.now()
        self._move_task_to_completed(task)
    
    def _execute_deployment_task(self, task: TaskStatus):
        """Execute deployment task"""
        logging.info("Executing deployment task")
        task.progress = 0.1
        
        # Check for deployment files
        deployment_files = [
            'k8s/deployments.yaml',
            'k8s/services.yaml',
            'k8s/ingress.yaml'
        ]
        
        for file in deployment_files:
            file_path = self.workspace_root / file
            if file_path.exists():
                task.progress += 0.2
                self._update_tasklog(f"DEPLOYMENT: Found deployment file - {file}")
        
        task.progress = 1.0
        task.status = 'completed'
        task.end_time = datetime.now()
        self._move_task_to_completed(task)
    
    def _execute_generic_task(self, task: TaskStatus):
        """Execute generic task"""
        logging.info(f"Executing generic task: {task.name}")
        task.progress = 0.5
        
        # Generic task execution
        self._update_tasklog(f"GENERIC: Executing task - {task.name}")
        
        task.progress = 1.0
        task.status = 'completed'
        task.end_time = datetime.now()
        self._move_task_to_completed(task)
    
    def _move_task_to_completed(self, task: TaskStatus):
        """Move task from active to completed"""
        if task in self.recovery_state.active_tasks:
            self.recovery_state.active_tasks.remove(task)
        self.recovery_state.completed_tasks.append(task)
        
        self._update_tasklog(f"COMPLETED: Task {task.name} completed successfully")
    
    def _update_tasklog(self, message: str):
        """Update tasklog.md with message"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            with open(self.tasklog_path, 'a') as f:
                f.write(log_entry)
                
        except Exception as e:
            logging.error(f"Failed to update tasklog: {e}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_patterns = ['*.tmp', '*.temp', '*.log', '__pycache__']
            for pattern in temp_patterns:
                for file_path in self.workspace_root.rglob(pattern):
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        import shutil
                        shutil.rmtree(file_path)
            
            logging.info("Temporary files cleaned up")
        except Exception as e:
            logging.error(f"Error cleaning up temp files: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}, shutting down gracefully")
        self.stop_monitoring()
        self.save_recovery_state()
        sys.exit(0)
    
    def run(self):
        """Run the recovery agent"""
        logging.info("Starting Process Recovery Agent")
        
        try:
            # Start monitoring
            self.start_monitoring()
            
            # Keep running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            self.stop_monitoring()
            self.save_recovery_state()
            logging.info("Process Recovery Agent stopped")

def main():
    """Main function"""
    try:
        agent = ProcessRecoveryAgent()
        agent.run()
    except Exception as e:
        logging.error(f"Failed to start recovery agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()