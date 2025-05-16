import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime
from metrics_tracker import MetricsTracker, get_metrics_tracker
from model_loader import get_model_loader

class TestMetricsTracker(unittest.TestCase):
    def setUp(self):
        # Reset singleton instance
        if hasattr(get_metrics_tracker, '_instance'):
            delattr(get_metrics_tracker, '_instance')
        self.tracker = get_metrics_tracker()
        self.tracker.metrics_history = {
            'llm_calls': [],
            'embedding_calls': [],
            'node_executions': [],
            'cache_events': [],
            'cache_hit_rate': []
        }

    def test_track_llm_call_success(self):
        """Test tracking successful LLM call."""
        model_name = "test-model"
        input_size = 100
        latency = 0.5
        success = True
        
        self.tracker.track_llm_call(model_name, input_size, latency, success)
        
        self.assertEqual(len(self.tracker.metrics_history['llm_calls']), 1)
        call = self.tracker.metrics_history['llm_calls'][0]
        self.assertEqual(call['model_name'], model_name)
        self.assertEqual(call['input_size'], input_size)
        self.assertEqual(call['latency'], latency)
        self.assertEqual(call['success'], success)
        self.assertIsNone(call['error'])
        self.assertTrue('timestamp' in call)

    def test_track_llm_call_failure(self):
        """Test tracking failed LLM call."""
        model_name = "test-model"
        input_size = 100
        latency = 0.5
        success = False
        error = "Test error"
        
        self.tracker.track_llm_call(model_name, input_size, latency, success, error)
        
        self.assertEqual(len(self.tracker.metrics_history['llm_calls']), 1)
        call = self.tracker.metrics_history['llm_calls'][0]
        self.assertEqual(call['model_name'], model_name)
        self.assertEqual(call['input_size'], input_size)
        self.assertEqual(call['latency'], latency)
        self.assertEqual(call['success'], success)
        self.assertEqual(call['error'], error)

    def test_track_embedding_call_success(self):
        """Test tracking successful embedding call."""
        model_name = "test-model"
        input_size = 100
        latency = 0.5
        success = True
        
        self.tracker.track_embedding_call(model_name, input_size, latency, success)
        
        self.assertEqual(len(self.tracker.metrics_history['embedding_calls']), 1)
        call = self.tracker.metrics_history['embedding_calls'][0]
        self.assertEqual(call['model_name'], model_name)
        self.assertEqual(call['input_size'], input_size)
        self.assertEqual(call['latency'], latency)
        self.assertEqual(call['success'], success)
        self.assertIsNone(call['error'])
        self.assertTrue('timestamp' in call)

    def test_track_embedding_call_failure(self):
        """Test tracking failed embedding call."""
        model_name = "test-model"
        input_size = 100
        latency = 0.5
        success = False
        error = "Test error"
        
        self.tracker.track_embedding_call(model_name, input_size, latency, success, error)
        
        self.assertEqual(len(self.tracker.metrics_history['embedding_calls']), 1)
        call = self.tracker.metrics_history['embedding_calls'][0]
        self.assertEqual(call['model_name'], model_name)
        self.assertEqual(call['input_size'], input_size)
        self.assertEqual(call['latency'], latency)
        self.assertEqual(call['success'], success)
        self.assertEqual(call['error'], error)

    def test_get_llm_metrics_summary(self):
        """Test getting LLM metrics summary."""
        # Add some test data
        self.tracker.metrics_history['llm_calls'] = [
            {'timestamp': datetime.now().isoformat(), 'model_name': 'test', 'input_size': 100, 'latency': 0.5, 'success': True},
            {'timestamp': datetime.now().isoformat(), 'model_name': 'test', 'input_size': 200, 'latency': 0.7, 'success': True},
            {'timestamp': datetime.now().isoformat(), 'model_name': 'test', 'input_size': 150, 'latency': 0.6, 'success': False, 'error': 'test error'}
        ]
        
        summary = self.tracker.get_llm_metrics_summary()
        
        self.assertEqual(summary['total_calls'], 3)
        self.assertAlmostEqual(summary['success_rate'], 2/3)
        self.assertAlmostEqual(summary['avg_latency'], 0.6)
        self.assertAlmostEqual(summary['avg_input_size'], 150)
        self.assertEqual(summary['error_count'], 1)

    def test_get_embedding_metrics_summary(self):
        """Test getting embedding metrics summary."""
        # Add some test data
        self.tracker.metrics_history['embedding_calls'] = [
            {'timestamp': datetime.now().isoformat(), 'model_name': 'test', 'input_size': 100, 'latency': 0.5, 'success': True},
            {'timestamp': datetime.now().isoformat(), 'model_name': 'test', 'input_size': 200, 'latency': 0.7, 'success': True},
            {'timestamp': datetime.now().isoformat(), 'model_name': 'test', 'input_size': 150, 'latency': 0.6, 'success': False, 'error': 'test error'}
        ]
        
        summary = self.tracker.get_embedding_metrics_summary()
        
        self.assertEqual(summary['total_calls'], 3)
        self.assertAlmostEqual(summary['success_rate'], 2/3)
        self.assertAlmostEqual(summary['avg_latency'], 0.6)
        self.assertAlmostEqual(summary['avg_input_size'], 150)
        self.assertEqual(summary['error_count'], 1)

    def test_get_llm_throughput(self):
        # Add LLM calls with timestamps in the last 60 seconds
        now = datetime.now()
        self.tracker.metrics_history['llm_calls'] = [
            {'timestamp': (now).isoformat(), 'model_name': 'test', 'input_size': 100, 'latency': 0.5, 'success': True},
            {'timestamp': (now).isoformat(), 'model_name': 'test', 'input_size': 200, 'latency': 0.7, 'success': True},
            {'timestamp': (now).isoformat(), 'model_name': 'test', 'input_size': 150, 'latency': 0.6, 'success': False, 'error': 'test error'}
        ]
        throughput = self.tracker.get_llm_throughput(window_seconds=60)
        self.assertAlmostEqual(throughput, 3.0)

    def test_get_embeddings_batch(self):
        loader = get_model_loader()
        # Patch get_model to return a mock model with encode
        class MockModel:
            def get_config_dict(self):
                return {'model_name': 'mock-model'}
            def encode(self, texts, convert_to_tensor=True):
                return [f"embedding_{i}" for i in range(len(texts))]
        loader._model = MockModel()
        texts = ["hello", "world", "test"]
        embeddings = loader.get_embeddings_batch(texts)
        self.assertEqual(len(embeddings), 3)
        # Check that metrics were tracked
        tracker = get_metrics_tracker()
        calls = tracker.metrics_history['embedding_calls'][-3:]
        self.assertEqual(len(calls), 3)
        for call in calls:
            self.assertEqual(call['model_name'], 'mock-model')
            self.assertTrue(call['success'])

    def test_log_node_execution_and_traversal_rate(self):
        tracker = get_metrics_tracker()
        now = time.time()
        tracker.metrics_history['node_executions'] = []
        tracker.log_node_execution('nodeA', now-10, now-9, 'success')
        tracker.log_node_execution('nodeB', now-8, now-7, 'success')
        tracker.log_node_execution('nodeC', now-6, now-5, 'failure', error='err')
        executions = tracker.metrics_history['node_executions']
        self.assertEqual(len(executions), 3)
        self.assertEqual(executions[0]['node_name'], 'nodeA')
        self.assertEqual(executions[2]['status'], 'failure')
        self.assertEqual(executions[2]['error'], 'err')
        # Traversal rate (all in last 60s)
        rate = tracker.get_graph_traversal_rate(window_seconds=60)
        self.assertAlmostEqual(rate, 3.0)

    def test_track_llm_call_token_usage(self):
        model_name = "test-model"
        input_size = 100
        latency = 0.5
        success = True
        token_usage = 42
        self.tracker.track_llm_call(model_name, input_size, latency, success, token_usage=token_usage)
        call = self.tracker.metrics_history['llm_calls'][-1]
        self.assertEqual(call['token_usage'], token_usage)
        # Add another call with different token usage
        self.tracker.track_llm_call(model_name, input_size, latency, success, token_usage=58)
        summary = self.tracker.get_llm_metrics_summary()
        self.assertAlmostEqual(summary['avg_token_usage'], 50.0)

    def test_llm_response_cache_hit_miss(self):
        tracker = get_metrics_tracker()
        tracker.metrics_history['cache_events'] = []
        tracker.metrics_history['cache_hit_rate'] = []
        # Simulate 2 hits, 1 miss
        tracker.track_cache_event('llm_response', True)
        tracker.track_cache_event('llm_response', False)
        tracker.track_cache_event('llm_response', True)
        rates = tracker.get_cache_hit_rate('llm_response')
        self.assertTrue(len(rates) > 0)
        self.assertAlmostEqual(rates[-1]['value'], 100.0 * 2 / 3, places=1)

if __name__ == '__main__':
    unittest.main() 