import os
import torch
import time
from typing import Optional, Callable
from sentence_transformers import SentenceTransformer
from pathlib import Path
import shutil
import psutil
from tqdm import tqdm
from metrics_tracker import get_metrics_tracker
from alerting import get_alert_manager
from logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

class ModelLoader:
    _instance = None
    _model = None
    _loading_progress: Optional[Callable] = None
    _start_time: float = 0.0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance._start_time = time.time()
            cls._instance._configure_torch()
        return cls._instance
    
    def _configure_torch(self):
        """Configure PyTorch for optimal memory usage."""
        try:
            # Limit number of threads
            torch.set_num_threads(2)
            os.environ['OMP_NUM_THREADS'] = '2'
            logger.info("PyTorch configured with 2 threads")
            
            # Track startup time
            metrics = get_metrics_tracker()
            metrics.track_startup_time(self._start_time)
        except Exception as e:
            logger.error(f"Error configuring PyTorch: {str(e)}")
            get_metrics_tracker().track_crash()
    
    def set_loading_progress_callback(self, callback: Callable[[float], None]):
        """Set a callback function to report loading progress."""
        self._loading_progress = callback
    
    def _report_progress(self, progress: float):
        """Report loading progress if callback is set."""
        if self._loading_progress:
            self._loading_progress(progress)
    
    def get_cache_size(self) -> int:
        """Get the size of the HuggingFace cache."""
        try:
            cache_dir = Path.home() / '.cache' / 'huggingface'
            if not cache_dir.exists():
                return 0
            
            total_size = 0
            for path in cache_dir.glob('**/*'):
                if path.is_file():
                    total_size += path.stat().st_size
            return total_size
        except Exception as e:
            logger.error(f"Error getting cache size: {str(e)}")
            return 0
    
    def clear_cache(self) -> bool:
        """Clear the HuggingFace cache if it's too large."""
        try:
            cache_dir = Path.home() / '.cache' / 'huggingface'
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                logger.info("Cache cleared successfully")
                get_metrics_tracker().track_memory_usage()  # Track memory after cache clear
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def _ensure_weights_materialized(self, model):
        """Ensure all model weights are materialized (not on 'meta' device)."""
        if any(p.device.type == 'meta' for p in model.parameters()):
            model.to_empty()
        return model

    def _load_model(self, model_name: str, device: str = 'cpu', dtype: torch.dtype = torch.float16) -> torch.nn.Module:
        try:
            model = SentenceTransformer(model_name, torch_dtype=dtype)
            model = self._ensure_weights_materialized(model)
            model = model.to(device)
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            raise
    
    def get_model(self, force_reload: bool = False) -> Optional[SentenceTransformer]:
        """Load the model with optimizations, handling meta tensors and device transitions."""
        try:
            if self._model is None or force_reload:
                logger.info("Loading model...")
                self._report_progress(0.0)
                # Track memory before loading
                metrics = get_metrics_tracker()
                memory_before = metrics.track_memory_usage()
                # Initialize model with basic configuration
                self._model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
                self._report_progress(0.3)
                # --- Meta tensor/device handling ---
                import torch
                meta_found = False
                for name, param in self._model.named_parameters():
                    if hasattr(param, 'device') and str(param.device) == 'meta':
                        meta_found = True
                        logger.warning(f"Parameter {name} is on 'meta' device. Materializing weights on CPU using to_empty().")
                        break
                if meta_found:
                    try:
                        # Use to_empty to materialize weights before any device/dtype conversion
                        self._model = self._model.to_empty(device=torch.device('cpu'))
                        logger.info("Model weights materialized from meta to CPU using to_empty().")
                        # Verify all parameters are now materialized
                        still_meta = [name for name, param in self._model.named_parameters() if hasattr(param, 'device') and str(param.device) == 'meta']
                        if still_meta:
                            logger.warning(f"Some parameters are still on 'meta' after materialization: {still_meta}")
                        else:
                            logger.info("All model parameters are now materialized on a real device.")
                    except Exception as e:
                        logger.error(f"Error materializing model from meta: {str(e)}")
                        get_metrics_tracker().track_crash()
                        return None
                # --- End meta tensor handling ---
                # Convert to float16 to reduce memory usage
                try:
                    self._model.to(torch.float16)
                except Exception as e:
                    logger.error(f"Error converting model to float16: {str(e)}")
                self._report_progress(0.6)
                # Initialize model components progressively
                if hasattr(self._model, 'tokenizer'):
                    self._model.tokenizer.model_max_length = 256
                self._report_progress(0.8)
                if hasattr(self._model, 'max_seq_length'):
                    self._model.max_seq_length = 256
                self._report_progress(1.0)
                # Track memory after loading
                memory_after = metrics.track_memory_usage()
                memory_used = memory_after - memory_before
                logger.info(f"Model loaded successfully. Memory used: {memory_used:.2f} MB")
            return self._model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            get_metrics_tracker().track_crash()
            return None
    
    def get_embedding(self, text: str) -> Optional[torch.Tensor]:
        """Generate embeddings for input text."""
        try:
            start_time = time.time()
            model = self.get_model()
            if model is None:
                return None
            
            # Track input size
            input_size = len(text)
            
            try:
                embedding = model.encode(text, convert_to_tensor=True)
                latency = time.time() - start_time
                
                # Track successful embedding call
                get_metrics_tracker().track_embedding_call(
                    model_name=model.get_config_dict().get('model_name', 'unknown'),
                    input_size=input_size,
                    latency=latency,
                    success=True
                )
                
                # Check for alerts
                get_alert_manager().check_embedding_call(
                    latency=latency,
                    success=True,
                    model_name=model.get_config_dict().get('model_name', 'unknown')
                )
                
                return embedding
            except Exception as e:
                latency = time.time() - start_time
                # Track failed embedding call
                get_metrics_tracker().track_embedding_call(
                    model_name=model.get_config_dict().get('model_name', 'unknown'),
                    input_size=input_size,
                    latency=latency,
                    success=False,
                    error=str(e)
                )
                
                # Check for alerts
                get_alert_manager().check_embedding_call(
                    latency=latency,
                    success=False,
                    model_name=model.get_config_dict().get('model_name', 'unknown')
                )
                raise
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            get_metrics_tracker().track_crash()
            return None
    
    def get_embeddings_batch(self, texts: list) -> list:
        """Generate embeddings for a batch of input texts."""
        results = []
        start_time = time.time()
        model = self.get_model()
        if model is None:
            return [None] * len(texts)
        input_sizes = [len(t) for t in texts]
        try:
            embeddings = model.encode(texts, convert_to_tensor=True)
            latency = time.time() - start_time
            for i, text in enumerate(texts):
                get_metrics_tracker().track_embedding_call(
                    model_name=model.get_config_dict().get('model_name', 'unknown'),
                    input_size=input_sizes[i],
                    latency=latency / len(texts),
                    success=True
                )
                get_alert_manager().check_embedding_call(
                    latency=latency / len(texts),
                    success=True,
                    model_name=model.get_config_dict().get('model_name', 'unknown')
                )
            return embeddings
        except Exception as e:
            latency = time.time() - start_time
            for i, text in enumerate(texts):
                get_metrics_tracker().track_embedding_call(
                    model_name=model.get_config_dict().get('model_name', 'unknown'),
                    input_size=input_sizes[i],
                    latency=latency / len(texts),
                    success=False,
                    error=str(e)
                )
                get_alert_manager().check_embedding_call(
                    latency=latency / len(texts),
                    success=False,
                    model_name=model.get_config_dict().get('model_name', 'unknown')
                )
            return [None] * len(texts)

def get_model_loader() -> ModelLoader:
    """Get the singleton instance of ModelLoader."""
    return ModelLoader()

# Example usage with Streamlit
"""
import streamlit as st

@st.cache_resource
def get_embedding_model():
    loader = get_model_loader()
    
    # Add progress bar for model loading
    progress_bar = st.progress(0)
    loader.set_loading_progress_callback(lambda p: progress_bar.progress(p))
    
    return loader.get_model()

# In your Streamlit app:
model = get_embedding_model()
""" 