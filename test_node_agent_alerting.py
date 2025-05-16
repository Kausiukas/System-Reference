import unittest
from unittest.mock import patch
import time
from metrics_tracker import get_metrics_tracker
from alerting import AlertManager

class TestNodeAgentExecution(unittest.TestCase):
    def setUp(self):
        self.metrics = get_metrics_tracker()
        self.metrics.metrics_history['node_agent_executions'] = []
        self.metrics.save_metrics_history()
        self.alert_manager = AlertManager()

    def test_log_successful_execution(self):
        start = time.time()
        time.sleep(0.01)
        end = time.time()
        self.metrics.track_node_agent_execution(
            name='test_node',
            start_time=start,
            end_time=end,
            status='success',
            error=None
        )
        logs = self.metrics.get_node_agent_executions('test_node')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['status'], 'success')
        self.assertIsNone(logs[0]['error'])

    def test_log_failed_execution(self):
        start = time.time()
        time.sleep(0.01)
        end = time.time()
        self.metrics.track_node_agent_execution(
            name='test_node',
            start_time=start,
            end_time=end,
            status='failure',
            error='Some error'
        )
        logs = self.metrics.get_node_agent_executions('test_node')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['status'], 'failure')
        self.assertEqual(logs[0]['error'], 'Some error')

    def test_alert_on_high_duration(self):
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Duration above threshold (default 5s)
            result = self.alert_manager.check_node_agent_execution(
                duration=6.0,
                success=True,
                name='slow_node'
            )
            self.assertTrue(result)
            mock_send.assert_called_once()

    def test_alert_on_consecutive_failures(self):
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Simulate consecutive failures (threshold 3)
            for _ in range(3):
                self.alert_manager.check_node_agent_execution(
                    duration=1.0,
                    success=False,
                    name='fail_node'
                )
            self.assertEqual(self.alert_manager.consecutive_failures['node_agent'], 3)
            self.assertEqual(mock_send.call_count, 1)
            # Success resets counter
            self.alert_manager.check_node_agent_execution(
                duration=1.0,
                success=True,
                name='fail_node'
            )
            self.assertEqual(self.alert_manager.consecutive_failures['node_agent'], 0)

if __name__ == '__main__':
    unittest.main() 