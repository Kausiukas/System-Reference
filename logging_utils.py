import logging
import os
import json
from logging.handlers import RotatingFileHandler
import csv
from datetime import datetime

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

os.makedirs(LOG_DIR, exist_ok=True)

# Standard log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Singleton logger cache
_loggers = {}

def get_logger(name: str = 'app', level=logging.INFO):
    if name in _loggers:
        return _loggers[name]
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Prevent duplicate handlers
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(ch)
        # Rotating file handler
        fh = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(fh)
    _loggers[name] = logger
    return logger

def log_csv(filename, row, header=None):
    path = os.path.join(LOG_DIR, filename)
    write_header = not os.path.exists(path) and header is not None
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)

def log_event(event, log_file=os.path.join(LOG_DIR, 'events.log')):
    """
    Log a structured event (as dict or JSON string) to a separate events log file.
    """
    if isinstance(event, dict):
        event_str = json.dumps(event)
    else:
        event_str = str(event)
    with open(log_file, 'a') as f:
        f.write(event_str + '\n')

def log_error(error, context="", filename="errors.log"):
    path = os.path.join(LOG_DIR, filename)
    with open(path, "a") as f:
        f.write(f"{datetime.now().isoformat()} ERROR: {error} | Context: {context}\n")

# Example usage:
# logger = get_logger(__name__)
# logger.info("This is an info message.")
# logger.error("This is an error message.") 