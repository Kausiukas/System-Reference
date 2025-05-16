# Troubleshooting Guide

## Overview
This guide helps diagnose and resolve common issues in the vector database and memory optimization system. Use it to quickly identify problems, apply solutions, and know when to escalate.

---

## Common Issues & Solutions

### 1. High Memory Usage
- **Symptoms:** App is slow, memory usage spikes, OOM errors.
- **Causes:** Large queries, memory leaks, unoptimized cache, model loading issues.
- **Solutions:**
  - Run `trend_analysis.py` to check for leaks.
  - Defragment index: `python -c "from maintenance_utils import defragment_index; defragment_index()"`
  - Rebuild cache: `python -c "from maintenance_utils import rebuild_cache; rebuild_cache()"`
  - Restart service: `python -c "from maintenance_utils import auto_restart_if_needed; auto_restart_if_needed()"`
  - Check logs for errors.

### 2. Slow Queries or Poor Performance
- **Symptoms:** High query latency, low throughput, timeouts.
- **Causes:** Fragmented index, cache not rebuilt, high load, insufficient hardware.
- **Solutions:**
  - Run performance test: `python test_performance.py`
  - Rebuild cache and defragment index.
  - Check for background jobs or high system load.
  - Review logs for bottlenecks.

### 3. Database Errors (ChromaDB, Annoy, FAISS)
- **Symptoms:** Errors on startup, failed queries, file not found, permission errors.
- **Causes:** File locks (Windows), corrupted files, concurrent access, missing dependencies.
- **Solutions:**
  - Ensure only one process accesses the DB at a time.
  - Check for file locks and close all related apps.
  - Restore from backup if files are corrupted.
  - Reinstall dependencies.

### 4. Log File or Disk Full
- **Symptoms:** App crashes, cannot write logs, disk space low.
- **Causes:** Log rotation not running, excessive logging, large data files.
- **Solutions:**
  - Run log rotation: `python -c "from maintenance_utils import rotate_logs; rotate_logs()"`
  - Delete/archive old logs and data.
  - Increase disk space if possible.

### 5. Maintenance Script Fails
- **Symptoms:** Script exits with error, no output, partial results.
- **Causes:** File locks, missing dependencies, permission issues, logic errors.
- **Solutions:**
  - Check logs for stack traces and error messages.
  - Ensure all dependencies are installed (`pip install -r requirements.txt`).
  - Run as administrator if needed.
  - Check for file locks (especially on Windows).

### 6. Purge/Deletion Not Working
- **Symptoms:** Documents not deleted, PermissionError, no effect.
- **Causes:** Attempt to purge persistent main DB (`D:/DATA`), missing permissions.
- **Solutions:**
  - Only purge local/test DBs (never `D:/DATA`).
  - Check path and permissions.

### 7. Model Loading Errors
- **Symptoms:** Errors like "Cannot copy out of meta tensor", model not found, slow startup.
- **Causes:** Corrupted HuggingFace cache, incompatible model, device mismatch.
- **Solutions:**
  - Clear HuggingFace cache (`rmdir /s /q %USERPROFILE%\.cache\huggingface`).
  - Use a supported model (e.g., `all-MiniLM-L6-v2`).
  - Check device and dtype settings.

---

## Diagnostic Steps
- **Check logs:** `logs/`, `D:/DATA/logs/`, `D:/GUI/logs/`
- **Run maintenance report:** `python -c "from maintenance_utils import generate_maintenance_report; generate_maintenance_report()"`
- **Run trend analysis:** `python trend_analysis.py`
- **Run performance/stress tests:** `python test_performance.py`, `python stress_test.py`
- **Check disk space:** `dir` or `df -h` (Linux)
- **Check running processes:** Task Manager (Windows) or `ps aux` (Linux)

---

## Escalation & Contact
- If the above steps do not resolve the issue:
  - Escalate to the system administrator or lead developer.
  - Provide relevant logs, error messages, and steps taken.
  - Document any changes made before the issue occurred.

---

## Best Practices
- Regularly monitor logs and reports.
- Run maintenance scripts on schedule.
- Test after major changes.
- Keep this guide up to date. 