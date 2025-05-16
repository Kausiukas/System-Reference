import time
import json
import logging
import psutil
import threading
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurable parameters
NUM_REQUESTS = 1000
CONCURRENCY = 10
TIMEOUT = 5  # seconds

def simulate_request() -> Dict[str, Any]:
    """Simulate a single request (e.g., query, computation)."""
    start_time = time.time()
    # Simulate work (e.g., sleep, computation)
    time.sleep(0.1)
    end_time = time.time()
    return {
        'start_time': start_time,
        'end_time': end_time,
        'duration': end_time - start_time,
        'success': True
    }

def stress_test() -> Dict[str, Any]:
    """Run stress test with concurrent requests."""
    results = []
    errors = []
    timeouts = []
    start_time = time.time()
    threads = []
    for _ in range(NUM_REQUESTS):
        thread = threading.Thread(target=lambda: results.append(simulate_request()))
        threads.append(thread)
        thread.start()
        if len(threads) >= CONCURRENCY:
            for t in threads:
                t.join()
            threads = []
    for t in threads:
        t.join()
    end_time = time.time()
    # Log resource usage
    memory_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(interval=1)
    return {
        'total_requests': NUM_REQUESTS,
        'concurrency': CONCURRENCY,
        'start_time': start_time,
        'end_time': end_time,
        'duration': end_time - start_time,
        'results': results,
        'errors': errors,
        'timeouts': timeouts,
        'memory_percent': memory_percent,
        'cpu_percent': cpu_percent
    }

if __name__ == '__main__':
    logger.info("Starting stress test...")
    results = stress_test()
    with open('stress_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    logger.info("Stress test completed. Results saved to stress_test_results.json.") 