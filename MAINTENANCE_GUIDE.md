# Maintenance Guide

## Overview
This guide documents all routine and emergency maintenance procedures for the vector database and memory optimization system. It is intended for future maintainers and operators.

---

## Routine Maintenance Tasks

### 1. Defragmentation
- **Script:** `maintenance_utils.py` (`defragment_index()`)
- **Purpose:** Rebuilds vector store indices for optimal performance and memory usage.
- **How to Run:**
  - Manually: `python -c "from maintenance_utils import defragment_index; defragment_index()"`
  - Scheduled: Included in `scheduled_maintenance.py` (runs daily at 2:00 AM)
- **Output:** Logs to file and updates metrics.

### 2. Cache Rebuild
- **Script:** `maintenance_utils.py` (`rebuild_cache()`)
- **Purpose:** Rebuilds the Annoy cache with the most frequently accessed documents.
- **How to Run:**
  - Manually: `python -c "from maintenance_utils import rebuild_cache; rebuild_cache()"`
  - Scheduled: Included in `scheduled_maintenance.py` (runs every 6 hours)
- **Output:** Logs to file and updates metrics.

### 3. Log Rotation
- **Script:** `maintenance_utils.py` (`rotate_logs()`)
- **Purpose:** Rotates and archives log files to prevent disk bloat.
- **How to Run:**
  - Manually: `python -c "from maintenance_utils import rotate_logs; rotate_logs()"`
  - Scheduled: Included in `scheduled_maintenance.py`
- **Output:** Logs to file and archives old logs.

### 4. Auto-Restart
- **Script:** `maintenance_utils.py` (`auto_restart_if_needed()`)
- **Purpose:** Restarts the service if resource usage exceeds thresholds.
- **How to Run:**
  - Manually: `python -c "from maintenance_utils import auto_restart_if_needed; auto_restart_if_needed()"`
  - Scheduled: Included in `scheduled_maintenance.py`
- **Output:** Logs to file and triggers restart if needed.

### 5. Stress Testing
- **Script:** `stress_test.py`
- **Purpose:** Simulates high load to identify bottlenecks and failure points.
- **How to Run:** `python stress_test.py`
- **Output:** Results saved to `stress_test_results.json`.

### 6. Performance Testing
- **Script:** `test_performance.py`
- **Purpose:** Validates system speed and reliability after changes.
- **How to Run:** `python test_performance.py`
- **Output:** Results saved to `performance_results.json`.

### 7. Maintenance Report Generation
- **Script:** `maintenance_utils.py` (`generate_maintenance_report()`)
- **Purpose:** Summarizes recent maintenance actions and system health.
- **How to Run:**
  - Manually: `python -c "from maintenance_utils import generate_maintenance_report; generate_maintenance_report()"`
  - Scheduled: Included in `scheduled_maintenance.py`
- **Output:** Report saved to `maintenance_report.txt`.

### 8. Trend Analysis
- **Script:** `trend_analysis.py`
- **Purpose:** Detects slow memory leaks or performance regressions.
- **How to Run:** `python trend_analysis.py`
- **Output:** Prints analysis to console.

---

## Emergency Maintenance
- **Manual Purging:** Only allowed on local/test databases (never on `D:/DATA`). Use the `purge_documents` method in vector DB classes with caution.
- **Crash Recovery:** Check logs for errors, run `auto_restart_if_needed()`, and consult the maintenance report for recent issues.
- **Disk Full:** Run `rotate_logs()` and clear old data if needed.

---

## Scheduling
- **Script:** `scheduled_maintenance.py`
- **How to Use:**
  - Run in the background on your server: `python scheduled_maintenance.py`
  - Defragmentation and full maintenance: daily at 2:00 AM
  - Cache rebuild: every 6 hours
- **Logs:** All actions are logged for audit and troubleshooting.

---

## Best Practices
- **Never purge or modify the persistent main database (`D:/DATA`) except via approved scripts.**
- **Monitor logs and reports regularly.**
- **Test performance and stress after major changes.**
- **Keep this guide up to date with any new procedures or scripts.**

---

## Troubleshooting
- **Check logs** in `logs/`, `D:/DATA/logs/`, or `D:/GUI/logs/` for errors and warnings.
- **Review `maintenance_report.txt`** for recent actions and system health.
- **Use `trend_analysis.py`** to detect memory leaks or regressions.
- **If a script fails:**
  - Check for file locks (especially on Windows).
  - Ensure all dependencies are installed.
  - Review recent changes for possible regressions.

---

## Contact
For further help, contact the system administrator or lead developer. 