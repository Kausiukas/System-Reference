import logging
import schedule
import time
from memory_cleanup import memory_cleanup
from memory_tracker import log_usage_metrics
from maintenance_utils import defragment_index, rebuild_cache, rotate_logs, auto_restart_if_needed, run_stress_test, generate_maintenance_report

def periodic_tasks():
    logging.info("Running periodic maintenance tasks...")
    # Log usage metrics
    log_usage_metrics()
    # Example: Run memory cleanup with a 500MB threshold
    memory_cleanup(threshold_mb=500)
    # Defragment index
    defragment_index()
    # Rebuild cache
    rebuild_cache()
    # Rotate logs
    rotate_logs()
    # Auto-restart if needed
    auto_restart_if_needed()
    # Run stress test (optional)
    run_stress_test()
    # Generate maintenance report
    report = generate_maintenance_report()
    logging.info(report)
    # Add other maintenance tasks here as needed

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    schedule.every(1).hours.do(periodic_tasks)
    logging.info("Scheduled periodic maintenance every hour.")
    while True:
        schedule.run_pending()
        time.sleep(60) 