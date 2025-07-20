"""
Shared State Management System

Manages state synchronization between local development, cloud deployment, 
and Codex analysis environments using GitHub repository as central hub.
"""

import os
import json
import yaml
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import git
from git import Repo
import requests
from dataclasses import dataclass, asdict
from enum import Enum

class EnvironmentType(Enum):
    """Environment types for state management"""
    LOCAL = "local"
    CLOUD = "cloud"
    CODEX = "codex"
    GITHUB = "github"

class StateType(Enum):
    """State types for different analysis categories"""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    RECOMMENDATIONS = "recommendations"

@dataclass
class AnalysisResult:
    """Analysis result data structure"""
    timestamp: str
    environment: str
    repository_version: str
    analysis_type: str
    score: float
    metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    automated_fixes: List[Dict[str, Any]]

@dataclass
class SharedState:
    """Shared state data structure"""
    last_update: str
    environments: List[str]
    repository_version: str
    analysis_results: Dict[str, AnalysisResult]
    recommendations: List[Dict[str, Any]]
    priority_issues: List[Dict[str, Any]]
    automated_fixes: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    security_alerts: List[Dict[str, Any]]

class SharedStateManager:
    """Manages shared state across environments"""
    
    def __init__(self, 
                 repo_path: str = ".",
                 state_file: str = "shared_state.json",
                 config_file: str = "shared_state_config.yaml"):
        """
        Initialize shared state manager
        
        Args:
            repo_path: Path to git repository
            state_file: Name of state file in repository
            config_file: Configuration file path
        """
        self.repo_path = Path(repo_path)
        self.state_file = state_file
        self.config_file = config_file
        self.config = self.load_config()
        
        # Initialize git repository
        self.repo = self.initialize_repository()
        
        # Current environment
        self.environment = self.detect_environment()
        
        # State cache
        self.state_cache = None
        self.last_sync = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")
        
        # Default configuration
        return {
            'sync_interval': 300,  # 5 minutes
            'max_retries': 3,
            'retry_delay': 5,
            'backup_enabled': True,
            'notifications': {
                'enabled': False,
                'webhook_url': None
            }
        }
    
    def initialize_repository(self) -> Repo:
        """Initialize git repository"""
        try:
            return Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            self.logger.error(f"Invalid git repository at {self.repo_path}")
            raise
    
    def detect_environment(self) -> str:
        """Detect current environment"""
        # Check for environment variables
        if os.getenv('STREAMLIT_SERVER_PORT'):
            return EnvironmentType.CLOUD.value
        elif os.getenv('CODEX_ANALYSIS'):
            return EnvironmentType.CODEX.value
        elif os.getenv('GITHUB_ACTIONS'):
            return EnvironmentType.GITHUB.value
        else:
            return EnvironmentType.LOCAL.value
    
    def get_state_file_path(self) -> Path:
        """Get full path to state file"""
        return self.repo_path / self.state_file
    
    def load_state(self) -> Optional[SharedState]:
        """Load current state from file"""
        state_path = self.get_state_file_path()
        
        if not state_path.exists():
            return None
        
        try:
            with open(state_path, 'r') as f:
                data = json.load(f)
            
            # Convert to SharedState object
            analysis_results = {}
            for key, result_data in data.get('analysis_results', {}).items():
                analysis_results[key] = AnalysisResult(**result_data)
            
            return SharedState(
                last_update=data.get('last_update'),
                environments=data.get('environments', []),
                repository_version=data.get('repository_version'),
                analysis_results=analysis_results,
                recommendations=data.get('recommendations', []),
                priority_issues=data.get('priority_issues', []),
                automated_fixes=data.get('automated_fixes', []),
                performance_metrics=data.get('performance_metrics', {}),
                security_alerts=data.get('security_alerts', [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            return None
    
    def save_state(self, state: SharedState) -> bool:
        """Save state to file"""
        try:
            state_path = self.get_state_file_path()
            
            # Convert to dictionary
            data = asdict(state)
            
            # Convert AnalysisResult objects to dictionaries
            analysis_results = {}
            for key, result in state.analysis_results.items():
                analysis_results[key] = asdict(result)
            data['analysis_results'] = analysis_results
            
            # Create backup if enabled
            if self.config.get('backup_enabled') and state_path.exists():
                backup_path = state_path.with_suffix('.backup')
                state_path.rename(backup_path)
            
            # Save new state
            with open(state_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"State saved to {state_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            return False
    
    def update_state(self, 
                    analysis_type: str,
                    score: float,
                    metrics: Dict[str, Any],
                    issues: List[Dict[str, Any]] = None,
                    recommendations: List[Dict[str, Any]] = None,
                    automated_fixes: List[Dict[str, Any]] = None) -> bool:
        """
        Update state with new analysis results
        
        Args:
            analysis_type: Type of analysis performed
            score: Analysis score (0-100)
            metrics: Analysis metrics
            issues: Issues found
            recommendations: Recommendations
            automated_fixes: Automated fixes available
        """
        try:
            # Load current state or create new
            state = self.load_state()
            if state is None:
                state = SharedState(
                    last_update=datetime.now().isoformat(),
                    environments=[self.environment],
                    repository_version=self.get_repository_version(),
                    analysis_results={},
                    recommendations=[],
                    priority_issues=[],
                    automated_fixes=[],
                    performance_metrics={},
                    security_alerts=[]
                )
            
            # Update state
            state.last_update = datetime.now().isoformat()
            
            # Add environment if not present
            if self.environment not in state.environments:
                state.environments.append(self.environment)
            
            # Update repository version
            state.repository_version = self.get_repository_version()
            
            # Create analysis result
            analysis_result = AnalysisResult(
                timestamp=datetime.now().isoformat(),
                environment=self.environment,
                repository_version=state.repository_version,
                analysis_type=analysis_type,
                score=score,
                metrics=metrics,
                issues=issues or [],
                recommendations=recommendations or [],
                automated_fixes=automated_fixes or []
            )
            
            # Update analysis results
            state.analysis_results[analysis_type] = analysis_result
            
            # Update global recommendations and issues
            if recommendations:
                state.recommendations.extend(recommendations)
            
            if issues:
                # Filter priority issues
                priority_issues = [issue for issue in issues if issue.get('priority') in ['critical', 'high']]
                state.priority_issues.extend(priority_issues)
            
            if automated_fixes:
                state.automated_fixes.extend(automated_fixes)
            
            # Save updated state
            return self.save_state(state)
            
        except Exception as e:
            self.logger.error(f"Failed to update state: {e}")
            return False
    
    def get_repository_version(self) -> str:
        """Get current repository version (commit hash)"""
        try:
            return self.repo.head.commit.hexsha[:8]
        except Exception:
            return "unknown"
    
    def sync_with_remote(self) -> bool:
        """Sync state with remote repository"""
        try:
            # Pull latest changes
            origin = self.repo.remote('origin')
            origin.pull()
            
            # Load updated state
            state = self.load_state()
            if state:
                self.state_cache = state
                self.last_sync = time.time()
                self.logger.info("State synchronized with remote")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to sync with remote: {e}")
            return False
    
    def push_to_remote(self, commit_message: str = None) -> bool:
        """Push state changes to remote repository"""
        try:
            # Add state file
            self.repo.index.add([self.state_file])
            
            # Create commit
            if not commit_message:
                commit_message = f"Update shared state from {self.environment} - {datetime.now().isoformat()}"
            
            self.repo.index.commit(commit_message)
            
            # Push to remote
            origin = self.repo.remote('origin')
            origin.push()
            
            self.logger.info("State pushed to remote")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to push to remote: {e}")
            return False
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all analysis results"""
        state = self.load_state()
        if not state:
            return {}
        
        summary = {
            'last_update': state.last_update,
            'repository_version': state.repository_version,
            'environments': state.environments,
            'analysis_count': len(state.analysis_results),
            'total_recommendations': len(state.recommendations),
            'priority_issues': len(state.priority_issues),
            'automated_fixes': len(state.automated_fixes),
            'analysis_scores': {},
            'recent_issues': [],
            'top_recommendations': []
        }
        
        # Calculate average scores
        for analysis_type, result in state.analysis_results.items():
            summary['analysis_scores'][analysis_type] = result.score
        
        # Get recent issues (last 10)
        all_issues = []
        for result in state.analysis_results.values():
            all_issues.extend(result.issues)
        
        summary['recent_issues'] = sorted(
            all_issues, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )[:10]
        
        # Get top recommendations
        summary['top_recommendations'] = sorted(
            state.recommendations,
            key=lambda x: x.get('priority', 'low'),
            reverse=True
        )[:5]
        
        return summary
    
    def trigger_analysis(self, analysis_type: str, **kwargs) -> bool:
        """Trigger analysis and update state"""
        try:
            # This would integrate with actual analysis tools
            # For now, create a placeholder analysis result
            
            placeholder_metrics = {
                'files_analyzed': 0,
                'issues_found': 0,
                'complexity_score': 0.0,
                'maintainability_index': 0.0
            }
            
            return self.update_state(
                analysis_type=analysis_type,
                score=75.0,  # Placeholder score
                metrics=placeholder_metrics,
                issues=[],
                recommendations=[],
                automated_fixes=[]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to trigger analysis: {e}")
            return False
    
    def get_environment_status(self) -> Dict[str, Any]:
        """Get status of all environments"""
        state = self.load_state()
        if not state:
            return {}
        
        status = {
            'current_environment': self.environment,
            'last_sync': self.last_sync,
            'environments': {}
        }
        
        for env in state.environments:
            # Find latest analysis for each environment
            latest_analysis = None
            for result in state.analysis_results.values():
                if result.environment == env:
                    if not latest_analysis or result.timestamp > latest_analysis.timestamp:
                        latest_analysis = result
            
            status['environments'][env] = {
                'last_activity': latest_analysis.timestamp if latest_analysis else None,
                'analysis_count': len([r for r in state.analysis_results.values() if r.environment == env]),
                'status': 'active' if latest_analysis else 'inactive'
            }
        
        return status
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old analysis data"""
        try:
            state = self.load_state()
            if not state:
                return True
            
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            # Remove old analysis results
            old_results = []
            for key, result in state.analysis_results.items():
                try:
                    result_timestamp = datetime.fromisoformat(result.timestamp).timestamp()
                    if result_timestamp < cutoff_date:
                        old_results.append(key)
                except:
                    old_results.append(key)
            
            for key in old_results:
                del state.analysis_results[key]
            
            # Save cleaned state
            return self.save_state(state)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False

# Utility functions for easy integration
def create_shared_state_manager(repo_path: str = ".") -> SharedStateManager:
    """Create a shared state manager instance"""
    return SharedStateManager(repo_path=repo_path)

def update_analysis_state(analysis_type: str, 
                         score: float, 
                         metrics: Dict[str, Any],
                         repo_path: str = ".") -> bool:
    """Quick function to update analysis state"""
    manager = create_shared_state_manager(repo_path)
    return manager.update_state(analysis_type, score, metrics)

def get_analysis_summary(repo_path: str = ".") -> Dict[str, Any]:
    """Quick function to get analysis summary"""
    manager = create_shared_state_manager(repo_path)
    return manager.get_analysis_summary() 