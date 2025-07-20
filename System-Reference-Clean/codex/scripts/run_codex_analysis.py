#!/usr/bin/env python3
"""
Codex Analysis Automation Script

This script automates the execution of OpenAI Codex analysis on the System-Reference repository.
It handles the complete analysis workflow from setup to output generation.
"""

import os
import sys
import json
import yaml
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import git
from git import Repo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codex_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class CodexAnalysisRunner:
    """Automated Codex analysis runner for System-Reference repository"""
    
    def __init__(self, config_path: str = "codex/config/codex_config.yaml"):
        self.config = self.load_config(config_path)
        self.working_dir = Path(self.config['analysis']['repository']['working_directory'])
        self.repo_url = self.config['analysis']['repository']['url']
        self.branch = self.config['analysis']['repository']['branch']
        
        # Initialize repository
        self.repo = self.initialize_repository()
        
        # Track analysis progress
        self.progress = {
            'started_at': datetime.now().isoformat(),
            'completed_phases': [],
            'current_phase': None,
            'errors': [],
            'warnings': []
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
        """Initialize or clone the repository"""
        if self.working_dir.exists():
            try:
                repo = Repo(self.working_dir)
                logging.info(f"Using existing repository at {self.working_dir}")
                return repo
            except git.InvalidGitRepositoryError:
                logging.error(f"Invalid Git repository at {self.working_dir}")
                sys.exit(1)
        else:
            logging.info(f"Cloning repository from {self.repo_url}")
            return Repo.clone_from(
                self.repo_url,
                self.working_dir,
                branch=self.branch
            )
    
    def setup_environment(self):
        """Setup analysis environment"""
        logging.info("Setting up analysis environment...")
        
        # Install dependencies
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, cwd=self.working_dir)
            logging.info("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install dependencies: {e}")
            self.progress['errors'].append(f"Dependency installation failed: {e}")
        
        # Install analysis tools
        tools = self.config['analysis']['tools']
        for category, tool_list in tools.items():
            for tool in tool_list:
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", tool], 
                                 check=True, cwd=self.working_dir)
                    logging.info(f"Installed analysis tool: {tool}")
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Failed to install tool {tool}: {e}")
                    self.progress['warnings'].append(f"Tool installation failed: {tool}")
        
        self.progress['completed_phases'].append('environment_setup')
    
    def run_code_quality_analysis(self):
        """Run code quality analysis"""
        logging.info("Running code quality analysis...")
        self.progress['current_phase'] = 'code_quality_analysis'
        
        results = {
            'pylint': self.run_pylint_analysis(),
            'flake8': self.run_flake8_analysis(),
            'mypy': self.run_mypy_analysis(),
            'radon': self.run_radon_analysis(),
            'bandit': self.run_bandit_analysis()
        }
        
        # Generate report
        self.generate_code_quality_report(results)
        self.progress['completed_phases'].append('code_quality_analysis')
    
    def run_pylint_analysis(self) -> Dict:
        """Run pylint analysis"""
        try:
            result = subprocess.run(
                ['pylint', 'src/', '--output-format=json'],
                capture_output=True, text=True, cwd=self.working_dir
            )
            return {
                'success': result.returncode == 0,
                'output': json.loads(result.stdout) if result.stdout else [],
                'errors': result.stderr if result.stderr else None
            }
        except Exception as e:
            logging.error(f"Pylint analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_flake8_analysis(self) -> Dict:
        """Run flake8 analysis"""
        try:
            result = subprocess.run(
                ['flake8', 'src/', '--format=json'],
                capture_output=True, text=True, cwd=self.working_dir
            )
            return {
                'success': result.returncode == 0,
                'output': json.loads(result.stdout) if result.stdout else [],
                'errors': result.stderr if result.stderr else None
            }
        except Exception as e:
            logging.error(f"Flake8 analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_mypy_analysis(self) -> Dict:
        """Run mypy analysis"""
        try:
            result = subprocess.run(
                ['mypy', 'src/'],
                capture_output=True, text=True, cwd=self.working_dir
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr if result.stderr else None
            }
        except Exception as e:
            logging.error(f"MyPy analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_radon_analysis(self) -> Dict:
        """Run radon analysis"""
        try:
            result = subprocess.run(
                ['radon', 'cc', 'src/', '-j'],
                capture_output=True, text=True, cwd=self.working_dir
            )
            return {
                'success': result.returncode == 0,
                'output': json.loads(result.stdout) if result.stdout else {},
                'errors': result.stderr if result.stderr else None
            }
        except Exception as e:
            logging.error(f"Radon analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_bandit_analysis(self) -> Dict:
        """Run bandit security analysis"""
        try:
            result = subprocess.run(
                ['bandit', '-r', 'src/', '-f', 'json'],
                capture_output=True, text=True, cwd=self.working_dir
            )
            return {
                'success': result.returncode == 0,
                'output': json.loads(result.stdout) if result.stdout else {'results': []},
                'errors': result.stderr if result.stderr else None
            }
        except Exception as e:
            logging.error(f"Bandit analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_code_quality_report(self, results: Dict):
        """Generate code quality analysis report"""
        report_path = Path("codex/outputs/analysis_reports")
        report_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = report_path / f"code_quality_analysis_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Code Quality Analysis Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n")
            f.write(f"**Repository**: {self.repo_url}\n")
            f.write(f"**Branch**: {self.branch}\n\n")
            
            # Summary
            f.write("## Executive Summary\n\n")
            total_issues = 0
            for tool, result in results.items():
                if result.get('success'):
                    if tool == 'pylint':
                        total_issues += len(result.get('output', []))
                    elif tool == 'flake8':
                        total_issues += len(result.get('output', []))
                    elif tool == 'bandit':
                        total_issues += len(result.get('output', {}).get('results', []))
            
            f.write(f"Total issues found: {total_issues}\n\n")
            
            # Detailed results
            f.write("## Detailed Analysis\n\n")
            for tool, result in results.items():
                f.write(f"### {tool.upper()}\n\n")
                if result.get('success'):
                    f.write("✅ Analysis completed successfully\n\n")
                    if result.get('output'):
                        f.write("**Issues Found:**\n\n")
                        if isinstance(result['output'], list):
                            for issue in result['output'][:10]:  # Show first 10 issues
                                f.write(f"- {issue}\n")
                        elif isinstance(result['output'], dict):
                            f.write(f"- {len(result['output'])} items analyzed\n")
                else:
                    f.write("❌ Analysis failed\n\n")
                    if result.get('error'):
                        f.write(f"**Error**: {result['error']}\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            if total_issues > 0:
                f.write("1. **Address Critical Issues**: Prioritize fixing high-severity issues\n")
                f.write("2. **Improve Code Style**: Follow PEP 8 guidelines consistently\n")
                f.write("3. **Enhance Type Safety**: Add type hints where missing\n")
                f.write("4. **Security Review**: Address security vulnerabilities\n")
                f.write("5. **Documentation**: Improve code documentation and comments\n")
            else:
                f.write("✅ No significant issues found. Code quality is good.\n")
        
        logging.info(f"Code quality report generated: {report_file}")
    
    def run_security_analysis(self):
        """Run security analysis"""
        logging.info("Running security analysis...")
        self.progress['current_phase'] = 'security_analysis'
        
        # Run security tools
        results = {
            'bandit': self.run_bandit_analysis(),
            'safety': self.run_safety_check()
        }
        
        # Generate security report
        self.generate_security_report(results)
        self.progress['completed_phases'].append('security_analysis')
    
    def run_safety_check(self) -> Dict:
        """Run safety dependency check"""
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True, text=True, cwd=self.working_dir
            )
            return {
                'success': result.returncode == 0,
                'output': json.loads(result.stdout) if result.stdout else [],
                'errors': result.stderr if result.stderr else None
            }
        except Exception as e:
            logging.error(f"Safety check failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_security_report(self, results: Dict):
        """Generate security analysis report"""
        report_path = Path("codex/outputs/security_findings")
        report_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = report_path / f"security_analysis_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Security Analysis Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n")
            f.write(f"**Repository**: {self.repo_url}\n")
            f.write(f"**Branch**: {self.branch}\n\n")
            
            # Summary
            f.write("## Executive Summary\n\n")
            total_vulnerabilities = 0
            for tool, result in results.items():
                if result.get('success'):
                    if tool == 'bandit':
                        total_vulnerabilities += len(result.get('output', {}).get('results', []))
                    elif tool == 'safety':
                        total_vulnerabilities += len(result.get('output', []))
            
            f.write(f"Total vulnerabilities found: {total_vulnerabilities}\n\n")
            
            # Detailed results
            f.write("## Detailed Findings\n\n")
            for tool, result in results.items():
                f.write(f"### {tool.upper()}\n\n")
                if result.get('success'):
                    f.write("✅ Analysis completed successfully\n\n")
                    if result.get('output'):
                        f.write("**Vulnerabilities Found:**\n\n")
                        if isinstance(result['output'], list):
                            for vuln in result['output'][:10]:  # Show first 10
                                f.write(f"- {vuln}\n")
                        elif isinstance(result['output'], dict):
                            for vuln in result['output'].get('results', [])[:10]:
                                f.write(f"- {vuln}\n")
                else:
                    f.write("❌ Analysis failed\n\n")
                    if result.get('error'):
                        f.write(f"**Error**: {result['error']}\n\n")
            
            # Recommendations
            f.write("## Security Recommendations\n\n")
            if total_vulnerabilities > 0:
                f.write("1. **Immediate Action**: Address critical security vulnerabilities\n")
                f.write("2. **Dependency Updates**: Update vulnerable dependencies\n")
                f.write("3. **Code Review**: Review code for security best practices\n")
                f.write("4. **Security Testing**: Implement automated security testing\n")
                f.write("5. **Monitoring**: Set up security monitoring and alerting\n")
            else:
                f.write("✅ No security vulnerabilities found.\n")
        
        logging.info(f"Security report generated: {report_file}")
    
    def run_performance_analysis(self):
        """Run performance analysis"""
        logging.info("Running performance analysis...")
        self.progress['current_phase'] = 'performance_analysis'
        
        # Basic performance metrics
        results = self.analyze_performance()
        
        # Generate performance report
        self.generate_performance_report(results)
        self.progress['completed_phases'].append('performance_analysis')
    
    def analyze_performance(self) -> Dict:
        """Analyze basic performance metrics"""
        results = {
            'file_count': 0,
            'total_lines': 0,
            'average_file_size': 0,
            'largest_files': []
        }
        
        try:
            # Count Python files and lines
            python_files = list(self.working_dir.rglob("*.py"))
            results['file_count'] = len(python_files)
            
            total_lines = 0
            file_sizes = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        line_count = len(lines)
                        total_lines += line_count
                        file_sizes.append((file_path.name, line_count))
                except Exception as e:
                    logging.warning(f"Could not read {file_path}: {e}")
            
            results['total_lines'] = total_lines
            if python_files:
                results['average_file_size'] = total_lines / len(python_files)
            
            # Find largest files
            file_sizes.sort(key=lambda x: x[1], reverse=True)
            results['largest_files'] = file_sizes[:10]
            
        except Exception as e:
            logging.error(f"Performance analysis failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def generate_performance_report(self, results: Dict):
        """Generate performance analysis report"""
        report_path = Path("codex/outputs/performance_reports")
        report_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = report_path / f"performance_analysis_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Performance Analysis Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n")
            f.write(f"**Repository**: {self.repo_url}\n")
            f.write(f"**Branch**: {self.branch}\n\n")
            
            # Summary
            f.write("## Executive Summary\n\n")
            f.write(f"**Total Python Files**: {results['file_count']}\n")
            f.write(f"**Total Lines of Code**: {results['total_lines']:,}\n")
            f.write(f"**Average File Size**: {results['average_file_size']:.1f} lines\n\n")
            
            # Detailed analysis
            f.write("## Detailed Analysis\n\n")
            
            f.write("### File Size Distribution\n\n")
            f.write("**Largest Files:**\n\n")
            for filename, line_count in results['largest_files']:
                f.write(f"- {filename}: {line_count:,} lines\n")
            
            # Recommendations
            f.write("\n## Performance Recommendations\n\n")
            f.write("1. **Code Organization**: Consider breaking down large files\n")
            f.write("2. **Modularity**: Improve code modularity and reusability\n")
            f.write("3. **Optimization**: Identify and optimize performance bottlenecks\n")
            f.write("4. **Caching**: Implement appropriate caching strategies\n")
            f.write("5. **Monitoring**: Set up performance monitoring and metrics\n")
        
        logging.info(f"Performance report generated: {report_file}")
    
    def generate_final_report(self):
        """Generate final analysis summary"""
        logging.info("Generating final analysis report...")
        
        report_path = Path("codex/outputs/analysis_reports")
        report_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_file = report_path / f"final_analysis_summary_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Codex Analysis Final Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n")
            f.write(f"**Repository**: {self.repo_url}\n")
            f.write(f"**Branch**: {self.branch}\n\n")
            
            # Progress summary
            f.write("## Analysis Progress\n\n")
            f.write(f"**Started**: {self.progress['started_at']}\n")
            f.write(f"**Completed Phases**: {', '.join(self.progress['completed_phases'])}\n\n")
            
            # Errors and warnings
            if self.progress['errors']:
                f.write("## Errors Encountered\n\n")
                for error in self.progress['errors']:
                    f.write(f"- {error}\n")
                f.write("\n")
            
            if self.progress['warnings']:
                f.write("## Warnings\n\n")
                for warning in self.progress['warnings']:
                    f.write(f"- {warning}\n")
                f.write("\n")
            
            # Next steps
            f.write("## Next Steps\n\n")
            f.write("1. **Review Reports**: Examine generated analysis reports\n")
            f.write("2. **Prioritize Issues**: Identify high-priority improvements\n")
            f.write("3. **Create Implementation Plan**: Develop action plan\n")
            f.write("4. **Integrate with Shared State**: Update shared state management\n")
            f.write("5. **Execute Improvements**: Implement recommended changes\n")
        
        logging.info(f"Final report generated: {report_file}")
    
    def run(self):
        """Run complete analysis workflow"""
        logging.info("Starting Codex analysis workflow...")
        
        try:
            # Setup environment
            self.setup_environment()
            
            # Run analyses
            self.run_code_quality_analysis()
            self.run_security_analysis()
            self.run_performance_analysis()
            
            # Generate final report
            self.generate_final_report()
            
            logging.info("Codex analysis workflow completed successfully!")
            
        except Exception as e:
            logging.error(f"Analysis workflow failed: {e}")
            self.progress['errors'].append(f"Workflow failure: {e}")
            raise

def main():
    """Main entry point"""
    runner = CodexAnalysisRunner()
    runner.run()

if __name__ == "__main__":
    main() 