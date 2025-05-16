import unittest
from unittest.mock import Mock, patch, MagicMock, ANY
import torch
import psutil
from pathlib import Path
import time
import os
from model_loader import ModelLoader, get_model_loader
from metrics_tracker import get_metrics_tracker

class TestModelLoader(unittest.TestCase):
    def setUp(self):
        # Mock torch
        self.torch_patcher = patch('torch.set_num_threads')
        self.mock_torch = self.torch_patcher.start()
        
        # Mock psutil
        self.psutil_patcher = patch('psutil.Process')
        self.mock_psutil = self.psutil_patcher.start()
        self.mock_process = MagicMock()
        self.mock_process.memory_info.return_value = MagicMock(rss=1000000)
        self.mock_psutil.return_value = self.mock_process
        
        # Mock Path
        self.path_patcher = patch('pathlib.Path')
        self.mock_path = self.path_patcher.start()
        self.mock_path_instance = MagicMock()
        self.mock_path.return_value = self.mock_path_instance
        self.mock_path_instance.exists.return_value = True
        self.mock_path_instance.glob.return_value = [MagicMock(is_file=lambda: True, stat=lambda: MagicMock(st_size=1000))]
        
        # Mock metrics tracker
        self.metrics_patcher = patch('model_loader.get_metrics_tracker')
        self.mock_metrics = self.metrics_patcher.start()
        self.mock_metrics_instance = MagicMock()
        self.mock_metrics.return_value = self.mock_metrics_instance
        self.mock_metrics_instance.track_memory_usage.return_value = 0.0
        
        # Reset singleton instance
        ModelLoader._instance = None
        ModelLoader._model = None
        
        # Do not create instance here; create in each test as needed
        # self.loader = ModelLoader()
        
    def tearDown(self):
        self.torch_patcher.stop()
        self.psutil_patcher.stop()
        self.path_patcher.stop()
        self.metrics_patcher.stop()
        ModelLoader._instance = None
        ModelLoader._model = None
    
    def test_singleton_pattern(self):
        """Test that get_model_loader returns the same instance."""
        loader1 = get_model_loader()
        loader2 = get_model_loader()
        self.assertIs(loader1, loader2)
    
    def test_torch_configuration(self):
        """Test PyTorch thread configuration."""
        loader = ModelLoader()
        self.mock_torch.assert_called_once_with(2)
        self.assertEqual(os.environ.get('OMP_NUM_THREADS'), '2')
        self.mock_metrics_instance.track_startup_time.assert_called_once()
    
    def test_model_loading(self):
        """Test model loading with memory tracking."""
        with patch('model_loader.SentenceTransformer') as mock_transformer:
            ModelLoader._instance = None  # Reset after patching
            ModelLoader._model = None
            loader = ModelLoader()
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model
            
            model = loader.get_model()
            
            mock_transformer.assert_called_once_with('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
            mock_model.to.assert_called_once_with(torch.float16)
            self.mock_metrics_instance.track_memory_usage.assert_called()
            self.mock_metrics_instance.track_startup_time.assert_called()
    
    def test_embedding_generation(self):
        """Test embedding generation with query time tracking."""
        with patch('model_loader.SentenceTransformer') as mock_transformer:
            ModelLoader._instance = None  # Reset after patching
            ModelLoader._model = None
            loader = ModelLoader()
            mock_model = MagicMock()
            mock_model.encode.return_value = torch.tensor([1.0, 2.0, 3.0])
            mock_model.get_config_dict.return_value = {'model_name': 'mock-model'}
            mock_transformer.return_value = mock_model
            embedding = loader.get_embedding("test text")
            mock_model.encode.assert_called_once_with("test text", convert_to_tensor=True)
            self.mock_metrics_instance.track_embedding_call.assert_called_once()
            call_args = self.mock_metrics_instance.track_embedding_call.call_args[1]
            self.assertEqual(call_args['model_name'], 'mock-model')
            self.assertEqual(call_args['input_size'], len("test text"))
            self.assertTrue(call_args['success'])
            self.assertIsInstance(embedding, torch.Tensor)
    
    def test_cache_management(self):
        """Test cache size calculation."""
        loader = ModelLoader()
        
        # Create a mock for the cache directory
        mock_cache_dir = MagicMock()
        mock_cache_dir.exists.return_value = True
        
        # Create a mock for the file
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.stat.return_value = MagicMock(st_size=1000)
        
        # Set up the mock to return our file when glob is called
        mock_cache_dir.glob.return_value = [mock_file]
        
        # Create the chain: Path.home() / '.cache' / 'huggingface' -> mock_cache_dir
        mock_cache_base = MagicMock()
        mock_home = MagicMock()
        mock_home.__truediv__.side_effect = lambda other: mock_cache_base if other == '.cache' else None
        mock_cache_base.__truediv__.side_effect = lambda other: mock_cache_dir if other == 'huggingface' else None
        
        with patch('model_loader.Path.home', return_value=mock_home):
            size = loader.get_cache_size()
            print(f"\nDebug: mock_cache_dir.exists() called: {mock_cache_dir.exists.called}")
            print(f"Debug: mock_cache_dir.glob() called: {mock_cache_dir.glob.called}")
            print(f"Debug: mock_file.is_file() called: {mock_file.is_file.called}")
            print(f"Debug: mock_file.stat() called: {mock_file.stat.called}")
            self.assertEqual(size, 1000)
            # Verify the mock was used correctly
            mock_cache_dir.exists.assert_called_once()
            mock_cache_dir.glob.assert_called_once_with('**/*')
            mock_file.is_file.assert_called_once()
            mock_file.stat.assert_called_once()
    
    def test_cache_clearing(self):
        """Test cache clearing with memory tracking."""
        loader = ModelLoader()
        with patch('shutil.rmtree') as mock_rmtree:
            result = loader.clear_cache()
            mock_rmtree.assert_called_once()
            self.mock_metrics_instance.track_memory_usage.assert_called_once()
            self.assertTrue(result)
    
    def test_error_handling(self):
        """Test error handling with crash tracking."""
        with patch('model_loader.SentenceTransformer', side_effect=Exception("Test error")):
            ModelLoader._instance = None  # Reset after patching
            ModelLoader._model = None
            loader = ModelLoader()
            model = loader.get_model()
            self.assertIsNone(model)
            self.mock_metrics_instance.track_crash.assert_called_once()
    
    def test_progress_reporting(self):
        """Test progress reporting during model loading."""
        progress_values = []
        def progress_callback(progress):
            progress_values.append(progress)
        
        with patch('model_loader.SentenceTransformer') as mock_transformer:
            ModelLoader._instance = None  # Reset after patching
            ModelLoader._model = None
            loader = ModelLoader()
            loader.set_loading_progress_callback(progress_callback)
            mock_transformer.return_value = MagicMock()
            loader.get_model()
        
        self.assertEqual(progress_values, [0.0, 0.3, 0.6, 0.8, 1.0])
    
    def test_lazy_loading(self):
        """Test that model is not loaded until get_model is called."""
        loader = ModelLoader()
        self.assertIsNone(loader._model)
        with patch('model_loader.SentenceTransformer') as mock_st:
            ModelLoader._instance = None  # Reset after patching
            ModelLoader._model = None
            loader = ModelLoader()
            loader.get_model()
            mock_st.assert_called_once()
    
    def test_peak_memory_usage_tracking(self):
        tracker = get_metrics_tracker()
        # Simulate memory usage records
        tracker.metrics_history['memory_usage'] = [
            {'timestamp': '2024-01-01T00:00:00', 'value': 100.0},
            {'timestamp': '2024-01-01T00:01:00', 'value': 150.0},
            {'timestamp': '2024-01-01T00:02:00', 'value': 120.0}
        ]
        # Patch psutil.Process.memory_info to not have peak_wset (simulate Unix)
        with patch('psutil.Process') as mock_proc:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=123456789)
            delattr(mock_instance.memory_info.return_value, 'peak_wset') if hasattr(mock_instance.memory_info.return_value, 'peak_wset') else None
            mock_proc.return_value = mock_instance
            peak = tracker.track_peak_memory_usage()
            self.assertEqual(peak, 150.0)
        # Patch psutil.Process.memory_info to have peak_wset (simulate Windows)
        with patch('psutil.Process') as mock_proc:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=123456789, peak_wset=987654321)
            mock_proc.return_value = mock_instance
            peak = tracker.track_peak_memory_usage()
            self.assertAlmostEqual(peak, 941.90, places=1)  # 987654321 / 1024 / 1024
    
    def test_startup_time_tracking(self):
        """Test that startup time is tracked when ModelLoader is initialized."""
        # Reset singleton to ensure fresh instance
        ModelLoader._instance = None
        ModelLoader._model = None
        
        # Create new instance and verify startup time was tracked
        loader = ModelLoader()
        self.mock_metrics_instance.track_startup_time.assert_called_once()
        
        # Verify the call was made with a float value
        args, _ = self.mock_metrics_instance.track_startup_time.call_args
        self.assertIsInstance(args[0], float)
    
    def test_meta_tensor_handling(self):
        """Test that _ensure_weights_materialized correctly materializes meta tensors."""
        loader = ModelLoader()
        # Create a mock model with a parameter on 'meta' device
        mock_param = MagicMock()
        mock_param.device.type = 'meta'
        model = MagicMock()
        model.parameters.return_value = [mock_param]
        # Simulate to_empty returns the model itself
        model.to_empty.return_value = model
        # Call _ensure_weights_materialized
        result = loader._ensure_weights_materialized(model)
        # Verify that to_empty was called
        model.to_empty.assert_called_once()
        self.assertIs(result, model)
    
    def test_meta_tensor_warning_if_still_meta(self):
        """Test that a warning is logged if parameters remain on 'meta' after materialization."""
        with patch('model_loader.SentenceTransformer') as mock_transformer, \
             patch('model_loader.logger') as mock_logger:
            ModelLoader._instance = None
            ModelLoader._model = None
            loader = ModelLoader()
            # Create a mock model with a parameter on 'meta' device
            mock_model = MagicMock()
            param1 = MagicMock()
            param1.device = 'meta'
            param2 = MagicMock()
            param2.device = 'cpu'
            # After to_empty, param1 is still on meta
            mock_model.named_parameters.side_effect = [
                [('weight1', param1), ('weight2', param2)],  # Before materialization
                [('weight1', param1), ('weight2', param2)]   # After materialization
            ]
            mock_model.to_empty.return_value = mock_model
            mock_transformer.return_value = mock_model
            # Call get_model and check warning is logged
            loader.get_model(force_reload=True)
            mock_logger.warning.assert_any_call("Some parameters are still on 'meta' after materialization: ['weight1']")

    def test_model_instantiation_error(self):
        """Test error during model instantiation (invalid model name)."""
        with patch('model_loader.SentenceTransformer', side_effect=Exception("Model not found")), \
             patch('model_loader.logger') as mock_logger:
            ModelLoader._instance = None
            ModelLoader._model = None
            loader = ModelLoader()
            model = loader.get_model(force_reload=True)
            self.assertIsNone(model)
            mock_logger.error.assert_any_call("Error loading model: Model not found")
            self.mock_metrics_instance.track_crash.assert_called()

    def test_device_dtype_conversion_error(self):
        """Test error during device/dtype conversion (e.g., OOM, unsupported dtype)."""
        with patch('model_loader.SentenceTransformer') as mock_transformer, \
             patch('model_loader.logger') as mock_logger:
            ModelLoader._instance = None
            ModelLoader._model = None
            loader = ModelLoader()
            mock_model = MagicMock()
            # Simulate float16 conversion error
            def to_side_effect(arg):
                if arg == torch.float16:
                    raise RuntimeError("Unsupported dtype")
                return mock_model
            mock_model.to.side_effect = to_side_effect
            mock_model.named_parameters.return_value = []
            mock_transformer.return_value = mock_model
            model = loader.get_model(force_reload=True)
            mock_logger.error.assert_any_call("Error converting model to float16: Unsupported dtype")
            self.assertIs(model, mock_model)

    def test_meta_tensor_materialization_error(self):
        """Test error during meta tensor materialization."""
        with patch('model_loader.SentenceTransformer') as mock_transformer, \
             patch('model_loader.logger') as mock_logger:
            ModelLoader._instance = None
            ModelLoader._model = None
            loader = ModelLoader()
            mock_model = MagicMock()
            param = MagicMock()
            param.device = 'meta'
            mock_model.named_parameters.return_value = [('weight', param)]
            # Simulate to_empty error
            mock_model.to_empty.side_effect = Exception("Materialization failed")
            mock_transformer.return_value = mock_model
            model = loader.get_model(force_reload=True)
            mock_logger.error.assert_any_call("Error materializing model from meta: Materialization failed")
            self.mock_metrics_instance.track_crash.assert_called()
            self.assertIsNone(model)

if __name__ == '__main__':
    unittest.main() 