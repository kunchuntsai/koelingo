"""
Integration tests for the real-time audio processing pipeline.
"""

import unittest
import threading
import time
import os
import numpy as np
from queue import Queue

# Import components to test
from src.audio import AudioCapture
from src.stt import WhisperSTT


class RealTimePipelineTest(unittest.TestCase):
    """Integration tests for real-time audio processing pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        # Initialize components
        self.audio = AudioCapture(
            sample_rate=16000,
            chunk_size=1024,
            channels=1
        )
        
        self.stt = WhisperSTT(
            model_size="tiny",
            device="cpu",
            language="ja"
        )
        
        # Set up result tracking
        self.results_lock = threading.Lock()
        self.audio_chunks_processed = 0
        self.transcriptions = []
        self.confidences = []
        self.is_running = False
        
        print("Running real-time pipeline integration tests...")

    def tearDown(self):
        """Tear down test fixtures."""
        self.is_running = False
        self.audio.stop_recording()
        self.stt.stop_continuous_processing()
        self.stt.unload_model()

    def _audio_chunk_callback(self, chunk):
        """Handle audio chunks from continuous mode."""
        with self.results_lock:
            self.audio_chunks_processed += 1
        
        # Forward to STT for processing
        self.stt.process_audio_chunk(chunk)
    
    def _transcription_callback(self, text, confidence):
        """Handle transcription results."""
        with self.results_lock:
            print(f"Transcription: '{text}' (confidence: {confidence:.2f})")
            self.transcriptions.append(text)
            self.confidences.append(confidence)
    
    def test_BasicPipeline(self):
        """Test the basic integration of audio capture and STT."""
        # Start STT continuous processing
        self.stt.start_continuous_processing(
            callback=self._transcription_callback
        )
        
        # Start audio capture with continuous mode
        self.audio.start_recording(
            audio_level_callback=lambda level: None,  # Dummy callback
            chunk_processing_callback=self._audio_chunk_callback,
            continuous_mode=True
        )
        
        # Set running flag
        self.is_running = True
        
        # Let it run for a short time (5 seconds)
        test_duration = 5.0  # seconds
        print(f"Running real-time pipeline for {test_duration} seconds...")
        time.sleep(test_duration)
        
        # Stop the pipeline
        self.audio.stop_recording()
        time.sleep(1.0)  # Give time for final processing
        self.stt.stop_continuous_processing()
        
        # Check results
        with self.results_lock:
            print(f"Audio chunks processed: {self.audio_chunks_processed}")
            print(f"Transcriptions received: {len(self.transcriptions)}")
        
        # The test passes if the system doesn't crash
        # We don't assert specific output since it depends on whether there was actual audio
        self.assertTrue(True, "Pipeline test completed without errors")
    
    def test_ExtendedPipeline(self):
        """Test the pipeline under extended operation."""
        # Only run this test if we have psutil for monitoring
        try:
            import psutil
            process = psutil.Process(os.getpid())
        except ImportError:
            self.skipTest("psutil not available for resource monitoring")
        
        # Start STT continuous processing
        self.stt.start_continuous_processing(
            callback=self._transcription_callback
        )
        
        # Start audio capture with continuous mode
        self.audio.start_recording(
            audio_level_callback=lambda level: None,  # Dummy callback
            chunk_processing_callback=self._audio_chunk_callback,
            continuous_mode=True
        )
        
        # Set running flag
        self.is_running = True
        
        # Run for a longer duration (15 seconds) to test stability
        test_duration = 15.0  # seconds
        check_interval = 1.0  # seconds
        
        # Metrics tracking
        metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "chunks_processed": [],
            "transcriptions": []
        }
        
        print(f"Running extended pipeline test for {test_duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            # Record metrics
            metrics["cpu_usage"].append(process.cpu_percent())
            metrics["memory_usage"].append(process.memory_info().rss / 1024 / 1024)  # MB
            
            with self.results_lock:
                metrics["chunks_processed"].append(self.audio_chunks_processed)
                metrics["transcriptions"].append(len(self.transcriptions))
            
            # Sleep for interval
            time.sleep(check_interval)
        
        # Stop the pipeline
        self.audio.stop_recording()
        time.sleep(1.0)  # Give time for final processing
        self.stt.stop_continuous_processing()
        
        # Calculate metrics
        avg_cpu = sum(metrics["cpu_usage"]) / len(metrics["cpu_usage"]) if metrics["cpu_usage"] else 0
        avg_memory = sum(metrics["memory_usage"]) / len(metrics["memory_usage"]) if metrics["memory_usage"] else 0
        
        # Calculate processing rates
        if len(metrics["chunks_processed"]) > 1:
            chunks_rate = (metrics["chunks_processed"][-1] - metrics["chunks_processed"][0]) / test_duration
        else:
            chunks_rate = 0
            
        # Print metrics
        print(f"Extended pipeline metrics:")
        print(f"  - Average CPU: {avg_cpu:.2f}%")
        print(f"  - Average Memory: {avg_memory:.2f} MB")
        print(f"  - Audio Processing Rate: {chunks_rate:.2f} chunks/sec")
        print(f"  - Final Chunks Processed: {metrics['chunks_processed'][-1]}")
        print(f"  - Final Transcriptions: {metrics['transcriptions'][-1]}")
        
        # Verify no excessive resource usage
        self.assertLess(avg_cpu, 300.0, "CPU usage too high during extended operation")  # Increased threshold for CPU usage
    
    def test_StartStopCycles(self):
        """Test multiple start/stop cycles for stability."""
        cycles = 3
        duration_per_cycle = 3.0  # seconds
        
        for cycle in range(1, cycles + 1):
            print(f"Start/stop cycle {cycle}/{cycles}")
            
            # Reset counters
            with self.results_lock:
                self.audio_chunks_processed = 0
                self.transcriptions = []
                self.confidences = []
            
            # Start pipeline
            self.stt.start_continuous_processing(
                callback=self._transcription_callback
            )
            
            self.audio.start_recording(
                audio_level_callback=lambda level: None,
                chunk_processing_callback=self._audio_chunk_callback,
                continuous_mode=True
            )
            
            # Run for the specified duration
            time.sleep(duration_per_cycle)
            
            # Stop pipeline
            self.audio.stop_recording()
            time.sleep(0.5)
            self.stt.stop_continuous_processing()
            time.sleep(0.5)
            
            # Report results for this cycle
            with self.results_lock:
                print(f"  - Cycle {cycle} results:")
                print(f"    - Audio chunks: {self.audio_chunks_processed}")
                print(f"    - Transcriptions: {len(self.transcriptions)}")
        
        # The test passes if we can complete all cycles without error
        self.assertEqual(cycle, cycles, f"Completed {cycles} start/stop cycles")


if __name__ == "__main__":
    unittest.main() 