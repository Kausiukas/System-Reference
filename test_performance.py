import time
import json
import random
import threading
from queue import Queue
from vector_db import AutoVectorDB

DB_PATH = "D:/GUI/vectorstore"  # Use local/test DB for performance testing
NUM_QUERIES = 100
CONCURRENCY = 10
RESULTS_FILE = "performance_results.json"

# Example queries (can be replaced with real or synthetic queries)
QUERIES = [f"Test query {i}" for i in range(NUM_QUERIES)]

def run_query(db, query):
    start = time.time()
    try:
        results = db.search(query, k=5)
        latency = time.time() - start
        return {"success": True, "latency": latency, "results": results}
    except Exception as e:
        latency = time.time() - start
        return {"success": False, "latency": latency, "error": str(e)}

def worker(db, q, results):
    while not q.empty():
        query = q.get()
        res = run_query(db, query)
        results.append(res)
        q.task_done()

def run_performance_test():
    db = AutoVectorDB(db_path=DB_PATH)
    q = Queue()
    for query in QUERIES:
        q.put(query)
    results = []
    threads = []
    for _ in range(CONCURRENCY):
        t = threading.Thread(target=worker, args=(db, q, results))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    # Analyze results
    latencies = [r["latency"] for r in results if r["success"]]
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    throughput = len(results) / sum(latencies) if latencies else 0
    summary = {
        "total_queries": len(results),
        "success_count": success_count,
        "fail_count": fail_count,
        "avg_latency": avg_latency,
        "min_latency": min_latency,
        "max_latency": max_latency,
        "throughput_qps": throughput,
    }
    print("Performance Test Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    with open(RESULTS_FILE, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    print(f"Results saved to {RESULTS_FILE}")
    return summary

if __name__ == "__main__":
    run_performance_test() 