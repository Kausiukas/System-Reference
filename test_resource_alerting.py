import unittest
from unittest.mock import patch
from metrics_tracker import get_metrics_tracker
from alerting import AlertManager

class TestResourceAlerting(unittest.TestCase):
    def setUp(self):
        self.metrics = get_metrics_tracker()
        self.alert_manager = AlertManager()

    def test_log_cpu_usage(self):
        cpu = self.metrics.track_cpu_usage()
        self.assertIsInstance(cpu, float)
        logs = self.metrics.metrics_history['cpu_usage']
        self.assertTrue(len(logs) > 0)
        self.assertIn('value', logs[-1])

    def test_log_gpu_usage(self):
        # GPU may not be available, so just check for no exception
        try:
            gpu = self.metrics.track_gpu_usage()
            # If available, should be float or None
            self.assertTrue(gpu is None or isinstance(gpu, float))
        except Exception as e:
            self.fail(f"track_gpu_usage raised an exception: {e}")

    def test_alert_on_high_memory(self):
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            result = self.alert_manager.check_resource_usage(memory=85.0)
            self.assertTrue(result)
            mock_send.assert_called_once()

    def test_alert_on_high_cpu(self):
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            result = self.alert_manager.check_resource_usage(cpu=95.0)
            self.assertTrue(result)
            mock_send.assert_called_once()

    def test_alert_on_high_gpu(self):
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            result = self.alert_manager.check_resource_usage(gpu=95.0)
            self.assertTrue(result)
            mock_send.assert_called_once()

if __name__ == '__main__':
    unittest.main() 