import unittest
from unittest.mock import patch
from alerting import AlertManager

class TestCacheAlerting(unittest.TestCase):
    def setUp(self):
        self.alert_manager = AlertManager()

    def test_alert_on_low_cache_hit_rate(self):
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Below threshold (default 70%)
            result = self.alert_manager.check_cache_hit_rate('test_cache', 60.0)
            self.assertTrue(result)
            mock_send.assert_called_once()

    def test_no_alert_on_high_cache_hit_rate(self):
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Above threshold
            result = self.alert_manager.check_cache_hit_rate('test_cache', 80.0)
            self.assertFalse(result)
            mock_send.assert_not_called()

if __name__ == '__main__':
    unittest.main() 