#!/usr/bin/env python3
"""
Recovery Integration Utilities

This module provides integration between the existing shared state system
and the Process Recovery Agent.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .shared_state_manager import SharedStateManager

class RecoveryIntegration:
    """Integration utilities for recovery system"""
    
    def __init__(self, workspace_root: str = "/workspace"):
        self.workspace_root = Path(workspace_root)
        self.tasklog_path = self.workspace_root / "tasklog.md"
        self.shared_state_manager = SharedStateManager()
        
    def update_tasklog(self, message: str, task_name: str = None, status: str = None):
        """Update tasklog.md with structured message"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format message based on type
            if task_name and status:
                log_entry = f"[{timestamp}] TASK: {task_name} - {status} - {message}\n"
            else:
                log_entry = f"[{timestamp}] {message}\n"
            
            # Append to tasklog
            with open(self.tasklog_path, 'a') as f:
                f.write(log_entry)
                
            logging.info(f"Updated tasklog: {message}")
            
        except Exception as e:
            logging.error(f"Failed to update tasklog: {e}")
    
    def get_recommended_next_task(self) -> Optional[str]:
        """Get recommended next task based on current state"""
        try:
            # Load shared state
            state = self.shared_state_manager.load_state()
            if not state:
                return "initialization"
            
            # Check for pending recommendations
            recommendations = getattr(state, 'recommendations', [])
            if recommendations:
                return recommendations[0].get('action', '')
            
            # Check analysis results for next steps
            analysis_results = getattr(state, 'analysis_results', {})
            if not analysis_results:
                return "analysis"
            
            # Check if all analyses are complete
            completed_analyses = [name for name, result in analysis_results.items() 
                                if result.score > 0]
            
            if len(completed_analyses) < 5:  # Expected 5 analysis types
                return "analysis"
            
            # Check for deployment readiness
            if "deployment" not in analysis_results:
                return "deployment"
            
            return "documentation"  # Default fallback
            
        except Exception as e:
            logging.error(f"Error getting recommended task: {e}")
            return "initialization"
    
    def update_shared_state_with_recovery(self, recovery_info: Dict[str, Any]):
        """Update shared state with recovery information"""
        try:
            # Add recovery metadata
            recovery_metadata = {
                "recovery_timestamp": datetime.now().isoformat(),
                "recovery_count": recovery_info.get("recovery_count", 0),
                "last_recovery": recovery_info.get("last_recovery"),
                "active_tasks": recovery_info.get("active_tasks", []),
                "failed_tasks": recovery_info.get("failed_tasks", [])
            }
            
            # Update shared state
            self.shared_state_manager.update_state(
                "recovery_status",
                100,
                recovery_metadata
            )
            
            logging.info("Updated shared state with recovery information")
            
        except Exception as e:
            logging.error(f"Failed to update shared state with recovery info: {e}")
    
    def check_process_health(self) -> Dict[str, Any]:
        """Check overall process health"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "workspace_accessible": self.workspace_root.exists(),
            "shared_state_accessible": (self.workspace_root / "shared_state.json").exists(),
            "tasklog_accessible": self.tasklog_path.exists(),
            "recovery_agent_running": self._check_recovery_agent_status()
        }
        
        return health_status
    
    def _check_recovery_agent_status(self) -> bool:
        """Check if recovery agent is running"""
        try:
            pid_file = self.workspace_root / "recovery_agent.pid"
            if not pid_file.exists():
                return False
            
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is running
            import psutil
            return psutil.pid_exists(pid)
            
        except Exception:
            return False
    
    def trigger_manual_recovery(self, reason: str = "manual_trigger"):
        """Manually trigger recovery process"""
        try:
            self.update_tasklog(f"MANUAL RECOVERY: Triggered - {reason}")
            
            # Update shared state
            self.shared_state_manager.update_state(
                "manual_recovery",
                100,
                {
                    "triggered_at": datetime.now().isoformat(),
                    "reason": reason,
                    "status": "initiated"
                }
            )
            
            # Get recommended next task
            next_task = self.get_recommended_next_task()
            if next_task:
                self.update_tasklog(f"RECOMMENDATION: Next task - {next_task}")
            
            logging.info(f"Manual recovery triggered: {reason}")
            
        except Exception as e:
            logging.error(f"Failed to trigger manual recovery: {e}")
    
    def get_task_progress_summary(self) -> Dict[str, Any]:
        """Get summary of task progress"""
        try:
            # Read tasklog to get task history
            if not self.tasklog_path.exists():
                return {"error": "Tasklog not found"}
            
            with open(self.tasklog_path, 'r') as f:
                lines = f.readlines()
            
            # Count different task statuses
            task_counts = {
                "completed": 0,
                "failed": 0,
                "in_progress": 0,
                "timeout": 0
            }
            
            for line in lines:
                if "TASK:" in line:
                    if "completed" in line.lower():
                        task_counts["completed"] += 1
                    elif "failed" in line.lower():
                        task_counts["failed"] += 1
                    elif "in_progress" in line.lower():
                        task_counts["in_progress"] += 1
                    elif "timeout" in line.lower():
                        task_counts["timeout"] += 1
            
            return {
                "timestamp": datetime.now().isoformat(),
                "task_counts": task_counts,
                "total_tasks": sum(task_counts.values()),
                "last_activity": lines[-1].strip() if lines else "No activity"
            }
            
        except Exception as e:
            logging.error(f"Failed to get task progress summary: {e}")
            return {"error": str(e)}