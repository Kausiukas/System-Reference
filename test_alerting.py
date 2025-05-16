import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from alerting import AlertManager, get_alert_manager

class TestAlertManager(unittest.TestCase):
    def setUp(self):
        # Reset singleton instance
        if hasattr(get_alert_manager, '_instance'):
            delattr(get_alert_manager, '_instance')
        
        # Create test instance with mock SMTP settings
        self.alert_manager = AlertManager(
            smtp_server='test.server',
            smtp_port=587,
            smtp_username='test@example.com',
            smtp_password='password',
            alert_email='alerts@example.com'
        )

    def test_llm_call_high_latency(self):
        """Test alerting on high LLM latency."""
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Test high latency
            result = self.alert_manager.check_llm_call(
                latency=6.0,  # Above 5.0 threshold
                success=True,
                model_name='test-model'
            )
            self.assertTrue(result)
            mock_send.assert_called_once()
            
            # Test normal latency
            mock_send.reset_mock()
            result = self.alert_manager.check_llm_call(
                latency=2.0,  # Below threshold
                success=True,
                model_name='test-model'
            )
            self.assertFalse(result)
            mock_send.assert_not_called()

    def test_llm_call_consecutive_failures(self):
        """Test alerting on consecutive LLM failures."""
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Simulate consecutive failures
            for _ in range(3):  # Hit threshold
                self.alert_manager.check_llm_call(
                    latency=1.0,
                    success=False,
                    model_name='test-model'
                )
            
            self.assertEqual(self.alert_manager.consecutive_failures['llm'], 3)
            self.assertEqual(mock_send.call_count, 1)
            
            # Test successful call resets counter
            self.alert_manager.check_llm_call(
                latency=1.0,
                success=True,
                model_name='test-model'
            )
            self.assertEqual(self.alert_manager.consecutive_failures['llm'], 0)

    def test_embedding_call_high_latency(self):
        """Test alerting on high embedding latency."""
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Test high latency
            result = self.alert_manager.check_embedding_call(
                latency=3.0,  # Above 2.0 threshold
                success=True,
                model_name='test-model'
            )
            self.assertTrue(result)
            mock_send.assert_called_once()
            
            # Test normal latency
            mock_send.reset_mock()
            result = self.alert_manager.check_embedding_call(
                latency=1.0,  # Below threshold
                success=True,
                model_name='test-model'
            )
            self.assertFalse(result)
            mock_send.assert_not_called()

    def test_embedding_call_consecutive_failures(self):
        """Test alerting on consecutive embedding failures."""
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Simulate consecutive failures
            for _ in range(3):  # Hit threshold
                self.alert_manager.check_embedding_call(
                    latency=1.0,
                    success=False,
                    model_name='test-model'
                )
            
            self.assertEqual(self.alert_manager.consecutive_failures['embedding'], 3)
            self.assertEqual(mock_send.call_count, 1)
            
            # Test successful call resets counter
            self.alert_manager.check_embedding_call(
                latency=1.0,
                success=True,
                model_name='test-model'
            )
            self.assertEqual(self.alert_manager.consecutive_failures['embedding'], 0)

    def test_error_rate_threshold(self):
        """Test alerting on high error rate."""
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Test high error rate
            result = self.alert_manager.check_error_rate(
                total_calls=100,
                error_count=15,  # 15% error rate
                call_type='llm'
            )
            self.assertTrue(result)
            mock_send.assert_called_once()
            
            # Test normal error rate
            mock_send.reset_mock()
            result = self.alert_manager.check_error_rate(
                total_calls=100,
                error_count=5,  # 5% error rate
                call_type='llm'
            )
            self.assertFalse(result)
            mock_send.assert_not_called()

    def test_alert_cooldown(self):
        """Test alert cooldown period."""
        with patch.object(self.alert_manager, '_send_alert') as mock_send:
            # Send first alert
            self.alert_manager.check_llm_call(
                latency=6.0,
                success=True,
                model_name='test-model'
            )
            self.assertEqual(mock_send.call_count, 1)
            
            # Try to send another alert immediately
            mock_send.reset_mock()
            self.alert_manager.check_llm_call(
                latency=6.0,
                success=True,
                model_name='test-model'
            )
            self.assertEqual(mock_send.call_count, 0)
            
            # Move time forward past cooldown
            self.alert_manager.last_alert_time['llm'] = datetime.now() - timedelta(minutes=6)
            self.alert_manager.check_llm_call(
                latency=6.0,
                success=True,
                model_name='test-model'
            )
            self.assertEqual(mock_send.call_count, 1)

if __name__ == '__main__':
    unittest.main() 