import unittest
from metrics_tracker import get_metrics_tracker

class TestCacheMetrics(unittest.TestCase):
    def setUp(self):
        self.metrics = get_metrics_tracker()
        self.metrics.metrics_history['cache_events'] = []
        self.metrics.metrics_history['cache_hit_rate'] = []
        self.metrics.save_metrics_history()

    def test_cache_hit_and_miss_logging(self):
        self.metrics.track_cache_event('test_cache', True)
        self.metrics.track_cache_event('test_cache', False)
        self.metrics.track_cache_event('test_cache', True)
        events = [e for e in self.metrics.metrics_history['cache_events'] if e['cache_name'] == 'test_cache']
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]['hit'], True)
        self.assertEqual(events[1]['hit'], False)
        self.assertEqual(events[2]['hit'], True)

    def test_cache_hit_rate_calculation(self):
        self.metrics.track_cache_event('test_cache', True)
        self.metrics.track_cache_event('test_cache', False)
        self.metrics.track_cache_event('test_cache', True)
        rates = self.metrics.get_cache_hit_rate('test_cache')
        self.assertTrue(len(rates) > 0)
        # The last rate should be 66.666...%
        self.assertAlmostEqual(rates[-1]['value'], 100.0 * 2 / 3, places=1)

    def test_cache_hit_rate_separate_caches(self):
        self.metrics.track_cache_event('cache_a', True)
        self.metrics.track_cache_event('cache_b', False)
        self.metrics.track_cache_event('cache_a', False)
        self.metrics.track_cache_event('cache_b', True)
        rates_a = self.metrics.get_cache_hit_rate('cache_a')
        rates_b = self.metrics.get_cache_hit_rate('cache_b')
        self.assertAlmostEqual(rates_a[-1]['value'], 50.0, places=1)
        self.assertAlmostEqual(rates_b[-1]['value'], 50.0, places=1)

if __name__ == '__main__':
    unittest.main() 