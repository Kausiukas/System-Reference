import gc
import psutil
from datetime import datetime
from logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

def log_gc_stats(log_file: str = 'gc_stats.log'):
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024
    gc.collect()
    mem_after = process.memory_info().rss / 1024 / 1024
    gc_counts = gc.get_count()
    gc_stats = gc.get_stats() if hasattr(gc, 'get_stats') else None
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] GC run\n")
        f.write(f"Memory before: {mem_before:.2f} MB\n")
        f.write(f"Memory after: {mem_after:.2f} MB\n")
        f.write(f"GC counts: {gc_counts}\n")
        if gc_stats:
            f.write(f"GC stats: {gc_stats}\n")
        f.write("\n")
    logger.info(f"GC run: memory before {mem_before:.2f} MB, after {mem_after:.2f} MB, counts {gc_counts}")
    return mem_before, mem_after, gc_counts, gc_stats

def manual_gc_and_log():
    return log_gc_stats() 