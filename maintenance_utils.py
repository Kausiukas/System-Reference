from logging_utils import get_logger, log_event
from metrics_tracker import get_metrics_tracker
from vector_db import AnnoyVectorDB, ChromaVectorDB
from pathlib import Path
import time
import gc
import json
from collections import Counter
import shutil
from datetime import datetime, timedelta
import gzip
import os
import psutil
import subprocess
import sys
import pandas as pd
import requests

logger = get_logger(__name__)

def defragment_index():
    """Defragment vector store/index to optimize performance and memory usage."""
    logger.info("Starting vector store/index defragmentation")
    metrics = get_metrics_tracker()
    start_time = time.time()
    
    try:
        # Track memory before defragmentation
        memory_before = metrics.track_memory_usage()
        
        # Handle Annoy cache index
        cache_path = Path("D:/DATA/cache")
        if cache_path.exists():
            logger.info("Defragmenting Annoy cache index")
            cache_db = AnnoyVectorDB(str(cache_path))
            # Rebuild Annoy index with optimal parameters
            cache_db.index.build(n_trees=10)  # Adjust n_trees based on cache size
            cache_db._save_db()
            logger.info("Annoy cache index defragmentation complete")
        
        # Handle ChromaDB full index
        full_db_path = Path("D:/DATA/vectorstore")
        if full_db_path.exists():
            logger.info("Defragmenting ChromaDB full index")
            full_db = ChromaVectorDB(str(full_db_path))
            # ChromaDB's HNSW index can be rebuilt using the CLI command
            # For now, we'll just trigger a collection rebuild
            full_db.collection.rebuild()
            logger.info("ChromaDB full index defragmentation complete")
        
        # Force garbage collection
        gc.collect()
        
        # Track memory after defragmentation
        memory_after = metrics.track_memory_usage()
        memory_saved = memory_before - memory_after
        
        # Log results
        duration = time.time() - start_time
        logger.info(f"Defragmentation completed in {duration:.2f} seconds")
        logger.info(f"Memory saved: {memory_saved:.2f} MB")
        
        # Track the maintenance action
        metrics.log_node_execution(
            node_name="defragment_index",
            start_time=start_time,
            end_time=time.time(),
            status="success",
            error=None
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error during defragmentation: {str(e)}")
        metrics.log_node_execution(
            node_name="defragment_index",
            start_time=start_time,
            end_time=time.time(),
            status="error",
            error=str(e)
        )
        return False

def rebuild_cache():
    """Rebuild the Annoy cache index with the most frequently accessed documents."""
    logger.info("Starting cache rebuild")
    metrics = get_metrics_tracker()
    start_time = time.time()
    
    try:
        # Track memory before rebuild
        memory_before = metrics.track_memory_usage()
        
        # Get cache hit statistics from metrics
        cache_events = metrics.metrics_history.get('cache_events', [])
        if not cache_events:
            logger.warning("No cache events found in metrics history")
            return False
        
        # Count document access frequency
        doc_access = Counter()
        for event in cache_events:
            if event.get('hit'):
                doc_id = event.get('document_id')
                if doc_id:
                    doc_access[doc_id] += 1
        
        # Get top accessed documents
        top_docs = doc_access.most_common(1000)  # Cache size limit
        if not top_docs:
            logger.warning("No frequently accessed documents found")
            return False
        
        # Initialize vector databases
        cache_path = Path("D:/DATA/cache")
        full_db_path = Path("D:/DATA/vectorstore")
        
        if not full_db_path.exists():
            logger.error("Full vector store not found")
            return False
        
        # Get documents from full store
        full_db = ChromaVectorDB(str(full_db_path))
        cache_db = AnnoyVectorDB(str(cache_path))
        
        # Clear existing cache
        cache_db.index = AnnoyIndex(cache_db.dimension, 'angular')
        cache_db.documents = []
        
        # Add top accessed documents to cache
        for doc_id, _ in top_docs:
            try:
                # Get document from full store
                result = full_db.collection.get(ids=[doc_id])
                if result and result['documents']:
                    # Add to cache
                    cache_db.add_documents(
                        texts=result['documents'],
                        metadata=result['metadatas']
                    )
            except Exception as e:
                logger.error(f"Error adding document {doc_id} to cache: {str(e)}")
                continue
        
        # Build and save cache
        cache_db.index.build(n_trees=10)
        cache_db._save_db()
        
        # Force garbage collection
        gc.collect()
        
        # Track memory after rebuild
        memory_after = metrics.track_memory_usage()
        memory_used = memory_after - memory_before
        
        # Log results
        duration = time.time() - start_time
        logger.info(f"Cache rebuild completed in {duration:.2f} seconds")
        logger.info(f"Memory used: {memory_used:.2f} MB")
        logger.info(f"Documents in cache: {len(cache_db.documents)}")
        
        # Track the maintenance action
        metrics.log_node_execution(
            node_name="rebuild_cache",
            start_time=start_time,
            end_time=time.time(),
            status="success",
            error=None
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error during cache rebuild: {str(e)}")
        metrics.log_node_execution(
            node_name="rebuild_cache",
            start_time=start_time,
            end_time=time.time(),
            status="error",
            error=str(e)
        )
        return False

def rotate_logs():
    """Rotate and archive log files to prevent them from growing too large."""
    logger.info("Starting log rotation")
    metrics = get_metrics_tracker()
    start_time = time.time()
    
    try:
        # Track disk usage before rotation
        disk_before = shutil.disk_usage("D:/").used
        
        # Define log directories and patterns
        log_dirs = [
            Path("logs"),
            Path("D:/DATA/logs"),
            Path("D:/GUI/logs")
        ]
        
        # Define log file patterns
        log_patterns = [
            "*.log",
            "*.txt",
            "metrics_*.json",
            "vectorstore_health.log"
        ]
        
        # Maximum log file size (10MB)
        max_size = 10 * 1024 * 1024
        
        # Maximum age for archived logs (30 days)
        max_age = timedelta(days=30)
        
        # Process each log directory
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
                
            # Create archive directory
            archive_dir = log_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # Process each log pattern
            for pattern in log_patterns:
                for log_file in log_dir.glob(pattern):
                    try:
                        # Skip if file is too small
                        if log_file.stat().st_size < max_size:
                            continue
                            
                        # Create archive filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        archive_name = f"{log_file.stem}_{timestamp}{log_file.suffix}.gz"
                        archive_path = archive_dir / archive_name
                        
                        # Compress and archive the log file
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(archive_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Clear the original log file
                        with open(log_file, 'w') as f:
                            f.write(f"Log rotated at {timestamp}\n")
                        
                        logger.info(f"Rotated log file: {log_file.name}")
                        
                    except Exception as e:
                        logger.error(f"Error rotating log file {log_file}: {str(e)}")
                        continue
            
            # Clean up old archives
            try:
                for archive in archive_dir.glob("*.gz"):
                    if datetime.now() - datetime.fromtimestamp(archive.stat().st_mtime) > max_age:
                        archive.unlink()
                        logger.info(f"Removed old archive: {archive.name}")
            except Exception as e:
                logger.error(f"Error cleaning up archives: {str(e)}")
        
        # Track disk usage after rotation
        disk_after = shutil.disk_usage("D:/").used
        space_saved = disk_before - disk_after
        
        # Log results
        duration = time.time() - start_time
        logger.info(f"Log rotation completed in {duration:.2f} seconds")
        logger.info(f"Disk space saved: {space_saved / (1024*1024):.2f} MB")
        
        # Track the maintenance action
        metrics.log_node_execution(
            node_name="rotate_logs",
            start_time=start_time,
            end_time=time.time(),
            status="success",
            error=None
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error during log rotation: {str(e)}")
        metrics.log_node_execution(
            node_name="rotate_logs",
            start_time=start_time,
            end_time=time.time(),
            status="error",
            error=str(e)
        )
        return False

def auto_restart_if_needed():
    """Comprehensive self-healing: check health, try staged recovery, restart if needed, escalate if all else fails."""
    logger.info("Checking if auto-restart/self-healing is needed")
    metrics = get_metrics_tracker()
    start_time = time.time()
    try:
        # 1. Health check (example: ping local health endpoint)
        health_ok = True
        try:
            resp = requests.get("http://localhost:8000/health", timeout=5)
            if resp.status_code != 200:
                health_ok = False
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            health_ok = False
        
        # 2. Resource usage check
        process = psutil.Process()
        memory_percent = process.memory_percent()
        cpu_percent = process.cpu_percent(interval=1)
        system_memory = psutil.virtual_memory()
        system_memory_percent = system_memory.percent
        MEMORY_THRESHOLD = 80.0
        CPU_THRESHOLD = 90.0
        SYSTEM_MEMORY_THRESHOLD = 90.0
        resource_ok = (
            memory_percent <= MEMORY_THRESHOLD and
            cpu_percent <= CPU_THRESHOLD and
            system_memory_percent <= SYSTEM_MEMORY_THRESHOLD
        )
        
        # 3. If healthy and resources OK, nothing to do
        if health_ok and resource_ok:
            logger.info("Service healthy and resources within limits. No action needed.")
            metrics.log_node_execution(
                node_name="auto_restart",
                start_time=start_time,
                end_time=time.time(),
                status="no_restart_needed",
                error=None
            )
            return False
        
        # 4. Try soft recovery (reload config, clear cache, manual GC)
        logger.warning("Attempting soft recovery...")
        try:
            # Example: reload config, clear cache, run GC
            from gc_utils import manual_gc_and_log
            manual_gc_and_log()
            # Add more soft recovery steps as needed
            logger.info("Soft recovery attempted.")
        except Exception as e:
            logger.error(f"Soft recovery failed: {str(e)}")
        
        # Re-check health after soft recovery
        health_ok_after = True
        try:
            resp = requests.get("http://localhost:8000/health", timeout=5)
            if resp.status_code != 200:
                health_ok_after = False
        except Exception as e:
            health_ok_after = False
        process = psutil.Process()
        memory_percent = process.memory_percent()
        cpu_percent = process.cpu_percent(interval=1)
        system_memory = psutil.virtual_memory()
        system_memory_percent = system_memory.percent
        resource_ok_after = (
            memory_percent <= MEMORY_THRESHOLD and
            cpu_percent <= CPU_THRESHOLD and
            system_memory_percent <= SYSTEM_MEMORY_THRESHOLD
        )
        if health_ok_after and resource_ok_after:
            logger.info("Soft recovery successful. No restart needed.")
            metrics.log_node_execution(
                node_name="auto_restart",
                start_time=start_time,
                end_time=time.time(),
                status="soft_recovery_success",
                error=None
            )
            return False
        
        # 5. Hard restart (process restart)
        logger.error("Soft recovery failed. Performing hard restart...")
        metrics.log_node_execution(
            node_name="auto_restart",
            start_time=start_time,
            end_time=time.time(),
            status="hard_restart_triggered",
            error=None
        )
        script_path = sys.argv[0]
        logger.info(f"Restarting service: {script_path}")
        subprocess.Popen([sys.executable, script_path] + sys.argv[1:])
        # Escalate/alert if restart fails (should not reach here)
        from alerting import get_alert_manager
        get_alert_manager().alert_critical_error(
            error_message="Hard restart triggered by self-healing logic",
            context=f"Health: {health_ok}, Resource OK: {resource_ok}",
            stack_trace=None
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during auto-restart/self-healing: {str(e)}")
        metrics.log_node_execution(
            node_name="auto_restart",
            start_time=start_time,
            end_time=time.time(),
            status="error",
            error=str(e)
        )
        from alerting import get_alert_manager
        get_alert_manager().alert_critical_error(
            error_message="Self-healing failed with exception",
            context=str(e),
            stack_trace=None
        )
        return False

def run_stress_test(num_requests=100, concurrency=10, target='vectorstore'):
    """Simulate high load and log results for stress testing."""
    import threading
    import random
    from queue import Queue
    logger.info(f"Running stress test: {num_requests} requests, concurrency={concurrency}, target={target}")
    metrics = get_metrics_tracker()
    start_time = time.time()
    
    results = []
    errors = []
    latencies = []
    success_count = 0
    failure_count = 0
    resource_snapshots = []
    
    def stress_worker(q):
        nonlocal success_count, failure_count
        while not q.empty():
            idx = q.get()
            req_start = time.time()
            try:
                # Simulate a query to the vector store or LLM
                if target == 'vectorstore':
                    # Use AnnoyVectorDB or ChromaVectorDB for a random query
                    db_path = Path("D:/DATA/vectorstore")
                    if db_path.exists():
                        db = ChromaVectorDB(str(db_path))
                        # Randomly select a document id or perform a search
                        ids = db.collection.get()['ids']
                        if ids:
                            doc_id = random.choice(ids)
                            db.collection.get(ids=[doc_id])
                    else:
                        raise RuntimeError("Vectorstore not found")
                elif target == 'llm':
                    # Simulate an LLM call (mocked for now)
                    time.sleep(random.uniform(0.05, 0.2))
                else:
                    raise ValueError(f"Unknown target: {target}")
                req_latency = time.time() - req_start
                latencies.append(req_latency)
                success_count += 1
                results.append({'status': 'success', 'latency': req_latency})
            except Exception as e:
                req_latency = time.time() - req_start
                latencies.append(req_latency)
                failure_count += 1
                errors.append(str(e))
                results.append({'status': 'error', 'latency': req_latency, 'error': str(e)})
            finally:
                # Track resource usage snapshot
                process = psutil.Process()
                resource_snapshots.append({
                    'memory_percent': process.memory_percent(),
                    'cpu_percent': process.cpu_percent(interval=None),
                    'timestamp': time.time()
                })
                q.task_done()
    
    q = Queue()
    for i in range(num_requests):
        q.put(i)
    
    threads = []
    for _ in range(concurrency):
        t = threading.Thread(target=stress_worker, args=(q,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    duration = time.time() - start_time
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    
    logger.info(f"Stress test completed: {success_count} successes, {failure_count} failures, duration={duration:.2f}s")
    logger.info(f"Latency: avg={avg_latency:.3f}s, min={min_latency:.3f}s, max={max_latency:.3f}s")
    if errors:
        logger.warning(f"Errors during stress test: {errors[:5]}{'...' if len(errors) > 5 else ''}")
    
    # Log to metrics
    metrics.log_node_execution(
        node_name="run_stress_test",
        start_time=start_time,
        end_time=time.time(),
        status="success" if failure_count == 0 else "partial_failure",
        error=None if not errors else str(errors[:3])
    )
    # Log event to unified logging
    log_event(json.dumps({
        'event': 'stress_test',
        'target': target,
        'num_requests': num_requests,
        'concurrency': concurrency,
        'success_count': success_count,
        'failure_count': failure_count,
        'avg_latency': avg_latency,
        'min_latency': min_latency,
        'max_latency': max_latency,
        'duration': duration,
        'errors': errors[:5],
        'resource_snapshots': resource_snapshots[:10]  # Only log first 10 for brevity
    }))
    
    summary = {
        'success_count': success_count,
        'failure_count': failure_count,
        'avg_latency': avg_latency,
        'min_latency': min_latency,
        'max_latency': max_latency,
        'duration': duration,
        'errors': errors[:5],
    }
    return summary

def generate_maintenance_report(report_file='maintenance_report.txt', days=7):
    """
    Generate a maintenance report summarizing recent actions and system health.
    - Summarizes maintenance actions from metrics_history.json (last N days)
    - Summarizes system resource usage from usage_metrics_log.csv
    - Outputs a human-readable report
    """
    lines = []
    now = datetime.now()
    lines.append(f"Maintenance Report - Generated {now.isoformat()}")
    lines.append("="*60)
    # Maintenance actions
    metrics_file = 'metrics_history.json'
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        lines.append("\nRecent Maintenance Actions:")
        for key in ['node_executions', 'cache_events']:
            if key in metrics and metrics[key]:
                recent = [e for e in metrics[key] if 'timestamp' in e and datetime.fromisoformat(e['timestamp']) > now - timedelta(days=days)]
                lines.append(f"- {key.replace('_', ' ').title()}: {len(recent)} events in last {days} days")
                for e in recent[-5:]:
                    lines.append(f"    {e['timestamp']}: {e}")
            else:
                lines.append(f"- {key.replace('_', ' ').title()}: No recent events.")
    else:
        lines.append("No metrics_history.json found.")
    # System health summary
    usage_log = 'usage_metrics_log.csv'
    if os.path.exists(usage_log):
        import pandas as pd
        df = pd.read_csv(usage_log)
        if not df.empty:
            lines.append("\nSystem Resource Usage (last 7 days):")
            for metric in ['memory_mb', 'cpu_percent', 'disk_percent']:
                if metric in df.columns:
                    values = pd.to_numeric(df[metric], errors='coerce').dropna()
                    if not values.empty:
                        lines.append(f"- {metric}: min={values.min():.2f}, max={values.max():.2f}, mean={values.mean():.2f}")
    else:
        lines.append("No usage_metrics_log.csv found.")
    # Save report
    with open(report_file, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Maintenance report written to {report_file}")
    return '\n'.join(lines) 