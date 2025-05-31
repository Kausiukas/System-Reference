import os
import time
import imaplib
import email
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.header import decode_header
import schedule
import logging
from pathlib import Path
import extract_msg
from abc import ABC, abstractmethod

class EmailWatcher(ABC):
    def __init__(self, imap_server: str, email_address: str, password: str, temp_dir: Optional[str] = None):
        """Initialize email watcher."""
        self.imap_server = imap_server
        self.email_address = email_address
        self.password = password
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.running = False
        self.imap = None
        
    @abstractmethod
    def connect(self) -> bool:
        """Connect to email server."""
        pass
        
    @abstractmethod
    def disconnect(self):
        """Disconnect from email server."""
        pass
        
    def start_watching(self):
        """Start watching for new emails."""
        if not self.connect():
            logging.error("Failed to connect to email server")
            return
            
        self.running = True
        while self.running:
            try:
                self.check_new_emails()
            except Exception as e:
                logging.error(f"Error checking emails: {e}")
                break
                
        self.disconnect()
        
    def stop(self):
        """Stop watching for new emails."""
        self.running = False
        
    def check_new_emails(self):
        """Check for new emails with attachments."""
        if not self.imap:
            return
            
        try:
            self.imap.select('INBOX')
            _, message_numbers = self.imap.search(None, 'UNSEEN')
            
            for num in message_numbers[0].split():
                _, msg_data = self.imap.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)
                
                self.process_attachments(msg)
                
        except Exception as e:
            logging.error(f"Error in check_new_emails: {e}")
            
    def process_attachments(self, msg: email.message.Message):
        """Process email attachments."""
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            if part.get('Content-Disposition') is None:
                continue
                
            filename = part.get_filename()
            if not filename:
                continue
                
            # Save attachment
            filepath = Path(self.temp_dir) / filename
            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))
                
            logging.info(f"Saved attachment: {filepath}")

class GmailWatcher(EmailWatcher):
    def __init__(self, email_address: str, app_password: str, temp_dir: Optional[str] = None):
        """Initialize Gmail watcher."""
        super().__init__(
            imap_server="imap.gmail.com",
            email_address=email_address,
            password=app_password,
            temp_dir=temp_dir
        )
        
    def connect(self) -> bool:
        """Connect to Gmail server."""
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server)
            self.imap.login(self.email_address, self.password)
            return True
        except Exception as e:
            logging.error(f"Gmail connection error: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from Gmail server."""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except Exception as e:
                logging.error(f"Gmail disconnection error: {e}")

class OutlookWatcher(EmailWatcher):
    def __init__(self, email_address: str, password: str, temp_dir: Optional[str] = None):
        """Initialize Outlook watcher."""
        super().__init__(
            imap_server="outlook.office365.com",
            email_address=email_address,
            password=password,
            temp_dir=temp_dir
        )
        
    def connect(self) -> bool:
        """Connect to Outlook server."""
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server)
            self.imap.login(self.email_address, self.password)
            return True
        except Exception as e:
            logging.error(f"Outlook connection error: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from Outlook server."""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except Exception as e:
                logging.error(f"Outlook disconnection error: {e}")

    def save_attachment(self, part, email_id: str, part_num: int) -> Optional[str]:
        """Save email attachment to temporary directory."""
        try:
            filename = part.get_filename()
            if filename:
                # Create safe filename
                safe_filename = f"{email_id}_{part_num}_{filename}"
                file_path = os.path.join(self.temp_dir, safe_filename)
                
                # Save attachment
                with open(file_path, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                    
                return file_path
        except Exception as e:
            logging.error(f"Failed to save attachment: {e}")
            
        return None
        
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary files."""
        try:
            now = datetime.now()
            for file_path in Path(self.temp_dir).glob('*'):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if now - mtime > timedelta(hours=max_age_hours):
                        file_path.unlink()
        except Exception as e:
            logging.error(f"Error cleaning up temp files: {e}")
            
    def check_new_emails(self) -> List[str]:
        """Check for new emails and save attachments."""
        saved_files = []
        
        try:
            if not self.connect():
                return saved_files
                    
            # Select inbox
            self.imap.select('INBOX')
            
            # Search for unread emails
            _, message_numbers = self.imap.search(None, 'UNSEEN')
            
            for num in message_numbers[0].split():
                try:
                    # Fetch email message
                    _, msg_data = self.imap.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Process attachments
                    for i, part in enumerate(email_message.walk(), 1):
                        if part.get_content_maintype() != 'multipart':
                            file_path = self.save_attachment(part, num.decode(), i)
                            if file_path:
                                saved_files.append(file_path)
                                
                except Exception as e:
                    logging.error(f"Error processing email {num}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error checking emails: {e}")
            
        return saved_files
        
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary files."""
        try:
            now = datetime.now()
            for file_path in Path(self.temp_dir).glob('*'):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if now - mtime > timedelta(hours=max_age_hours):
                        file_path.unlink()
        except Exception as e:
            logging.error(f"Error cleaning up temp files: {e}")
            
    def start_watching(self):
        """Start watching for new emails."""
        self.running = True
        
        # Schedule regular checks
        schedule.every(5).minutes.do(self.check_new_emails)
        schedule.every(1).day.do(self.cleanup_temp_files)
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
            
    def stop(self):
        """Stop watching for emails."""
        self.running = False
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass 