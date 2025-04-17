"""
Performance tests for the WhisperSTT module.
"""

import unittest
import os
import time
import tempfile
import numpy as np
import threading
import platform
from datetime import datetime

from src.stt import WhisperSTT


class STTPerformanceTest(unittest.TestCase):
    """Performance tests for the STT module."""

    def setUp(self):
        """Set up test fixtures."""
        self.stt = WhisperSTT(model_size="tiny")
        self.temp_dir = tempfile.mkdtemp()
        print("Running STT performance tests...")

    def tearDown(self):
        """Tear down test fixtures."""
        self.stt.unload_model()

        # Clean up temp directory
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_LoadTimePerformance(self):
        """Test model loading performance."""
        # Unload the model first
        self.stt.unload_model()

        # Measure model loading time
        start_time = time.time()
        self.stt.load_model()
        load_time = time.time() - start_time

        print(f"Model load time: {load_time:.3f} seconds")

        # Log system info for performance context
        system_info = f"OS: {platform.system()} {platform.release()}, Python: {platform.python_version()}"
        print(f"System information: {system_info}")

        # This is not a strict test, but we record performance metrics
        self.assertTrue(self.stt.is_loaded)

        # For tiny model, loading should typically be under 10 seconds even on modest hardware
        # but this is a flexible threshold
        self.assertLess(load_time, 20.0)

    def test_TranscriptionPerformance(self):
        """Test transcription performance with different audio durations."""
        # Test different audio durations
        durations = [1.0, 3.0, 5.0]
        sample_rate = 16000

        results = []

        for duration in durations:
            # Create an audio sample of the specified duration
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            # Generate a more complex signal (mixture of frequencies)
            audio_data = (
                0.5 * np.sin(2 * np.pi * 440 * t) +
                0.3 * np.sin(2 * np.pi * 880 * t) +
                0.2 * np.sin(2 * np.pi * 1320 * t)
            )

            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)

            # Measurement values
            transcription_result = None
            confidence_result = None

            # Event for synchronization
            event = threading.Event()

            def callback(text, confidence):
                nonlocal transcription_result, confidence_result
                transcription_result = text
                confidence_result = confidence
                event.set()

            # Measure transcription time
            start_time = time.time()
            self.stt.transcribe_audio(audio_data, callback)

            # Wait for transcription to complete
            event.wait(timeout=60)
            transcription_time = time.time() - start_time

            # Record results
            results.append({
                'duration': duration,
                'transcription_time': transcription_time,
                'processing_ratio': transcription_time / duration,
                'sample_length': len(audio_data),
                'confidence': confidence_result
            })

            print(f"Audio duration: {duration:.1f}s, Transcription time: {transcription_time:.3f}s, "
                  f"Ratio: {transcription_time / duration:.2f}x, Confidence: {confidence_result:.2f}")

        # Calculate averages
        avg_ratio = sum(r['processing_ratio'] for r in results) / len(results)
        print(f"Average processing ratio: {avg_ratio:.2f}x real-time")

        # Record results in a temporary file for later analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.temp_dir, f"stt_perf_{timestamp}.txt")
        with open(results_file, 'w') as f:
            f.write(f"STT Performance Test Results ({timestamp})\n")
            f.write(f"Model size: {self.stt.model_size}\n")
            f.write(f"Device: {self.stt.device}\n")
            f.write(f"System: {platform.system()} {platform.release()}\n")
            f.write(f"Python: {platform.python_version()}\n\n")

            for i, result in enumerate(results):
                f.write(f"Test {i+1}:\n")
                for key, value in result.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")

            f.write(f"Average processing ratio: {avg_ratio:.2f}x real-time\n")

        print(f"Performance results saved to {results_file}")

        # Check that performance is within reasonable bounds
        # The actual threshold would depend on hardware expectations
        # For tiny model, processing should be under 10x real-time on most modern hardware
        self.assertLess(avg_ratio, 30.0)

    def test_MemoryUsage(self):
        """Test memory usage of the STT model."""
        # This is a basic test that doesn't actually measure memory precisely
        # For more accurate measurements, tools like memory_profiler would be needed

        import gc
        import psutil

        # Force garbage collection
        gc.collect()

        # Get baseline memory usage
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB

        # Unload model if loaded
        if self.stt.is_loaded:
            self.stt.unload_model()
            gc.collect()

        # Get memory usage before model load
        pre_load_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB

        # Load model and measure memory
        self.stt.load_model()

        # Sleep briefly to allow memory usage to stabilize
        time.sleep(1)

        # Force garbage collection
        gc.collect()

        # Get memory usage after model load
        post_load_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB

        # Calculate memory usage increase
        memory_increase = post_load_memory - pre_load_memory

        print(f"Baseline memory usage: {baseline_memory:.2f} MB")
        print(f"Pre-load memory usage: {pre_load_memory:.2f} MB")
        print(f"Post-load memory usage: {post_load_memory:.2f} MB")
        print(f"Memory increase for model: {memory_increase:.2f} MB")

        # Add psutil to requirements.txt if it's not already there
        # This is just informational, not a strict test
        print(f"Note: This test requires 'psutil' package. Add it to requirements.txt if not already present.")

        # For tiny model, memory usage should be reasonable
        # The actual value will vary based on many factors, so this is a very flexible threshold
        self.assertLess(memory_increase, 2000)  # Less than 2GB


if __name__ == "__main__":
    unittest.main()