import psutil
import csv
import os
from datetime import datetime
from logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

try:
    import GPUtil
except ImportError:
    GPUtil = None

def log_usage_metrics(log_file: str = 'usage_metrics_log.csv'):
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = psutil.cpu_percent(interval=0.1)
    disk_percent = psutil.disk_usage('/').percent
    net_io = psutil.net_io_counters()
    bytes_sent = net_io.bytes_sent
    bytes_recv = net_io.bytes_recv
    # GPU metrics
    if GPUtil:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_load = f"{gpus[0].load*100:.2f}"
            gpu_mem = f"{gpus[0].memoryUtil*100:.2f}"
        else:
            gpu_load = gpu_mem = "N/A"
    else:
        gpu_load = gpu_mem = "N/A"
    timestamp = datetime.now().isoformat()
    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['timestamp', 'memory_mb', 'cpu_percent', 'disk_percent', 'bytes_sent', 'bytes_recv', 'gpu_load', 'gpu_mem'])
        writer.writerow([timestamp, f"{mem_mb:.2f}", f"{cpu_percent:.2f}", f"{disk_percent:.2f}", bytes_sent, bytes_recv, gpu_load, gpu_mem])
    logger.info(f"System metrics logged - Memory: {mem_mb:.2f}MB, CPU: {cpu_percent:.2f}%, Disk: {disk_percent:.2f}%")

if __name__ == "__main__":
    log_usage_metrics() 