import unittest
from unittest.mock import patch
from metrics_tracker import get_metrics_tracker

class TestCriticalErrorAlerting(unittest.TestCase):
    def setUp(self):
        self.metrics = get_metrics_tracker()

    def test_log_error_with_context(self):
        try:
            raise ValueError("Test error")
        except Exception as e:
            self.metrics.log_error_with_context(e, function="test_func", params={"a": 1, "b": 2}, critical=False)
        # Check that no exception is raised and log file is written (not asserting log content here)

    def test_alert_on_critical_error(self):
        with patch("alerting.AlertManager._send_alert") as mock_send:
            try:
                raise RuntimeError("Critical test error")
            except Exception as e:
                self.metrics.log_error_with_context(e, function="critical_func", params={"x": 42}, critical=True)
            mock_send.assert_called_once()

if __name__ == '__main__':
    unittest.main() 