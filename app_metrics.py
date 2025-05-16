import csv
import os
from datetime import datetime

APP_METRICS_LOG = 'app_metrics_log.csv'

# Initialize counters
metrics = {
    'queries': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'errors': 0
}

def log_app_metrics():
    timestamp = datetime.now().isoformat()
    file_exists = os.path.isfile(APP_METRICS_LOG)
    with open(APP_METRICS_LOG, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['timestamp', 'queries', 'cache_hits', 'cache_misses', 'errors'])
        writer.writerow([timestamp, metrics['queries'], metrics['cache_hits'], metrics['cache_misses'], metrics['errors']])

def increment_queries():
    metrics['queries'] += 1

def increment_cache_hits():
    metrics['cache_hits'] += 1

def increment_cache_misses():
    metrics['cache_misses'] += 1

def increment_errors():
    metrics['errors'] += 1

if __name__ == "__main__":
    increment_queries()
    increment_cache_hits()
    increment_cache_misses()
    increment_errors()
    log_app_metrics() 