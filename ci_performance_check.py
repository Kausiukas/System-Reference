import json
import sys
import os

# Configurable thresholds (can be set via env vars)
MAX_LATENCY = float(os.getenv('CI_MAX_LATENCY', '1.0'))  # seconds
MIN_THROUGHPUT = float(os.getenv('CI_MIN_THROUGHPUT', '10'))  # queries/sec
MAX_MEMORY_MB = float(os.getenv('CI_MAX_MEMORY_MB', '1024'))  # MB

PERF_RESULTS = 'performance_results.json'

# Run the performance test script
def run_performance_tests():
    import subprocess
    print("Running performance tests...")
    result = subprocess.run([sys.executable, 'test_performance.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Performance test script failed.")
        sys.exit(1)

def check_performance_results():
    if not os.path.exists(PERF_RESULTS):
        print(f"{PERF_RESULTS} not found.")
        sys.exit(1)
    with open(PERF_RESULTS, 'r') as f:
        data = json.load(f)
    # Example expected keys: avg_latency, throughput, peak_memory_mb
    avg_latency = data.get('avg_latency', None)
    throughput = data.get('throughput', None)
    peak_memory = data.get('peak_memory_mb', None)
    failed = False
    if avg_latency is not None and avg_latency > MAX_LATENCY:
        print(f"FAIL: Average latency {avg_latency:.3f}s exceeds max {MAX_LATENCY:.3f}s")
        failed = True
    if throughput is not None and throughput < MIN_THROUGHPUT:
        print(f"FAIL: Throughput {throughput:.2f}/s below min {MIN_THROUGHPUT:.2f}/s")
        failed = True
    if peak_memory is not None and peak_memory > MAX_MEMORY_MB:
        print(f"FAIL: Peak memory {peak_memory:.1f}MB exceeds max {MAX_MEMORY_MB:.1f}MB")
        failed = True
    if not failed:
        print("Performance/resource checks PASSED.")
        sys.exit(0)
    else:
        print("Performance/resource checks FAILED.")
        sys.exit(1)

if __name__ == '__main__':
    run_performance_tests()
    check_performance_results() 