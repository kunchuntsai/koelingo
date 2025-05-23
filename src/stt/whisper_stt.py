"""
Whisper STT module for Japanese speech recognition.
"""

import os
import time
import threading
import numpy as np
import whisper  # This is openai-whisper package
from typing import Optional, Callable, List, Dict, Any, Tuple
import queue

# Try to import CTranslate2 Whisper for better performance
try:
    import ctranslate2
    import faster_whisper
    CTRANSLATE2_AVAILABLE = True
except ImportError:
    CTRANSLATE2_AVAILABLE = False
    print("CTranslate2 not available. Using standard Whisper.")

# Make sure we're using the right package
if not hasattr(whisper, 'load_model'):
    raise ImportError("OpenAI Whisper model not found. Please install with: pip install git+https://github.com/openai/whisper.git")

class WhisperSTT:
    """Speech-to-Text implementation using Whisper for Japanese recognition."""

    def __init__(
        self,
        model_size: str = "tiny",
        device: str = "cpu",
        compute_type: str = "float32",
        language: str = "ja",
        use_ctranslate2: bool = True,
    ):
        """
        Initialize the Whisper speech recognition module.

        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to run inference on ('cpu' or 'cuda')
            compute_type: Computation type ('float32', 'float16', or 'int8')
            language: The language to recognize (default: 'ja' for Japanese)
            use_ctranslate2: Whether to use CTranslate2 optimized implementation if available
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.use_ctranslate2 = use_ctranslate2 and CTRANSLATE2_AVAILABLE

        # Flag to track if the model is loaded
        self.is_loaded = False
        self.model = None
        self.ct_model = None  # CTranslate2 model

        # Threading resources
        self._processing_thread = None
        self._is_processing = False
        self._continuous_thread = None
        self._continuous_active = False
        self._audio_queue = queue.Queue()

        # Callback for when transcription is ready
        self.transcription_callback = None

        # Load model automatically
        self.load_model()

    def load_model(self) -> bool:
        """
        Load the Whisper model.

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            print(f"Loading Whisper model: {self.model_size} (CTranslate2: {self.use_ctranslate2})")
            
            if self.use_ctranslate2:
                # Use CTranslate2 implementation for better performance
                self.ct_model = faster_whisper.WhisperModel(
                    model_size_or_path=self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                self.is_loaded = True
                print("Whisper model loaded successfully with CTranslate2")
            else:
                # Use standard Whisper implementation
                self.model = whisper.load_model(self.model_size, device=self.device)
                self.is_loaded = True
                print("Whisper model loaded successfully")
                
            return True
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.is_loaded = False
            return False

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        self.stop_continuous_processing()
        
        if self.model:
            # In PyTorch-based models like Whisper, we can help free memory by
            # explicitly removing references and running garbage collection
            import gc

            del self.model
            self.model = None
            gc.collect()

            if self.device == "cuda":
                import torch
                torch.cuda.empty_cache()
        
        if self.ct_model:
            del self.ct_model
            self.ct_model = None
            
            import gc
            gc.collect()

        self.is_loaded = False

    def transcribe_audio(
        self,
        audio_data: np.ndarray,
        callback: Optional[Callable[[str, float], None]] = None
    ) -> None:
        """
        Transcribe audio data asynchronously.

        Args:
            audio_data: Audio data as numpy array (16kHz, mono, float32)
            callback: Callback function to receive transcription results and confidence
        """
        if callback:
            self.transcription_callback = callback

        # Start a new thread for processing to avoid blocking the UI
        self._processing_thread = threading.Thread(
            target=self._process_audio,
            args=(audio_data,)
        )
        self._processing_thread.daemon = True
        self._processing_thread.start()

    def start_continuous_processing(
        self,
        callback: Optional[Callable[[str, float], None]] = None
    ) -> bool:
        """
        Start continuous audio processing mode.
        
        Args:
            callback: Callback function to receive transcription results and confidence
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self._continuous_active:
            return True  # Already running
            
        if callback:
            self.transcription_callback = callback
            
        # Clear any existing audio queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
                
        self._continuous_active = True
        
        # Start continuous processing thread
        self._continuous_thread = threading.Thread(
            target=self._continuous_processing_loop
        )
        self._continuous_thread.daemon = True
        self._continuous_thread.start()
        
        return True
        
    def stop_continuous_processing(self) -> None:
        """Stop continuous audio processing."""
        self._continuous_active = False
        
        if self._continuous_thread and self._continuous_thread.is_alive():
            # Wait for thread to finish
            self._continuous_thread.join(timeout=2.0)
            
    def process_audio_chunk(self, audio_chunk: np.ndarray) -> None:
        """
        Process an audio chunk in continuous mode.
        
        Args:
            audio_chunk: Audio data chunk as numpy array
        """
        if not self._continuous_active:
            self.start_continuous_processing()
            
        # Add to processing queue
        self._audio_queue.put(audio_chunk)
        
    def _continuous_processing_loop(self) -> None:
        """Main loop for continuous audio processing."""
        print("Starting continuous processing loop")
        
        while self._continuous_active:
            try:
                # Get audio chunk from queue, with timeout
                audio_chunk = self._audio_queue.get(timeout=0.5)
                
                # Process the chunk
                self._is_processing = True
                
                try:
                    # Prepare audio data
                    if audio_chunk.dtype != np.float32:
                        if audio_chunk.dtype == np.int16:
                            audio_chunk = audio_chunk.astype(np.float32) / 32768.0
                        else:
                            audio_chunk = audio_chunk.astype(np.float32)
                            max_value = max(np.max(np.abs(audio_chunk)), 1e-10)
                            audio_chunk /= max_value
                    
                    # Set options for Japanese recognition
                    if self.use_ctranslate2 and self.ct_model:
                        # Process with CTranslate2 
                        segments, info = self.ct_model.transcribe(
                            audio_chunk,
                            language=self.language,
                            task="transcribe",
                            beam_size=5
                        )
                        
                        # Extract text from segments
                        transcription = ""
                        segment_list = list(segments)  # Convert generator to list
                        for segment in segment_list:
                            transcription += segment.text
                        
                        # Estimate confidence
                        if segment_list:
                            avg_prob = sum(s.avg_logprob for s in segment_list) / len(segment_list)
                            # Convert log probability to confidence score (0-1)
                            confidence = min(1.0, max(0.0, 1.0 + avg_prob/10))
                        else:
                            confidence = 0.7  # Default confidence
                    else:
                        # Process with standard Whisper
                        options = {
                            "language": self.language,
                            "task": "transcribe"
                        }
                        
                        result = self.model.transcribe(audio_chunk, **options)
                        transcription = result["text"].strip()
                        confidence = self._estimate_confidence(result)
                    
                    if transcription:
                        # Call the callback with the transcription result
                        if self.transcription_callback:
                            self.transcription_callback(transcription, confidence)
                            
                except Exception as e:
                    print(f"Error processing audio chunk: {e}")
                
                finally:
                    self._is_processing = False
                    self._audio_queue.task_done()
                    
            except queue.Empty:
                # No data in queue, just continue
                pass
                
            except Exception as e:
                print(f"Error in continuous processing loop: {e}")
                
        print("Continuous processing loop stopped")

    def _process_audio(self, audio_data: np.ndarray) -> None:
        """
        Process audio data in a background thread.

        Args:
            audio_data: Audio data as numpy array (16kHz, mono, float32)
        """
        if not self.is_loaded:
            if not self.load_model():
                return

        self._is_processing = True

        try:
            # Normalize audio if needed (ensuring range is between -1 and 1)
            if audio_data.dtype != np.float32:
                if audio_data.dtype == np.int16:
                    # Convert 16-bit PCM to float32 in range [-1, 1]
                    audio_data = audio_data.astype(np.float32) / 32768.0
                else:
                    # Generic normalization for other types
                    audio_data = audio_data.astype(np.float32)
                    max_value = max(np.max(np.abs(audio_data)), 1e-10)
                    audio_data /= max_value

            # Perform transcription
            start_time = time.time()

            # Process with the appropriate model
            if self.use_ctranslate2 and self.ct_model:
                # Set options for Japanese recognition with CTranslate2
                segments, info = self.ct_model.transcribe(
                    audio_data,
                    language=self.language,
                    task="transcribe",
                    beam_size=5
                )
                
                # Extract text from segments
                transcription = ""
                segment_list = list(segments)  # Convert generator to list
                for segment in segment_list:
                    transcription += segment.text
                
                # Estimate confidence
                if segment_list:
                    avg_prob = sum(s.avg_logprob for s in segment_list) / len(segment_list)
                    # Convert log probability to confidence score (0-1)
                    confidence = min(1.0, max(0.0, 1.0 + avg_prob/10))
                else:
                    confidence = 0.7  # Default confidence
            else:
                # Set options for Japanese recognition with standard Whisper
                options = {
                    "language": self.language,
                    "task": "transcribe"
                }

                # Transcribe audio
                result = self.model.transcribe(audio_data, **options)

                # Extract text and compute a confidence score
                transcription = result["text"].strip()
                confidence = self._estimate_confidence(result)

            end_time = time.time()
            processing_time = end_time - start_time
            print(f"Audio processed in {processing_time:.2f} seconds, confidence: {confidence:.2f}")

            # Call the callback with the transcription result and confidence
            if self.transcription_callback:
                self.transcription_callback(transcription, confidence)

        except Exception as e:
            print(f"Error during transcription: {e}")
        finally:
            self._is_processing = False

    def _estimate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Estimate confidence score from Whisper result.

        Note: Whisper doesn't provide direct confidence scores, so this is a heuristic.

        Args:
            result: The Whisper transcription result

        Returns:
            float: Estimated confidence score between 0.0 and 1.0
        """
        # Extract segments if available
        if "segments" in result and result["segments"]:
            # Compute average segment-level confidence (no_speech_prob inverse)
            total_conf = 0.0
            for segment in result["segments"]:
                # Lower no_speech_prob means higher confidence that this is speech
                if "no_speech_prob" in segment:
                    total_conf += (1.0 - segment["no_speech_prob"])
                else:
                    # If no_speech_prob not available, use a moderate default
                    total_conf += 0.7

            # Average confidence across segments
            confidence = total_conf / len(result["segments"])

            # Apply some model size scaling (larger models generally perform better)
            model_quality_factor = {
                "tiny": 0.7,
                "base": 0.8,
                "small": 0.85,
                "medium": 0.9,
                "large": 0.95
            }.get(self.model_size, 0.8)

            # Combine factors (but keep range between 0.3 and 1.0)
            final_confidence = min(1.0, confidence * model_quality_factor)
            return max(0.3, final_confidence)  # minimum confidence floor
        else:
            # If no segments, use a model size based default
            return {
                "tiny": 0.6,
                "base": 0.7,
                "small": 0.8,
                "medium": 0.85,
                "large": 0.9
            }.get(self.model_size, 0.7)

    def is_processing(self) -> bool:
        """
        Check if the model is currently processing audio.

        Returns:
            bool: True if processing, False otherwise
        """
        return self._is_processing

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get available Whisper model sizes with info.

        Returns:
            List[Dict[str, Any]]: List of dictionaries with model information
        """
        models = [
            {
                "name": "tiny",
                "params": "39M",
                "english_only": False,
                "multilingual": True,
                "description": "Fastest, least accurate"
            },
            {
                "name": "base",
                "params": "74M",
                "english_only": False,
                "multilingual": True,
                "description": "Fast, reasonable accuracy"
            },
            {
                "name": "small",
                "params": "244M",
                "english_only": False,
                "multilingual": True,
                "description": "Balanced speed and accuracy"
            },
            {
                "name": "medium",
                "params": "769M",
                "english_only": False,
                "multilingual": True,
                "description": "Good accuracy, slower"
            },
            {
                "name": "large",
                "params": "1550M",
                "english_only": False,
                "multilingual": True,
                "description": "Most accurate, slowest"
            }
        ]
        return models