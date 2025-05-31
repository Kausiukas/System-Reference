import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
import signal
import platform

# Only import daemon on Unix-like systems
if platform.system() != 'Windows':
    import daemon
import lockfile
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.components.email_watcher import GmailWatcher, OutlookWatcher
from src.components.nodes import build_graph
from src.components.state import ClientState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailWatcherService:
    def __init__(self):
        """Initialize the email watcher service."""
        # Load environment variables
        load_dotenv()
        
        # Create necessary directories
        os.makedirs('data/temp_emails', exist_ok=True)
        
        # Initialize watchers list
        self.watchers = []
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
    def add_gmail_watcher(self, email: str, app_password: str):
        """Add a Gmail watcher."""
        watcher = GmailWatcher(
            email_address=email,
            app_password=app_password,
            temp_dir='data/temp_emails'
        )
        self.watchers.append(watcher)
        
    def add_outlook_watcher(self, email: str, password: str):
        """Add an Outlook watcher."""
        watcher = OutlookWatcher(
            email_address=email,
            password=password,
            temp_dir='data/temp_emails'
        )
        self.watchers.append(watcher)
        
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        self.running = False
        for watcher in self.watchers:
            watcher.stop()
            
    def process_files(self, files: list[str]):
        """Process a list of files."""
        workflow = build_graph()
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                # Create initial state
                initial_state = ClientState(
                    raw_content=content,
                    client_id=None,  # This would be set based on your logic
                    messages=[],
                    attachments=[],
                    metadata={}
                )
                # Run the workflow
                workflow.invoke(initial_state)
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
            finally:
                # Clean up the file
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error removing file {file_path}: {e}")
            
    def run(self):
        """Run the service."""
        try:
            # Start all watchers
            for watcher in self.watchers:
                watcher.start_watching()
                
            # Keep running until shutdown
            while self.running:
                pass
                
        except Exception as e:
            logging.error(f"Service error: {e}")
            self.running = False
            
        finally:
            # Clean up
            for watcher in self.watchers:
                watcher.stop()

def run_service(pid_file=None, work_dir=None):
    """Run the service, optionally as a daemon on Unix-like systems."""
    if platform.system() != 'Windows' and pid_file and work_dir:
        # Run as daemon on Unix-like systems
        with daemon.DaemonContext(
            pidfile=pid_file,
            working_directory=work_dir,
        ):
            service = EmailWatcherService()
            service.run()
    else:
        # Run normally on Windows or without daemon context
        service = EmailWatcherService()
        service.run()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Email Watcher Service')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (Unix-like systems only)')
    args = parser.parse_args()
    
    if args.daemon and platform.system() != 'Windows':
        # Run as daemon
        pid_file = "email_watcher.pid"
        work_dir = os.getcwd()
        run_service(pid_file, work_dir)
    else:
        # Run normally
        run_service()

if __name__ == '__main__':
    main() 