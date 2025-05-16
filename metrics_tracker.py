import time
import psutil
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from logging_utils import get_logger
import threading
import pandas as pd
import numpy as np

# Configure logging
logger = get_logger(__name__)

class MetricsTracker:
    def __init__(self):
        self.metrics_history: Dict[str, list] = {
            'memory_usage': [],
            'startup_time': [],
            'query_response_time': [],
            'cache_hit_rate': [],
            'crash_frequency': [],
            'service_uptime': [],
            'recovery_success': [],
            'peak_memory_usage': [],
            'llm_calls': [],
            'embedding_calls': [],
            'node_agent_executions': [],
            'cpu_usage': [],
            'gpu_usage': [],
            'cache_events': [],
            'node_executions': [],
            'llm_success_rate': [],
            'memory_stability_reports': [],
            'memory_leak_checks': []
        }
        self.metrics_file = Path('metrics_history.json')
        self.load_metrics_history()
    
    def load_metrics_history(self):
        """Load metrics history from file if it exists and ensure all keys are present."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    self.metrics_history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metrics history: {str(e)}")
        self._ensure_all_keys()

    def _ensure_all_keys(self):
        # Ensure all expected keys are present
        for key in [
            'memory_usage', 'startup_time', 'query_response_time', 'cache_hit_rate',
            'crash_frequency', 'service_uptime', 'recovery_success', 'peak_memory_usage',
            'llm_calls', 'embedding_calls', 'node_agent_executions', 'cpu_usage', 'gpu_usage', 'cache_events', 'node_executions']:
            if key not in self.metrics_history:
                self.metrics_history[key] = []
    
    def save_metrics_history(self):
        """Save metrics history to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics history: {str(e)}")
    
    def track_memory_usage(self) -> float:
        """Track current memory usage in MB."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.metrics_history['memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': memory_mb
            })
            logger.info(f"Memory usage: {memory_mb:.2f} MB")
            return memory_mb
        except Exception as e:
            logger.error(f"Error tracking memory usage: {str(e)}")
            return 0.0
    
    def track_startup_time(self, start_time: float) -> float:
        """Track startup time in seconds."""
        try:
            startup_time = time.time() - start_time
            self.metrics_history['startup_time'].append({
                'timestamp': datetime.now().isoformat(),
                'value': startup_time
            })
            logger.info(f"Startup time: {startup_time:.2f} seconds")
            return startup_time
        except Exception as e:
            logger.error(f"Error tracking startup time: {str(e)}")
            return 0.0
    
    def track_query_response_time(self, query_time: float):
        """Track query response time in seconds."""
        try:
            self.metrics_history['query_response_time'].append({
                'timestamp': datetime.now().isoformat(),
                'value': query_time
            })
            logger.info(f"Query response time: {query_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error tracking query response time: {str(e)}")
    
    def track_cache_hit_rate(self, hit_rate: float):
        """Track cache hit rate as a percentage."""
        try:
            self.metrics_history['cache_hit_rate'].append({
                'timestamp': datetime.now().isoformat(),
                'value': hit_rate
            })
            logger.info(f"Cache hit rate: {hit_rate:.2f}%")
        except Exception as e:
            logger.error(f"Error tracking cache hit rate: {str(e)}")
    
    def track_crash(self):
        """Track application crash."""
        try:
            self.metrics_history['crash_frequency'].append({
                'timestamp': datetime.now().isoformat(),
                'value': 1
            })
            logger.warning("Application crash detected")
        except Exception as e:
            logger.error(f"Error tracking crash: {str(e)}")
    
    def track_service_uptime(self, uptime: float):
        """Track service uptime in seconds."""
        try:
            self.metrics_history['service_uptime'].append({
                'timestamp': datetime.now().isoformat(),
                'value': uptime
            })
            logger.info(f"Service uptime: {uptime:.2f} seconds")
        except Exception as e:
            logger.error(f"Error tracking service uptime: {str(e)}")
    
    def track_recovery_success(self, success: bool):
        """Track recovery success."""
        try:
            self.metrics_history['recovery_success'].append({
                'timestamp': datetime.now().isoformat(),
                'value': 1 if success else 0
            })
            logger.info(f"Recovery {'successful' if success else 'failed'}")
        except Exception as e:
            logger.error(f"Error tracking recovery success: {str(e)}")
    
    def track_peak_memory_usage(self) -> float:
        """Track peak (maximum) memory usage in MB."""
        try:
            process = psutil.Process()
            if hasattr(process, 'memory_info') and hasattr(process.memory_info(), 'peak_wset'):
                # On Windows, peak_wset is peak working set
                peak = process.memory_info().peak_wset / (1024 * 1024)
            elif hasattr(process, 'memory_info') and hasattr(process.memory_info(), 'rss'):
                # On Unix, rss is resident set size (current, not peak)
                # Use max of all recorded rss values as a proxy
                peak = max([m['value'] for m in self.metrics_history['memory_usage']] or [0])
            else:
                peak = 0.0
            self.metrics_history['peak_memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': peak
            })
            logger.info(f"Peak memory usage: {peak:.2f} MB")
            return peak
        except Exception as e:
            logger.error(f"Error tracking peak memory usage: {str(e)}")
            return 0.0
    
    def track_llm_call(self, model_name: str, input_size: int, latency: float, success: bool, error: str = None, token_usage: dict = None):
        """Track LLM call metrics, including token usage (total, prompt, completion tokens)."""
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'model_name': model_name,
                'input_size': input_size,
                'latency': latency,
                'success': success,
                'error': error
            }
            if token_usage:
                entry['token_usage'] = token_usage
                entry['total_tokens'] = token_usage.get('total_tokens')
                entry['prompt_tokens'] = token_usage.get('prompt_tokens')
                entry['completion_tokens'] = token_usage.get('completion_tokens')
            else:
                entry['token_usage'] = None
                entry['total_tokens'] = None
                entry['prompt_tokens'] = None
                entry['completion_tokens'] = None
            self.metrics_history['llm_calls'].append(entry)
            logger.info(f"LLM call tracked: {model_name} | Latency: {latency:.2f}s | Success: {success} | Tokens: {entry['total_tokens']} (Prompt: {entry['prompt_tokens']}, Completion: {entry['completion_tokens']})")
        except Exception as e:
            logger.error(f"Error tracking LLM call: {str(e)}")

    def track_embedding_call(self, model_name: str, input_size: int, latency: float, success: bool, error: str = None):
        """Track embedding call metrics."""
        try:
            self.metrics_history['embedding_calls'].append({
                'timestamp': datetime.now().isoformat(),
                'model_name': model_name,
                'input_size': input_size,
                'latency': latency,
                'success': success,
                'error': error
            })
            logger.info(f"Embedding call tracked: {model_name} | Latency: {latency:.2f}s | Success: {success}")
        except Exception as e:
            logger.error(f"Error tracking embedding call: {str(e)}")

    def track_node_agent_execution(self, name, start_time, end_time, status, error=None):
        duration = end_time - start_time
        entry = {
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'status': status,
            'error': error
        }
        self.metrics_history['node_agent_executions'].append(entry)
        self.save_metrics_history()

    def get_node_agent_executions(self, name=None):
        executions = self.metrics_history['node_agent_executions']
        if name:
            return [e for e in executions if e['name'] == name]
        return executions

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        summary = {}
        for metric, values in self.metrics_history.items():
            if values:
                recent_values = [v['value'] for v in values[-10:]]  # Last 10 values
                summary[metric] = {
                    'current': recent_values[-1] if recent_values else None,
                    'average': sum(recent_values) / len(recent_values) if recent_values else None,
                    'min': min(recent_values) if recent_values else None,
                    'max': max(recent_values) if recent_values else None
                }
        return summary
    
    def log_metrics_summary(self):
        """Log a summary of all metrics."""
        summary = self.get_metrics_summary()
        logger.info("Metrics Summary:")
        for metric, stats in summary.items():
            logger.info(f"{metric}:")
            for stat, value in stats.items():
                if value is not None:
                    logger.info(f"  {stat}: {value:.2f}")
        self.save_metrics_history()

    def get_llm_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of LLM call metrics, including token usage."""
        if not self.metrics_history['llm_calls']:
            return {}
        calls = self.metrics_history['llm_calls']
        total_calls = len(calls)
        success_rate = sum(1 for c in calls if c['success']) / total_calls
        avg_latency = sum(c['latency'] for c in calls) / total_calls
        avg_input_size = sum(c['input_size'] for c in calls) / total_calls
        error_count = sum(1 for c in calls if not c['success'])
        # Token usage averages
        total_tokens = [c.get('total_tokens') for c in calls if c.get('total_tokens') is not None]
        prompt_tokens = [c.get('prompt_tokens') for c in calls if c.get('prompt_tokens') is not None]
        completion_tokens = [c.get('completion_tokens') for c in calls if c.get('completion_tokens') is not None]
        avg_total_tokens = sum(total_tokens) / len(total_tokens) if total_tokens else 0
        avg_prompt_tokens = sum(prompt_tokens) / len(prompt_tokens) if prompt_tokens else 0
        avg_completion_tokens = sum(completion_tokens) / len(completion_tokens) if completion_tokens else 0
        return {
            'total_calls': total_calls,
            'success_rate': success_rate,
            'avg_latency': avg_latency,
            'avg_input_size': avg_input_size,
            'error_count': error_count,
            'avg_total_tokens': avg_total_tokens,
            'avg_prompt_tokens': avg_prompt_tokens,
            'avg_completion_tokens': avg_completion_tokens
        }

    def get_embedding_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of embedding call metrics."""
        if not self.metrics_history['embedding_calls']:
            return {}
        
        calls = self.metrics_history['embedding_calls']
        return {
            'total_calls': len(calls),
            'success_rate': sum(1 for c in calls if c['success']) / len(calls),
            'avg_latency': sum(c['latency'] for c in calls) / len(calls),
            'avg_input_size': sum(c['input_size'] for c in calls) / len(calls),
            'error_count': sum(1 for c in calls if not c['success'])
        }

    def track_cpu_usage(self) -> float:
        """Track current CPU usage percentage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_history['cpu_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': cpu_percent
            })
            logger.info(f"CPU usage: {cpu_percent:.2f}%")
            return cpu_percent
        except Exception as e:
            logger.error(f"Error tracking CPU usage: {str(e)}")
            return 0.0

    def track_gpu_usage(self) -> Optional[float]:
        """Track current GPU usage percentage (if available)."""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_percent = torch.cuda.utilization() if hasattr(torch.cuda, 'utilization') else None
                if gpu_percent is None:
                    # Fallback: use nvidia-smi
                    import subprocess
                    result = subprocess.run([
                        'nvidia-smi',
                        '--query-gpu=utilization.gpu',
                        '--format=csv,noheader,nounits'
                    ], capture_output=True, text=True)
                    gpu_percent = float(result.stdout.strip().split('\n')[0])
                self.metrics_history['gpu_usage'].append({
                    'timestamp': datetime.now().isoformat(),
                    'value': gpu_percent
                })
                logger.info(f"GPU usage: {gpu_percent:.2f}%")
                return gpu_percent
            else:
                logger.info("No GPU available for usage tracking.")
                return None
        except Exception as e:
            logger.error(f"Error tracking GPU usage: {str(e)}")
            return None

    def track_cache_event(self, cache_name: str, hit: bool):
        """Log a cache hit or miss event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'cache_name': cache_name,
            'hit': hit
        }
        self.metrics_history['cache_events'].append(event)
        self.save_metrics_history()
        self._update_cache_hit_rate(cache_name)

    def _update_cache_hit_rate(self, cache_name: str):
        """Update cache hit rate for the given cache."""
        events = [e for e in self.metrics_history['cache_events'] if e['cache_name'] == cache_name]
        if not events:
            return
        hits = sum(1 for e in events if e['hit'])
        hit_rate = 100.0 * hits / len(events)
        self.metrics_history['cache_hit_rate'].append({
            'timestamp': datetime.now().isoformat(),
            'cache_name': cache_name,
            'value': hit_rate
        })
        self.save_metrics_history()

    def get_cache_hit_rate(self, cache_name: str = None):
        """Get cache hit rate for a specific cache or all caches."""
        rates = self.metrics_history['cache_hit_rate']
        if cache_name:
            rates = [r for r in rates if r.get('cache_name') == cache_name]
        return rates

    def log_error_with_context(self, error: Exception, function: str = None, params: dict = None, critical: bool = False):
        import traceback
        error_message = str(error)
        stack_trace = traceback.format_exc()
        context = f"Function: {function}\nParams: {params}" if function or params else None
        logger.error(f"Error: {error_message}\n{context if context else ''}\nStack trace:\n{stack_trace}")
        # Optionally alert on critical errors
        if critical:
            from alerting import get_alert_manager
            get_alert_manager().alert_critical_error(error_message, context, stack_trace)

    def get_llm_throughput(self, window_seconds: int = 60) -> float:
        """Calculate LLM call throughput (calls per window_seconds)."""
        now = datetime.now().timestamp()
        calls = [c for c in self.metrics_history['llm_calls'] if 'timestamp' in c]
        recent = [c for c in calls if (now - datetime.fromisoformat(c['timestamp']).timestamp()) <= window_seconds]
        throughput = len(recent) / (window_seconds / 60)  # calls per minute
        return throughput

    def log_node_execution(self, node_name: str, start_time: float, end_time: float, status: str, error: str = None):
        duration = end_time - start_time
        entry = {
            'timestamp': datetime.now().isoformat(),
            'node_name': node_name,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'status': status,
            'error': error
        }
        self.metrics_history['node_executions'].append(entry)
        self.save_metrics_history()

    def get_graph_traversal_rate(self, window_seconds: int = 60) -> float:
        """Calculate the number of node executions per window_seconds."""
        now = datetime.now().timestamp()
        executions = self.metrics_history['node_executions']
        recent = [e for e in executions if (now - e['start_time']) <= window_seconds]
        rate = len(recent) / (window_seconds / 60)  # nodes per minute
        return rate

    def start_periodic_metrics_logging(self, interval_seconds: int = 60):
        """Start a background thread to periodically log system metrics."""
        if hasattr(self, '_metrics_thread') and self._metrics_thread.is_alive():
            logger.info("Periodic metrics logging already running.")
            return
        def log_metrics_loop():
            while True:
                try:
                    self.track_memory_usage()
                    self.track_cpu_usage()
                    self.track_gpu_usage()
                    self.save_metrics_history()
                except Exception as e:
                    logger.error(f"Error in periodic metrics logging: {str(e)}")
                time.sleep(interval_seconds)
        self._metrics_thread = threading.Thread(target=log_metrics_loop, daemon=True)
        self._metrics_thread.start()
        logger.info(f"Started periodic metrics logging every {interval_seconds} seconds.")

    def compute_llm_success_rate(self, window_seconds: int = 600):
        """Compute and log LLM call success/failure rates over the last window_seconds."""
        now = datetime.now().timestamp()
        calls = [c for c in self.metrics_history['llm_calls'] if 'timestamp' in c]
        recent = [c for c in calls if (now - datetime.fromisoformat(c['timestamp']).timestamp()) <= window_seconds]
        if not recent:
            logger.info("No recent LLM calls to compute success rate.")
            return None
        successes = sum(1 for c in recent if c.get('success'))
        failures = sum(1 for c in recent if not c.get('success'))
        total = len(recent)
        success_rate = successes / total if total else 0.0
        failure_rate = failures / total if total else 0.0
        logger.info(f"LLM Success Rate (last {window_seconds}s): {success_rate:.2%} ({successes}/{total})")
        logger.info(f"LLM Failure Rate (last {window_seconds}s): {failure_rate:.2%} ({failures}/{total})")
        # Store in metrics_history
        self.metrics_history.setdefault('llm_success_rate', []).append({
            'timestamp': datetime.now().isoformat(),
            'window_seconds': window_seconds,
            'success_rate': success_rate,
            'failure_rate': failure_rate,
            'successes': successes,
            'failures': failures,
            'total': total
        })
        self.save_metrics_history()
        return success_rate, failure_rate

    def get_memory_window_stats(self, window_hours: int = 24) -> Dict[str, float]:
        """Calculate memory statistics for the specified time window."""
        try:
            now = datetime.now()
            window_start = now - timedelta(hours=window_hours)
            
            # Filter memory usage data for the window
            window_data = [
                m for m in self.metrics_history['memory_usage']
                if datetime.fromisoformat(m['timestamp']) >= window_start
            ]
            
            if not window_data:
                return {
                    'min': 0.0,
                    'max': 0.0,
                    'mean': 0.0,
                    'std': 0.0,
                    'trend': 0.0
                }
            
            values = [m['value'] for m in window_data]
            
            # Calculate basic statistics
            stats = {
                'min': min(values),
                'max': max(values),
                'mean': np.mean(values),
                'std': np.std(values)
            }
            
            # Calculate trend (linear regression slope)
            if len(values) > 1:
                x = np.arange(len(values))
                slope, _, _, _, _ = np.polyfit(x, values, 1)
                stats['trend'] = slope
            else:
                stats['trend'] = 0.0
            
            return stats
        except Exception as e:
            logger.error(f"Error calculating memory window stats: {str(e)}")
            return {
                'min': 0.0,
                'max': 0.0,
                'mean': 0.0,
                'std': 0.0,
                'trend': 0.0
            }

    def get_memory_stability_report(self) -> Dict[str, Any]:
        """Generate a comprehensive memory stability report with multiple time windows."""
        try:
            windows = {
                '1h': 1,
                '6h': 6,
                '24h': 24,
                '7d': 24 * 7
            }
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'windows': {}
            }
            
            for name, hours in windows.items():
                stats = self.get_memory_window_stats(hours)
                report['windows'][name] = stats
                
                # Add stability assessment
                if stats['trend'] > 0.05:  # MB per sample
                    report['windows'][name]['stability'] = 'increasing'
                elif stats['trend'] < -0.05:
                    report['windows'][name]['stability'] = 'decreasing'
                else:
                    report['windows'][name]['stability'] = 'stable'
                
                # Add anomaly detection
                if stats['std'] > 0:
                    recent_values = [m['value'] for m in self.metrics_history['memory_usage'][-50:]]
                    if recent_values:
                        z_scores = np.abs((recent_values - stats['mean']) / stats['std'])
                        anomalies = np.where(z_scores > 3)[0]
                        if len(anomalies) > 0:
                            report['windows'][name]['anomalies'] = {
                                'count': len(anomalies),
                                'timestamps': [self.metrics_history['memory_usage'][-50:][i]['timestamp'] 
                                             for i in anomalies]
                            }
            
            # Save report to metrics history
            self.metrics_history.setdefault('memory_stability_reports', []).append(report)
            self.save_metrics_history()
            
            return report
        except Exception as e:
            logger.error(f"Error generating memory stability report: {str(e)}")
            return {}

    def track_memory_stability(self) -> Dict[str, Any]:
        """Track memory stability and generate alerts if needed."""
        try:
            report = self.get_memory_stability_report()
            
            # Check for concerning trends
            for window, stats in report.get('windows', {}).items():
                if stats.get('stability') == 'increasing':
                    logger.warning(f"Memory usage is increasing in {window} window (trend: {stats['trend']:.4f} MB/sample)")
                    # Alert if trend is significant
                    if stats['trend'] > 0.1:  # MB per sample
                        from alerting import get_alert_manager
                        get_alert_manager().alert_critical_error(
                            error_message=f"Significant memory increase detected in {window} window",
                            context=f"Trend: {stats['trend']:.4f} MB/sample, Mean: {stats['mean']:.2f} MB",
                            stack_trace=None
                        )
                
                # Check for anomalies
                if 'anomalies' in stats:
                    logger.warning(f"Memory anomalies detected in {window} window: {stats['anomalies']['count']} occurrences")
            
            return report
        except Exception as e:
            logger.error(f"Error tracking memory stability: {str(e)}")
            return {}

    def log_memory_leak_check(self, output: str, total_growth: float):
        """Log the result of a memory leak check (tracemalloc)."""
        try:
            self.metrics_history.setdefault('memory_leak_checks', []).append({
                'timestamp': datetime.now().isoformat(),
                'output': output,
                'total_growth_kb': total_growth / 1024
            })
            self.save_metrics_history()
            logger.info(f"Memory leak check logged: {total_growth/1024:.2f} KB growth")
        except Exception as e:
            logger.error(f"Error logging memory leak check: {str(e)}")

    def get_memory_leak_summary(self, window_hours: int = 24):
        """Summarize memory leak checks over a time window."""
        try:
            now = datetime.now()
            window_start = now - timedelta(hours=window_hours)
            checks = [c for c in self.metrics_history.get('memory_leak_checks', [])
                      if datetime.fromisoformat(c['timestamp']) >= window_start]
            if not checks:
                return {'count': 0, 'max_growth_kb': 0, 'mean_growth_kb': 0}
            growths = [c.get('total_growth_kb', 0) for c in checks]
            return {
                'count': len(checks),
                'max_growth_kb': max(growths),
                'mean_growth_kb': np.mean(growths)
            }
        except Exception as e:
            logger.error(f"Error summarizing memory leak checks: {str(e)}")
            return {'count': 0, 'max_growth_kb': 0, 'mean_growth_kb': 0}

    def log_recovery_event(self, success: bool, reason: str = None, error: str = None):
        """Log a recovery event with context."""
        try:
            self.metrics_history.setdefault('recovery_success', []).append({
                'timestamp': datetime.now().isoformat(),
                'value': 1 if success else 0,
                'reason': reason,
                'error': error
            })
            self.save_metrics_history()
            logger.info(f"Recovery event logged: {'success' if success else 'failure'} | Reason: {reason} | Error: {error}")
        except Exception as e:
            logger.error(f"Error logging recovery event: {str(e)}")

    def get_recovery_success_summary(self, window_hours: int = 24):
        """Summarize recovery success rate over a time window."""
        try:
            now = datetime.now()
            window_start = now - timedelta(hours=window_hours)
            events = [e for e in self.metrics_history.get('recovery_success', [])
                      if datetime.fromisoformat(e['timestamp']) >= window_start]
            if not events:
                return {'count': 0, 'success_rate': 0.0, 'failures': 0, 'reasons': []}
            successes = sum(1 for e in events if e['value'] == 1)
            failures = sum(1 for e in events if e['value'] == 0)
            reasons = [e.get('reason') for e in events if e.get('reason')]
            return {
                'count': len(events),
                'success_rate': successes / len(events) if events else 0.0,
                'failures': failures,
                'reasons': reasons
            }
        except Exception as e:
            logger.error(f"Error summarizing recovery success: {str(e)}")
            return {'count': 0, 'success_rate': 0.0, 'failures': 0, 'reasons': []}

def get_metrics_tracker() -> MetricsTracker:
    """Get the singleton instance of MetricsTracker."""
    if not hasattr(get_metrics_tracker, '_instance'):
        get_metrics_tracker._instance = MetricsTracker()
    return get_metrics_tracker._instance 