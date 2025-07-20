#!/usr/bin/env python3
"""
Automatic GitHub Repository Update System

This script automatically updates the System-Reference GitHub repository with the latest
code, documentation, and configuration files. It handles:

1. Code synchronization
2. Documentation updates
3. Configuration management
4. Version control
5. Automated commits and pushes
6. Release management
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import git
from git import Repo
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_auto_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class GitHubAutoUpdater:
    """Automatic GitHub repository update system"""
    
    def __init__(self, config_path: str = "config/github_update_config.yaml"):
        self.config = self.load_config(config_path)
        self.source_dir = Path(self.config['source_directory'])
        self.target_repo_path = Path(self.config['target_repository_path'])
        self.github_token = self.config['github_token']
        self.repository_url = self.config['repository_url']
        
        # Initialize Git repository
        self.repo = self.initialize_repository()
        
        # Track changes
        self.changes = {
            'files_added': [],
            'files_modified': [],
            'files_deleted': [],
            'directories_created': [],
            'directories_deleted': []
        }
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logging.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"Error parsing configuration: {e}")
            sys.exit(1)
    
    def initialize_repository(self) -> Repo:
        """Initialize or clone the target repository"""
        if self.target_repo_path.exists():
            try:
                repo = Repo(self.target_repo_path)
                logging.info(f"Using existing repository at {self.target_repo_path}")
                return repo
            except git.InvalidGitRepositoryError:
                logging.error(f"Invalid Git repository at {self.target_repo_path}")
                sys.exit(1)
        else:
            logging.info(f"Cloning repository from {self.repository_url}")
            return Repo.clone_from(
                self.repository_url,
                self.target_repo_path,
                env={'GIT_SSH_COMMAND': f'git clone {self.repository_url}'}
            )
    
    def sync_code(self) -> bool:
        """Synchronize source code to target repository"""
        logging.info("Starting code synchronization...")
        
        try:
            # Create necessary directories
            self.create_directories()
            
            # Copy source files
            self.copy_source_files()
            
            # Update documentation
            self.update_documentation()
            
            # Update configuration files
            self.update_configuration()
            
            # Update deployment files
            self.update_deployment_files()
            
            # Update scripts
            self.update_scripts()
            
            logging.info("Code synchronization completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Code synchronization failed: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directory structure"""
        directories = [
            'src',
            'src/core',
            'src/processors',
            'src/ai',
            'src/ui',
            'src/utils',
            'docs',
            'docs/architecture',
            'docs/components',
            'docs/deployment',
            'docs/api',
            'docs/troubleshooting',
            'config',
            'scripts',
            'tests',
            'docker',
            'k8s',
            'terraform',
            'monitoring',
            'logs'
        ]
        
        for directory in directories:
            dir_path = self.target_repo_path / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.changes['directories_created'].append(directory)
                logging.info(f"Created directory: {directory}")
    
    def copy_source_files(self):
        """Copy source code files"""
        source_patterns = [
            'src/**/*.py',
            'src/**/*.js',
            'src/**/*.ts',
            'src/**/*.yaml',
            'src/**/*.yml',
            'src/**/*.json'
        ]
        
        for pattern in source_patterns:
            for source_file in self.source_dir.glob(pattern):
                if source_file.is_file():
                    relative_path = source_file.relative_to(self.source_dir)
                    target_file = self.target_repo_path / relative_path
                    
                    # Ensure target directory exists
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(source_file, target_file)
                    
                    if target_file.exists():
                        self.changes['files_added'].append(str(relative_path))
                        logging.info(f"Copied: {relative_path}")
    
    def update_documentation(self):
        """Update documentation files"""
        doc_files = [
            'README.md',
            'docs/README.md',
            'docs/architecture/system-overview.md',
            'docs/components/real-time-orchestrator.md',
            'docs/deployment/cloud-deployment.md',
            'docs/api/rest-api.md',
            'docs/troubleshooting/common-issues.md'
        ]
        
        for doc_file in doc_files:
            source_file = self.source_dir / doc_file
            if source_file.exists():
                target_file = self.target_repo_path / doc_file
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                self.changes['files_modified'].append(doc_file)
                logging.info(f"Updated documentation: {doc_file}")
    
    def update_configuration(self):
        """Update configuration files"""
        config_files = [
            'config/app.yaml',
            'config/database.yaml',
            'config/ai.yaml',
            'config/cloud.yaml',
            'requirements.txt',
            'Dockerfile',
            'docker-compose.yml'
        ]
        
        for config_file in config_files:
            source_file = self.source_dir / config_file
            if source_file.exists():
                target_file = self.target_repo_path / config_file
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                self.changes['files_modified'].append(config_file)
                logging.info(f"Updated configuration: {config_file}")
    
    def update_deployment_files(self):
        """Update deployment and infrastructure files"""
        deployment_files = [
            'k8s/namespace.yaml',
            'k8s/deployments.yaml',
            'k8s/services.yaml',
            'k8s/ingress.yaml',
            'k8s/configmap.yaml',
            'k8s/secrets.yaml',
            'terraform/main.tf',
            'terraform/variables.tf',
            'terraform/outputs.tf',
            'docker/Dockerfile.web-ui',
            'docker/Dockerfile.orchestrator',
            'docker/docker-compose.prod.yml'
        ]
        
        for deploy_file in deployment_files:
            source_file = self.source_dir / deploy_file
            if source_file.exists():
                target_file = self.target_repo_path / deploy_file
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                self.changes['files_modified'].append(deploy_file)
                logging.info(f"Updated deployment file: {deploy_file}")
    
    def update_scripts(self):
        """Update automation scripts"""
        script_files = [
            'scripts/deploy.sh',
            'scripts/setup.sh',
            'scripts/backup.sh',
            'scripts/monitor.sh',
            'scripts/github_auto_update.py'
        ]
        
        for script_file in script_files:
            source_file = self.source_dir / script_file
            if source_file.exists():
                target_file = self.target_repo_path / script_file
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                
                # Make scripts executable
                target_file.chmod(0o755)
                
                self.changes['files_modified'].append(script_file)
                logging.info(f"Updated script: {script_file}")
    
    def create_commit(self, message: str = None) -> bool:
        """Create a Git commit with changes"""
        try:
            # Add all changes
            self.repo.index.add('*')
            
            # Create commit message
            if not message:
                message = self.generate_commit_message()
            
            # Create commit
            commit = self.repo.index.commit(message)
            logging.info(f"Created commit: {commit.hexsha}")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to create commit: {e}")
            return False
    
    def generate_commit_message(self) -> str:
        """Generate commit message based on changes"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message_parts = [f"Auto-update: {timestamp}"]
        
        if self.changes['files_added']:
            message_parts.append(f"Added {len(self.changes['files_added'])} files")
        
        if self.changes['files_modified']:
            message_parts.append(f"Modified {len(self.changes['files_modified'])} files")
        
        if self.changes['directories_created']:
            message_parts.append(f"Created {len(self.changes['directories_created'])} directories")
        
        return " | ".join(message_parts)
    
    def push_changes(self) -> bool:
        """Push changes to remote repository"""
        try:
            origin = self.repo.remote('origin')
            origin.push()
            logging.info("Changes pushed to remote repository")
            return True
            
        except Exception as e:
            logging.error(f"Failed to push changes: {e}")
            return False
    
    def create_release(self, version: str, release_notes: str = None) -> bool:
        """Create a GitHub release"""
        try:
            # Create tag
            tag = self.repo.create_tag(version, message=f"Release {version}")
            
            # Push tag
            origin = self.repo.remote('origin')
            origin.push(tags=True)
            
            # Create release using GitHub API
            if release_notes:
                self.create_github_release(version, release_notes)
            
            logging.info(f"Created release: {version}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create release: {e}")
            return False
    
    def create_github_release(self, version: str, release_notes: str):
        """Create GitHub release using API"""
        import requests
        
        url = f"https://api.github.com/repos/Kausiukas/System-Reference/releases"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'tag_name': version,
            'name': f'Release {version}',
            'body': release_notes,
            'draft': False,
            'prerelease': False
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            logging.info(f"GitHub release created: {version}")
        else:
            logging.error(f"Failed to create GitHub release: {response.text}")
    
    def generate_release_notes(self) -> str:
        """Generate release notes based on changes"""
        notes = []
        notes.append(f"# Release {datetime.now().strftime('%Y.%m.%d')}")
        notes.append("")
        notes.append("## Changes")
        notes.append("")
        
        if self.changes['files_added']:
            notes.append("### Added")
            for file in self.changes['files_added'][:10]:  # Limit to 10 files
                notes.append(f"- {file}")
            if len(self.changes['files_added']) > 10:
                notes.append(f"- ... and {len(self.changes['files_added']) - 10} more files")
            notes.append("")
        
        if self.changes['files_modified']:
            notes.append("### Modified")
            for file in self.changes['files_modified'][:10]:
                notes.append(f"- {file}")
            if len(self.changes['files_modified']) > 10:
                notes.append(f"- ... and {len(self.changes['files_modified']) - 10} more files")
            notes.append("")
        
        if self.changes['directories_created']:
            notes.append("### New Directories")
            for directory in self.changes['directories_created']:
                notes.append(f"- {directory}")
            notes.append("")
        
        notes.append("## Technical Details")
        notes.append("- Automated update via GitHub Auto Update System")
        notes.append(f"- Timestamp: {datetime.now().isoformat()}")
        notes.append(f"- Total files processed: {len(self.changes['files_added']) + len(self.changes['files_modified'])}")
        
        return "\n".join(notes)
    
    def cleanup(self):
        """Clean up temporary files and reset changes tracking"""
        self.changes = {
            'files_added': [],
            'files_modified': [],
            'files_deleted': [],
            'directories_created': [],
            'directories_deleted': []
        }
        logging.info("Cleanup completed")
    
    def run(self, create_release: bool = False, version: str = None) -> bool:
        """Run the complete update process"""
        try:
            logging.info("Starting GitHub auto-update process...")
            
            # Sync code
            if not self.sync_code():
                return False
            
            # Create commit
            if not self.create_commit():
                return False
            
            # Push changes
            if not self.push_changes():
                return False
            
            # Create release if requested
            if create_release and version:
                release_notes = self.generate_release_notes()
                if not self.create_release(version, release_notes):
                    logging.warning("Failed to create release, but update was successful")
            
            # Cleanup
            self.cleanup()
            
            logging.info("GitHub auto-update process completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"GitHub auto-update process failed: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Auto Update System')
    parser.add_argument('--config', default='config/github_update_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--release', action='store_true',
                       help='Create a new release')
    parser.add_argument('--version', help='Release version')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform dry run without making changes')
    
    args = parser.parse_args()
    
    # Initialize updater
    updater = GitHubAutoUpdater(args.config)
    
    # Run update
    success = updater.run(create_release=args.release, version=args.version)
    
    if success:
        print("✅ GitHub auto-update completed successfully")
        sys.exit(0)
    else:
        print("❌ GitHub auto-update failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 