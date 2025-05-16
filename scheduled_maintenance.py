import schedule
import time
from maintenance_utils import defragment_index, rebuild_cache, rotate_logs, auto_restart_if_needed, run_stress_test, generate_maintenance_report
from logging_utils import get_logger
import json
from pathlib import Path
from datetime import datetime, timedelta
import trend_analysis
import tracemalloc

# Configure logging
logger = get_logger(__name__)

class MaintenanceScheduler:
    def __init__(self, config_file: str = "maintenance_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self._setup_schedules()
    
    def _load_config(self) -> dict:
        """Load maintenance configuration from file or use defaults."""
        default_config = {
            "defragmentation": {
                "enabled": True,
                "schedule": "02:00",  # Daily at 2 AM
                "max_runtime": 3600,  # 1 hour
                "min_interval": 24,   # Minimum hours between runs
                "memory_threshold": 80  # Run if memory usage > 80%
            },
            "cache_rebuild": {
                "enabled": True,
                "schedule": "every_6_hours",
                "max_runtime": 1800,  # 30 minutes
                "min_interval": 4     # Minimum hours between runs
            },
            "log_rotation": {
                "enabled": True,
                "schedule": "00:00",  # Daily at midnight
                "max_size_mb": 10,
                "backup_count": 5
            },
            "auto_restart": {
                "enabled": True,
                "memory_threshold": 90,  # Restart if memory > 90%
                "cpu_threshold": 95,     # Restart if CPU > 95%
                "check_interval": 300    # Check every 5 minutes
            }
        }
        
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Save default config
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return default_config
    
    def _setup_schedules(self):
        """Set up all scheduled maintenance tasks."""
        # Defragmentation
        if self.config["defragmentation"]["enabled"]:
            schedule.every().day.at(self.config["defragmentation"]["schedule"]).do(
                self._run_defragmentation
            )
            logger.info(f"Scheduled defragmentation for {self.config['defragmentation']['schedule']}")
        
        # Cache rebuild
        if self.config["cache_rebuild"]["enabled"]:
            if self.config["cache_rebuild"]["schedule"] == "every_6_hours":
                schedule.every(6).hours.do(self._run_cache_rebuild)
            else:
                schedule.every().day.at(self.config["cache_rebuild"]["schedule"]).do(
                    self._run_cache_rebuild
                )
            logger.info(f"Scheduled cache rebuild: {self.config['cache_rebuild']['schedule']}")
        
        # Log rotation
        if self.config["log_rotation"]["enabled"]:
            schedule.every().day.at(self.config["log_rotation"]["schedule"]).do(
                self._run_log_rotation
            )
            logger.info(f"Scheduled log rotation for {self.config['log_rotation']['schedule']}")
        
        # Auto-restart check
        if self.config["auto_restart"]["enabled"]:
            schedule.every(self.config["auto_restart"]["check_interval"]).seconds.do(
                self._check_auto_restart
            )
            logger.info(f"Scheduled auto-restart check every {self.config['auto_restart']['check_interval']} seconds")
        
        schedule.every(1).hours.do(self.run_memory_stability_check)
        schedule.every(6).hours.do(self.run_memory_leak_check)
    
    def _run_defragmentation(self):
        """Run defragmentation with checks and logging."""
        try:
            logger.info("Starting scheduled defragmentation")
            start_time = time.time()
            
            # Check if enough time has passed since last run
            last_run_file = Path("last_defragmentation.txt")
            if last_run_file.exists():
                with open(last_run_file, 'r') as f:
                    last_run = datetime.fromisoformat(f.read().strip())
                hours_since_last = (datetime.now() - last_run).total_seconds() / 3600
                if hours_since_last < self.config["defragmentation"]["min_interval"]:
                    logger.info(f"Skipping defragmentation: {hours_since_last:.1f} hours since last run")
                    return
            
            # Run defragmentation
            success = defragment_index()
            
            # Record run time
            duration = time.time() - start_time
            if duration > self.config["defragmentation"]["max_runtime"]:
                logger.warning(f"Defragmentation took longer than max runtime: {duration:.1f}s")
            
            # Update last run time
            with open(last_run_file, 'w') as f:
                f.write(datetime.now().isoformat())
            
            logger.info(f"Completed scheduled defragmentation in {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"Error during scheduled defragmentation: {str(e)}")
    
    def _run_cache_rebuild(self):
        """Run cache rebuild with checks and logging."""
        try:
            logger.info("Starting scheduled cache rebuild")
            start_time = time.time()
            
            # Check if enough time has passed since last run
            last_run_file = Path("last_cache_rebuild.txt")
            if last_run_file.exists():
                with open(last_run_file, 'r') as f:
                    last_run = datetime.fromisoformat(f.read().strip())
                hours_since_last = (datetime.now() - last_run).total_seconds() / 3600
                if hours_since_last < self.config["cache_rebuild"]["min_interval"]:
                    logger.info(f"Skipping cache rebuild: {hours_since_last:.1f} hours since last run")
                    return
            
            # Run cache rebuild
            success = rebuild_cache()
            
            # Record run time
            duration = time.time() - start_time
            if duration > self.config["cache_rebuild"]["max_runtime"]:
                logger.warning(f"Cache rebuild took longer than max runtime: {duration:.1f}s")
            
            # Update last run time
            with open(last_run_file, 'w') as f:
                f.write(datetime.now().isoformat())
            
            logger.info(f"Completed scheduled cache rebuild in {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"Error during scheduled cache rebuild: {str(e)}")
    
    def _run_log_rotation(self):
        """Run log rotation with checks and logging."""
        try:
            logger.info("Starting scheduled log rotation")
            start_time = time.time()
            
            # Run log rotation
            success = rotate_logs()
            
            # Record run time
            duration = time.time() - start_time
            logger.info(f"Completed scheduled log rotation in {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"Error during scheduled log rotation: {str(e)}")
    
    def _check_auto_restart(self):
        """Check if auto-restart is needed based on resource usage."""
        try:
            logger.info("Checking if auto-restart is needed")
            from metrics_tracker import get_metrics_tracker
            metrics = get_metrics_tracker()
            success = auto_restart_if_needed()
            if success:
                logger.info("Auto-restart triggered")
                metrics.log_recovery_event(True, reason="auto_restart", error=None)
            else:
                metrics.log_recovery_event(False, reason="auto_restart", error="Auto-restart not triggered")
        except Exception as e:
            logger.error(f"Error during auto-restart check: {str(e)}")
            from metrics_tracker import get_metrics_tracker
            metrics = get_metrics_tracker()
            metrics.log_recovery_event(False, reason="auto_restart_exception", error=str(e))
    
    def run_memory_stability_check(self):
        from metrics_tracker import get_metrics_tracker
        import json
        metrics = get_metrics_tracker()
        import io
        import sys
        # Capture output
        buf = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = buf
        try:
            trend_analysis.analyze_memory_trend()
        finally:
            sys.stdout = sys_stdout
        output = buf.getvalue()
        # Log to metrics_history.json
        metrics.metrics_history.setdefault('memory_stability_checks', []).append({
            'timestamp': datetime.now().isoformat(),
            'output': output
        })
        metrics.save_metrics_history()
        # Alert if leak detected
        if 'WARNING: Upward memory trend detected' in output:
            from alerting import get_alert_manager
            get_alert_manager().alert_critical_error(
                error_message='Memory leak or regression detected',
                context=output,
                stack_trace=None
            )
    
    def run_memory_leak_check(self):
        from metrics_tracker import get_metrics_tracker
        import json
        metrics = get_metrics_tracker()
        import io
        import sys
        buf = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = buf
        try:
            tracemalloc.start()
            snapshot1 = tracemalloc.take_snapshot()
            time.sleep(10)  # Short interval for demo; increase for real use
            snapshot2 = tracemalloc.take_snapshot()
            stats = snapshot2.compare_to(snapshot1, 'lineno')
            output_lines = [f"Top 10 memory growth (by line):"]
            for stat in stats[:10]:
                output_lines.append(str(stat))
            total_growth = sum(stat.size_diff for stat in stats)
            output_lines.append(f"Total growth: {total_growth/1024:.2f} KB")
            output = '\n'.join(output_lines)
        finally:
            sys.stdout = sys_stdout
            tracemalloc.stop()
        # Log to metrics_history.json
        metrics.metrics_history.setdefault('memory_leak_checks', []).append({
            'timestamp': datetime.now().isoformat(),
            'output': output
        })
        metrics.save_metrics_history()
        # Alert if significant growth
        if total_growth > 1024*100:  # >100MB
            from alerting import get_alert_manager
            get_alert_manager().alert_critical_error(
                error_message='Potential memory leak detected (tracemalloc)',
                context=output,
                stack_trace=None
            )
    
    def run_memory_stability_tracking(self):
        """Run comprehensive memory stability tracking and analysis."""
        try:
            from metrics_tracker import get_metrics_tracker
            metrics_tracker = get_metrics_tracker()
            
            # Get memory stability report
            report = metrics_tracker.track_memory_stability()
            
            # Log results
            logger.info("Memory stability tracking completed")
            for window, stats in report.get('windows', {}).items():
                logger.info(f"{window} window: {stats.get('stability', 'unknown')} " +
                          f"(trend: {stats.get('trend', 0):.4f} MB/sample)")
                
                if 'anomalies' in stats:
                    logger.warning(f"Found {stats['anomalies']['count']} memory anomalies in {window} window")
            
            return True
        except Exception as e:
            logger.error(f"Error in memory stability tracking: {str(e)}")
            return False
    
    def run(self):
        """Run the scheduler loop."""
        logger.info("Starting maintenance scheduler")
        from metrics_tracker import get_metrics_tracker
        metrics = get_metrics_tracker()
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                metrics.log_recovery_event(False, reason="scheduler_loop_exception", error=str(e))
                time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    scheduler = MaintenanceScheduler()
    scheduler.run() 