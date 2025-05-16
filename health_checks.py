import time
from typing import Callable, Dict, Any
from metrics_tracker import get_metrics_tracker
from alerting import get_alert_manager

class HealthCheckRegistry:
    def __init__(self):
        self.checks = {}
        self.last_status = {}  # service_name -> {'healthy': bool, 'timestamp': float}

    def register(self, name: str, check_fn: Callable[[], bool]):
        self.checks[name] = check_fn

    def run_all(self) -> Dict[str, Any]:
        results = {}
        now = time.time()
        for name, fn in self.checks.items():
            try:
                start = time.time()
                healthy = fn()
                duration = time.time() - start
                results[name] = {'healthy': healthy, 'duration': duration}
                # Log result
                get_metrics_tracker().metrics_history.setdefault('health_checks', []).append({
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'service': name,
                    'healthy': healthy,
                    'duration': duration
                })
                # Uptime/downtime tracking
                prev = self.last_status.get(name)
                if prev is not None and prev['healthy'] != healthy:
                    # State changed: log event
                    event = {
                        'service': name,
                        'from': prev['healthy'],
                        'to': healthy,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                        'duration': now - prev['timestamp']
                    }
                    if healthy:
                        # Service recovered: log downtime duration
                        get_metrics_tracker().metrics_history.setdefault('service_downtime', []).append(event)
                    else:
                        # Service went down: log uptime duration
                        get_metrics_tracker().metrics_history.setdefault('service_uptime', []).append(event)
                # Update last status
                self.last_status[name] = {'healthy': healthy, 'timestamp': now}
                get_metrics_tracker().save_metrics_history()
                # Alert if unhealthy
                if not healthy:
                    get_alert_manager().alert_critical_error(
                        error_message=f"Health check failed for {name}",
                        context=f"Service: {name}",
                        stack_trace=None
                    )
            except Exception as e:
                get_metrics_tracker().log_error_with_context(e, function=f"health_check:{name}", critical=True)
                results[name] = {'healthy': False, 'duration': None, 'error': str(e)}
        return results

    def get_uptime_downtime_summary(self):
        """Return a summary of uptime/downtime for each service."""
        tracker = get_metrics_tracker()
        summary = {}
        for event in tracker.metrics_history.get('service_uptime', []):
            name = event['service']
            summary.setdefault(name, {'uptime': 0, 'downtime': 0})
            summary[name]['uptime'] += event['duration']
        for event in tracker.metrics_history.get('service_downtime', []):
            name = event['service']
            summary.setdefault(name, {'uptime': 0, 'downtime': 0})
            summary[name]['downtime'] += event['duration']
        return summary

# Singleton registry
_health_check_registry = HealthCheckRegistry()

def register_health_check(name: str, check_fn: Callable[[], bool]):
    _health_check_registry.register(name, check_fn)

def run_all_health_checks() -> Dict[str, Any]:
    return _health_check_registry.run_all() 