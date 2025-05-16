import unittest
import time
from health_checks import HealthCheckRegistry
from metrics_tracker import get_metrics_tracker

class TestUptimeDowntime(unittest.TestCase):
    def setUp(self):
        self.registry = HealthCheckRegistry()
        get_metrics_tracker().metrics_history['service_uptime'] = []
        get_metrics_tracker().metrics_history['service_downtime'] = []
        get_metrics_tracker().save_metrics_history()
        self.state = True

    def toggle_check(self):
        # Alternate between up and down
        self.state = not self.state
        return self.state

    def test_uptime_downtime_tracking(self):
        self.registry.register('test_service', self.toggle_check)
        # Simulate up -> down -> up
        self.state = True
        self.registry.last_status['test_service'] = {'healthy': True, 'timestamp': time.time() - 10}
        self.registry.run_all()  # Should go down
        time.sleep(0.1)
        self.registry.run_all()  # Should go up
        summary = self.registry.get_uptime_downtime_summary()
        self.assertIn('test_service', summary)
        # Both uptime and downtime should be > 0
        self.assertGreater(summary['test_service']['uptime'], 0)
        self.assertGreater(summary['test_service']['downtime'], 0)

if __name__ == '__main__':
    unittest.main() 