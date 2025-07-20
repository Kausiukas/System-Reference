#!/usr/bin/env python3
"""
Clean GitHub Repository Update System for Cloud Deployment

This script automatically updates the System-Reference GitHub repository with ONLY
the essential files needed for cloud deployment. It removes all unnecessary files
and ensures a clean, minimal repository structure.
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
        logging.FileHandler('github_auto_update_clean.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class CleanGitHubAutoUpdater:
    """Clean automatic GitHub repository update system for cloud deployment"""
    
    def __init__(self, config_path: str = "config/github_update_config_clean.yaml"):
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
            logging.info(f"Clean configuration loaded from {config_path}")
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
    
    def clean_repository(self):
        """Remove all files except essential ones"""
        logging.info("Cleaning repository - removing unnecessary files...")
        
        # Get list of essential files
        essential_files = self.config['include_patterns']
        essential_paths = []
        
        for pattern in essential_files:
            if pattern.startswith('!'):
                continue
            if '*' in pattern:
                # Handle glob patterns
                for file_path in self.source_dir.glob(pattern):
                    if file_path.is_file():
                        essential_paths.append(str(file_path.relative_to(self.source_dir)))
            else:
                # Direct file path
                file_path = self.source_dir / pattern
                if file_path.exists():
                    essential_paths.append(pattern)
        
        logging.info(f"Essential files to keep: {essential_paths}")
        
        # Remove all files in target repository except .git
        for item in self.target_repo_path.iterdir():
            if item.name == '.git':
                continue
            
            if item.is_file():
                item.unlink()
                logging.info(f"Removed file: {item.name}")
            elif item.is_dir():
                shutil.rmtree(item)
                logging.info(f"Removed directory: {item.name}")
    
    def create_clean_structure(self):
        """Create clean directory structure"""
        logging.info("Creating clean directory structure...")
        
        directories = self.config['directories']
        for directory in directories:
            dir_path = self.target_repo_path / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.changes['directories_created'].append(directory)
                logging.info(f"Created directory: {directory}")
    
    def copy_essential_files(self):
        """Copy only essential files"""
        logging.info("Copying essential files...")
        
        essential_files = self.config['include_patterns']
        
        for pattern in essential_files:
            if pattern.startswith('!'):
                continue
                
            if '*' in pattern:
                # Handle glob patterns
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
            else:
                # Direct file path
                source_file = self.source_dir / pattern
                if source_file.exists() and source_file.is_file():
                    target_file = self.target_repo_path / pattern
                    
                    # Ensure target directory exists
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(source_file, target_file)
                    
                    if target_file.exists():
                        self.changes['files_added'].append(pattern)
                        logging.info(f"Copied: {pattern}")
    
    def sync_clean_repository(self) -> bool:
        """Synchronize clean repository with only essential files"""
        logging.info("Starting clean repository synchronization...")
        
        try:
            # Clean existing repository
            self.clean_repository()
            
            # Create clean directory structure
            self.create_clean_structure()
            
            # Copy only essential files
            self.copy_essential_files()
            
            logging.info("Clean repository synchronization completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Clean repository synchronization failed: {e}")
            return False
    
    def create_commit(self, message: str = None) -> bool:
        """Create a commit with the changes"""
        try:
            if not message:
                message = self.generate_commit_message()
            
            # Add all files
            self.repo.index.add('*')
            
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
        
        if self.changes['files_added']:
            return f"Cloud deployment: Clean repository update - {timestamp}"
        else:
            return f"Cloud deployment: Repository cleanup - {timestamp}"
    
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
    
    def cleanup(self):
        """Clean up temporary files and directories"""
        try:
            # Remove temporary clone if it was created
            if self.target_repo_path.exists() and self.target_repo_path != Path('.'):
                shutil.rmtree(self.target_repo_path)
                logging.info("Cleanup completed")
        except Exception as e:
            logging.warning(f"Cleanup failed: {e}")
    
    def run(self) -> bool:
        """Run the clean repository update process"""
        logging.info("Starting clean GitHub auto-update process...")
        
        try:
            # Sync clean repository
            if not self.sync_clean_repository():
                return False
            
            # Create commit
            if not self.create_commit():
                return False
            
            # Push changes
            if not self.push_changes():
                return False
            
            logging.info("Clean GitHub auto-update process completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Clean GitHub auto-update process failed: {e}")
            return False
        finally:
            self.cleanup()

def main():
    """Main function"""
    try:
        # Initialize clean updater
        updater = CleanGitHubAutoUpdater()
        
        # Run the update process
        success = updater.run()
        
        if success:
            print("✅ Clean GitHub auto-update completed successfully")
            print(f"📁 Clean repository: {updater.target_repo_path}")
            print(f"📊 Files added: {len(updater.changes['files_added'])}")
            print(f"📁 Directories created: {len(updater.changes['directories_created'])}")
        else:
            print("❌ Clean GitHub auto-update failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 