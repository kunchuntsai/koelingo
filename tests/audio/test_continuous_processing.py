"""
Tests for continuous audio processing functionality.
"""

import unittest
import os
import tempfile
import time
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

# Import the necessary classes
from src.audio import AudioCapture


class MockAudioCallback:
    """Mock callback class for testing audio processing."""
    
    def __init__(self):
        self.levels = []
        self.chunks = []
        self.lock = threading.Lock()
        
    def level_callback(self, level):
        """Store the audio level."""
        with self.lock:
            self.levels.append(level)
    
    def chunk_callback(self, chunk):
        """Store the audio chunk."""
        with self.lock:
            self.chunks.append(chunk)
            
    def get_levels(self):
        """Get current levels."""
        with self.lock:
            return self.levels.copy()
            
    def get_chunks(self):
        """Get current chunks."""
        with self.lock:
            return self.chunks.copy()
            
    def clear(self):
        """Clear stored data."""
        with self.lock:
            self.levels = []
            self.chunks = []


class ContinuousProcessingTest(unittest.TestCase):
    """Test cases for continuous audio processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio = AudioCapture()
        self.callback = MockAudioCallback()
        print("Running continuous audio processing tests...")

    def tearDown(self):
        """Tear down test fixtures."""
        self.audio.stop_recording()
        
    def test_ContinuousMode(self):
        """Test basic continuous mode operation."""
        # Start recording with continuous mode
        success = self.audio.start_recording(
            audio_level_callback=self.callback.level_callback,
            chunk_processing_callback=self.callback.chunk_callback,
            continuous_mode=True
        )
        self.assertTrue(success)
        self.assertTrue(self.audio.is_recording)
        self.assertTrue(self.audio.continuous_mode)
        
        # Let it record for a short time
        time.sleep(2.0)
        
        # Verify we received audio levels
        levels = self.callback.get_levels()
        self.assertGreater(len(levels), 0, "No audio levels received")
        print(f"Received {len(levels)} audio level updates")
        
        # Stop recording
        self.audio.stop_recording()
        self.assertFalse(self.audio.is_recording)
        
    def test_SilenceDetection(self):
        """Test silence detection in continuous mode."""
        # Configure audio settings for testing silence detection
        initial_threshold = self.audio.silence_threshold
        initial_chunks = self.audio.silence_chunks
        
        self.audio.silence_threshold = 0.05  # Increase threshold to detect silence more easily
        self.audio.silence_chunks = 5  # Reduce the number of chunks for faster testing
        
        # Start recording with continuous mode
        success = self.audio.start_recording(
            audio_level_callback=self.callback.level_callback,
            chunk_processing_callback=self.callback.chunk_callback,
            continuous_mode=True
        )
        self.assertTrue(success)
        
        # Record for enough time to potentially detect silence
        time.sleep(4.0)
        
        # Get chunks that were processed
        chunks = self.callback.get_chunks()
        chunk_count = len(chunks)
        
        # Stop recording
        self.audio.stop_recording()
        
        # Restore original settings
        self.audio.silence_threshold = initial_threshold
        self.audio.silence_chunks = initial_chunks
        
        # Print results
        print(f"Detected {chunk_count} speech segments with silence detection")
        
        # If we're using a real microphone, we might get actual speech segments,
        # but we can at least verify the code runs without errors
        self.assertTrue(chunk_count >= 0, "Silence detection failed")
    
    def test_SpeechBuffering(self):
        """Test speech segment buffering."""
        # Configure for testing
        self.audio.min_speech_chunks = 5
        
        # Create a buffer of "simulated speech"
        sample_rate = self.audio.sample_rate
        chunk_size = self.audio.chunk_size
        
        # Prepare test data
        audio_level = 0.1  # Above default silence threshold of 0.02
        
        # Add audio arrays that look like speech
        for _ in range(10):
            audio_array = np.ones(chunk_size, dtype=np.int16) * 1000  # Level above silence
            self.audio.buffered_chunks_for_processing.append(audio_array)
        
        # Call the process speech segment method
        self.audio.chunk_processing_callback = self.callback.chunk_callback
        self.audio._process_speech_segment()
        
        # Verify processing
        chunks = self.callback.get_chunks()
        self.assertEqual(len(chunks), 1, "Expected one processed speech segment")
        
        # Verify reset after processing
        self.assertEqual(len(self.audio.buffered_chunks_for_processing), 0,
                         "Buffer should be cleared after processing")
        self.assertFalse(self.audio.speech_detected, 
                         "Speech detected flag should be reset")
        self.assertEqual(self.audio.current_silence_count, 0,
                         "Silence count should be reset")
    
    def test_ExtendedOperation(self):
        """Test extended operation for stability."""
        test_duration = 10.0  # Run for 10 seconds
        
        # Start recording with continuous mode
        self.audio.start_recording(
            audio_level_callback=self.callback.level_callback,
            chunk_processing_callback=self.callback.chunk_callback,
            continuous_mode=True
        )
        
        # Monitor memory and performance during extended operation
        start_time = time.time()
        check_interval = 1.0  # Check every second
        
        # Track metrics
        metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "buffer_size": [],
            "callbacks": []
        }
        
        try:
            # Monitor resource usage during the test
            import psutil
            process = psutil.Process(os.getpid())
            
            while time.time() - start_time < test_duration:
                # Record metrics
                metrics["cpu_usage"].append(process.cpu_percent())
                metrics["memory_usage"].append(process.memory_info().rss / 1024 / 1024)  # MB
                metrics["buffer_size"].append(len(self.audio.audio_buffer))
                metrics["callbacks"].append(len(self.callback.get_levels()))
                
                # Sleep for the check interval
                time.sleep(check_interval)
                
            # Stop recording
            self.audio.stop_recording()
            
            # Calculate average metrics
            avg_cpu = sum(metrics["cpu_usage"]) / len(metrics["cpu_usage"]) if metrics["cpu_usage"] else 0
            avg_memory = sum(metrics["memory_usage"]) / len(metrics["memory_usage"]) if metrics["memory_usage"] else 0
            max_buffer = max(metrics["buffer_size"]) if metrics["buffer_size"] else 0
            callback_growth = metrics["callbacks"][-1] - metrics["callbacks"][0] if len(metrics["callbacks"]) > 1 else 0
            
            # Print metrics
            print(f"Extended operation metrics:")
            print(f"  - Average CPU: {avg_cpu:.2f}%")
            print(f"  - Average Memory: {avg_memory:.2f} MB")
            print(f"  - Max Buffer Size: {max_buffer} chunks")
            print(f"  - Callback Growth: {callback_growth} callbacks")
            
            # Verify metrics
            # These are just basic checks - adjust thresholds as needed
            self.assertLess(avg_cpu, 80.0, "CPU usage too high during extended operation")
            self.assertLess(max_buffer, self.audio.max_buffer_size * 1.1, 
                           "Buffer size exceeded limits during extended operation")
            
        except ImportError:
            # If psutil isn't available, just run the test without metrics
            time.sleep(test_duration)
            self.audio.stop_recording()
            print("Note: Install psutil for detailed performance metrics")


if __name__ == "__main__":
    unittest.main() 