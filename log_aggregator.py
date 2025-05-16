import os
import glob
from datetime import datetime

LOG_DIR = 'logs'
AGGREGATED_LOG = os.path.join(LOG_DIR, 'aggregated.log')

# Patterns for log files to aggregate
LOG_PATTERNS = [
    '*.log',
    '*.txt',
    'events.log',
    'metrics_*.json',
    'vectorstore_health.log'
]

EXCLUDE_FILES = {'aggregated.log', 'archive'}

def aggregate_logs():
    entries = []
    for pattern in LOG_PATTERNS:
        for log_path in glob.glob(os.path.join(LOG_DIR, pattern)):
            if any(ex in log_path for ex in EXCLUDE_FILES):
                continue
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # Prepend source file and timestamp if not present
                        ts = datetime.now().isoformat()
                        entry = f"[{ts}] [{os.path.basename(log_path)}] {line.strip()}"
                        entries.append(entry)
            except Exception as e:
                print(f"Error reading {log_path}: {e}")
    # Sort entries by timestamp if possible (not enforced here)
    with open(AGGREGATED_LOG, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(entry + '\n')
    print(f"Aggregated {len(entries)} log entries into {AGGREGATED_LOG}")

if __name__ == '__main__':
    aggregate_logs() 