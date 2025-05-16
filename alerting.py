import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import json
from datetime import datetime
from logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

# Default thresholds
DEFAULT_THRESHOLDS = {
    'llm_latency_threshold': 5.0,  # seconds
    'embedding_latency_threshold': 2.0,  # seconds (default for node/agent)
    'node_agent_latency_threshold': 5.0,  # seconds (default for node/agent)
    'memory_usage_threshold': 80.0,  # percent
    'cpu_usage_threshold': 90.0,    # percent
    'gpu_usage_threshold': 90.0,    # percent
    'cache_hit_rate_threshold': 70.0, # percent
    'error_rate_threshold': 0.1,  # 10% error rate
    'consecutive_failures_threshold': 3
}

class AlertManager:
    def __init__(self, 
                 smtp_server: str = None,
                 smtp_port: int = None,
                 smtp_username: str = None,
                 smtp_password: str = None,
                 alert_email: str = None,
                 thresholds: Dict[str, float] = None):
        """Initialize the alert manager with SMTP settings and thresholds."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.alert_email = alert_email
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.consecutive_failures = {
            'llm': 0,
            'embedding': 0,
            'node_agent': 0
        }
        self.last_alert_time = {
            'llm': None,
            'embedding': None,
            'node_agent': None,
            'memory': None,
            'cpu': None,
            'gpu': None,
            'cache': None
        }
        self.alert_cooldown = 300  # 5 minutes between alerts for the same type

    def check_llm_call(self, latency: float, success: bool, model_name: str) -> bool:
        """Check if an LLM call should trigger an alert."""
        try:
            alerts = []
            
            # Check latency
            if latency > self.thresholds['llm_latency_threshold']:
                alerts.append(f"High latency: {latency:.2f}s (threshold: {self.thresholds['llm_latency_threshold']}s)")
            
            # Check consecutive failures
            if not success:
                self.consecutive_failures['llm'] += 1
                if self.consecutive_failures['llm'] >= self.thresholds['consecutive_failures_threshold']:
                    alerts.append(f"Consecutive failures: {self.consecutive_failures['llm']}")
            else:
                self.consecutive_failures['llm'] = 0
            
            # Send alert if needed
            if alerts and self._should_send_alert('llm'):
                self._send_alert(
                    subject=f"LLM Alert: {model_name}",
                    body="\n".join(alerts)
                )
                self.last_alert_time['llm'] = datetime.now()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking LLM call: {str(e)}")
            return False

    def check_embedding_call(self, latency: float, success: bool, model_name: str) -> bool:
        """Check if an embedding call should trigger an alert."""
        try:
            alerts = []
            
            # Check latency
            if latency > self.thresholds['embedding_latency_threshold']:
                alerts.append(f"High latency: {latency:.2f}s (threshold: {self.thresholds['embedding_latency_threshold']}s)")
            
            # Check consecutive failures
            if not success:
                self.consecutive_failures['embedding'] += 1
                if self.consecutive_failures['embedding'] >= self.thresholds['consecutive_failures_threshold']:
                    alerts.append(f"Consecutive failures: {self.consecutive_failures['embedding']}")
            else:
                self.consecutive_failures['embedding'] = 0
            
            # Send alert if needed
            if alerts and self._should_send_alert('embedding'):
                self._send_alert(
                    subject=f"Embedding Alert: {model_name}",
                    body="\n".join(alerts)
                )
                self.last_alert_time['embedding'] = datetime.now()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking embedding call: {str(e)}")
            return False

    def check_error_rate(self, total_calls: int, error_count: int, call_type: str) -> bool:
        """Check if error rate exceeds threshold."""
        try:
            if total_calls == 0:
                return False
            
            error_rate = error_count / total_calls
            if error_rate > self.thresholds['error_rate_threshold']:
                if self._should_send_alert(call_type):
                    self._send_alert(
                        subject=f"High Error Rate Alert: {call_type}",
                        body=f"Error rate: {error_rate:.1%} (threshold: {self.thresholds['error_rate_threshold']:.1%})"
                    )
                    self.last_alert_time[call_type] = datetime.now()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking error rate: {str(e)}")
            return False

    def check_node_agent_execution(self, duration: float, success: bool, name: str) -> bool:
        """Check if a node/agent execution should trigger an alert."""
        try:
            alerts = []
            # Check duration
            if duration > self.thresholds.get('node_agent_latency_threshold', 5.0):
                alerts.append(f"High execution time: {duration:.2f}s (threshold: {self.thresholds.get('node_agent_latency_threshold', 5.0)}s)")
            # Check consecutive failures
            if not success:
                self.consecutive_failures['node_agent'] += 1
                if self.consecutive_failures['node_agent'] >= self.thresholds['consecutive_failures_threshold']:
                    alerts.append(f"Consecutive failures: {self.consecutive_failures['node_agent']}")
            else:
                self.consecutive_failures['node_agent'] = 0
            # Send alert if needed
            if alerts and self._should_send_alert('node_agent'):
                self._send_alert(
                    subject=f"Node/Agent Alert: {name}",
                    body="\n".join(alerts)
                )
                self.last_alert_time['node_agent'] = datetime.now()
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking node/agent execution: {str(e)}")
            return False

    def check_resource_usage(self, memory: float = None, cpu: float = None, gpu: float = None) -> bool:
        """Check if memory, CPU, or GPU usage should trigger an alert."""
        try:
            alerts = []
            now = datetime.now()
            triggered = False
            if memory is not None and memory > self.thresholds['memory_usage_threshold']:
                if self._should_send_alert('memory'):
                    alerts.append(f"High memory usage: {memory:.2f}% (threshold: {self.thresholds['memory_usage_threshold']}%)")
                    self.last_alert_time['memory'] = now
                    triggered = True
            if cpu is not None and cpu > self.thresholds['cpu_usage_threshold']:
                if self._should_send_alert('cpu'):
                    alerts.append(f"High CPU usage: {cpu:.2f}% (threshold: {self.thresholds['cpu_usage_threshold']}%)")
                    self.last_alert_time['cpu'] = now
                    triggered = True
            if gpu is not None and gpu > self.thresholds['gpu_usage_threshold']:
                if self._should_send_alert('gpu'):
                    alerts.append(f"High GPU usage: {gpu:.2f}% (threshold: {self.thresholds['gpu_usage_threshold']}%)")
                    self.last_alert_time['gpu'] = now
                    triggered = True
            if alerts:
                self._send_alert(
                    subject="Resource Usage Alert",
                    body="\n".join(alerts)
                )
            return triggered
        except Exception as e:
            logger.error(f"Error checking resource usage: {str(e)}")
            return False

    def check_cache_hit_rate(self, cache_name: str, hit_rate: float) -> bool:
        """Check if cache hit rate is below threshold and alert."""
        try:
            if hit_rate < self.thresholds['cache_hit_rate_threshold']:
                if self._should_send_alert('cache'):
                    self._send_alert(
                        subject=f"Low Cache Hit Rate Alert: {cache_name}",
                        body=f"Cache hit rate for '{cache_name}' is {hit_rate:.2f}% (threshold: {self.thresholds['cache_hit_rate_threshold']}%)"
                    )
                    self.last_alert_time['cache'] = datetime.now()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking cache hit rate: {str(e)}")
            return False

    def _should_send_alert(self, alert_type: str) -> bool:
        """Check if enough time has passed since the last alert."""
        if self.last_alert_time[alert_type] is None:
            return True
        
        time_since_last = (datetime.now() - self.last_alert_time[alert_type]).total_seconds()
        return time_since_last >= self.alert_cooldown

    def _send_alert(self, subject: str, body: str):
        """Send an alert via email and log it persistently."""
        # Log to alerts.log
        try:
            with open('alerts.log', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} | {subject} | {body}\n")
        except Exception as e:
            logger.error(f"Error writing to alerts.log: {str(e)}")
        # Log to metrics_history.json
        try:
            from metrics_tracker import get_metrics_tracker
            tracker = get_metrics_tracker()
            if 'alerts' not in tracker.metrics_history:
                tracker.metrics_history['alerts'] = []
            tracker.metrics_history['alerts'].append({
                'timestamp': datetime.now().isoformat(),
                'subject': subject,
                'body': body
            })
            tracker.save_metrics_history()
        except Exception as e:
            logger.error(f"Error logging alert to metrics_history.json: {str(e)}")
        # Email alert (if configured)
        if not all([self.smtp_server, self.smtp_port, self.smtp_username, 
                   self.smtp_password, self.alert_email]):
            logger.warning("Email alert not sent: SMTP settings not configured")
            return
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Alert sent: {subject}")
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")

    def alert_critical_error(self, error_message: str, context: str = None, stack_trace: str = None) -> bool:
        """Send an alert for a critical error, including context and stack trace."""
        try:
            body = f"Critical error occurred:\n{error_message}"
            if context:
                body += f"\nContext: {context}"
            if stack_trace:
                body += f"\nStack trace:\n{stack_trace}"
            self._send_alert(
                subject="Critical Error Alert",
                body=body
            )
            self.last_alert_time['critical_error'] = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error sending critical error alert: {str(e)}")
            return False

def get_alert_manager() -> AlertManager:
    """Get the singleton instance of AlertManager."""
    if not hasattr(get_alert_manager, '_instance'):
        get_alert_manager._instance = AlertManager()
    return get_alert_manager._instance 