import unittest
from unittest.mock import patch
from health_checks import register_health_check, run_all_health_checks
from metrics_tracker import get_metrics_tracker

class TestHealthChecks(unittest.TestCase):
    def setUp(self):
        # Clear health checks and logs
        get_metrics_tracker().metrics_history['health_checks'] = []
        get_metrics_tracker().save_metrics_history()
        # Register test health checks
        self.healthy_called = False
        self.unhealthy_called = False
        register_health_check('healthy_service', self.healthy_check)
        register_health_check('unhealthy_service', self.unhealthy_check)

    def healthy_check(self):
        self.healthy_called = True
        return True

    def unhealthy_check(self):
        self.unhealthy_called = True
        return False

    def test_health_check_logging_and_alerting(self):
        with patch('alerting.AlertManager._send_alert') as mock_send:
            results = run_all_health_checks()
            self.assertTrue(self.healthy_called)
            self.assertTrue(self.unhealthy_called)
            self.assertIn('healthy_service', results)
            self.assertIn('unhealthy_service', results)
            self.assertTrue(results['healthy_service']['healthy'])
            self.assertFalse(results['unhealthy_service']['healthy'])
            # Should alert on unhealthy
            mock_send.assert_called_once()
            # Check log
            logs = [h for h in get_metrics_tracker().metrics_history['health_checks'] if h['service'] == 'unhealthy_service']
            self.assertTrue(len(logs) > 0)
            self.assertFalse(logs[-1]['healthy'])

if __name__ == '__main__':
    unittest.main() 