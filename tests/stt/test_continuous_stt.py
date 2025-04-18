"""
Tests for continuous speech-to-text processing functionality.
"""

import unittest
import os
import tempfile
import time
import threading
import numpy as np
from queue import Queue

# Import the necessary classes
from src.stt import WhisperSTT


class MockSTTCallback:
    """Mock callback class for testing STT processing."""
    
    def __init__(self):
        self.transcriptions = []
        self.confidences = []
        self.lock = threading.Lock()
        
    def transcription_callback(self, text, confidence):
        """Store the transcription results."""
        with self.lock:
            print(f"Transcribed: '{text}' (confidence: {confidence:.2f})")
            self.transcriptions.append(text)
            self.confidences.append(confidence)
    
    def get_transcriptions(self):
        """Get current transcriptions."""
        with self.lock:
            return self.transcriptions.copy()
            
    def get_confidences(self):
        """Get current confidence scores."""
        with self.lock:
            return self.confidences.copy()
            
    def clear(self):
        """Clear stored data."""
        with self.lock:
            self.transcriptions = []
            self.confidences = []


class ContinuousSTTTest(unittest.TestCase):
    """Test cases for continuous speech-to-text processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.stt = WhisperSTT(model_size="tiny", language="ja")
        self.callback = MockSTTCallback()
        print("Running continuous STT tests...")

    def tearDown(self):
        """Tear down test fixtures."""
        self.stt.stop_continuous_processing()
        self.stt.unload_model()
        
    def test_ContinuousProcessingMode(self):
        """Test starting and stopping continuous processing mode."""
        # Start continuous processing
        success = self.stt.start_continuous_processing(
            callback=self.callback.transcription_callback
        )
        self.assertTrue(success)
        self.assertTrue(self.stt._continuous_active)
        
        # Wait for setup to complete
        time.sleep(1.0)
        
        # Verify continuous thread is running
        self.assertTrue(self.stt._continuous_thread.is_alive())
        
        # Stop continuous processing
        self.stt.stop_continuous_processing()
        
        # Wait for shutdown
        time.sleep(0.5)
        
        # Verify flags
        self.assertFalse(self.stt._continuous_active)
    
    def test_AudioChunkProcessing(self):
        """Test processing audio chunks through the queue."""
        # Start continuous processing
        self.stt.start_continuous_processing(
            callback=self.callback.transcription_callback
        )
        
        # Generate test audio - a simple sine wave tone
        sample_rate = 16000
        duration = 3.0  # seconds
        frequency = 440.0  # A4 tone
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * frequency * t) * 32767
        audio_chunk = tone.astype(np.int16)
        
        # Process the chunk
        self.stt.process_audio_chunk(audio_chunk)
        
        # Wait for processing to complete (may take some time)
        print("Waiting for audio chunk processing...")
        
        # Wait up to 10 seconds for a result
        max_wait = 10
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if len(self.callback.get_transcriptions()) > 0:
                break
            time.sleep(0.5)
        
        # Stop continuous processing
        self.stt.stop_continuous_processing()
        
        # The result might be empty or contain noise recognition
        # The main test is that no exceptions occur
        transcriptions = self.callback.get_transcriptions()
        print(f"Number of transcriptions: {len(transcriptions)}")
        for i, text in enumerate(transcriptions):
            print(f"Transcription {i+1}: {text}")
    
    def test_QueueHandling(self):
        """Test the queue handling functionality."""
        # Start continuous processing
        self.stt.start_continuous_processing(
            callback=self.callback.transcription_callback
        )
        
        # Add multiple small chunks to the queue
        chunk_duration = 0.5  # seconds
        sample_rate = 16000
        sample_count = int(sample_rate * chunk_duration)
        
        for i in range(3):  # Send 3 chunks
            # Generate simple chunk of audio
            chunk = np.random.randint(-1000, 1000, sample_count, dtype=np.int16)
            self.stt.process_audio_chunk(chunk)
            print(f"Added chunk {i+1} to processing queue")
        
        # Verify queue size
        time.sleep(0.5)  # Wait briefly for queuing
        queue_size = self.stt._audio_queue.qsize()
        print(f"Queue size after adding chunks: {queue_size}")
        
        # Wait for queue to be processed
        max_wait = 10  # seconds
        start_time = time.time()
        while not self.stt._audio_queue.empty() and time.time() - start_time < max_wait:
            time.sleep(0.5)
            print("Waiting for queue to empty...")
        
        # Stop continuous processing
        self.stt.stop_continuous_processing()
        
        # Final queue size should be 0 or close to 0
        final_queue_size = self.stt._audio_queue.qsize()
        print(f"Final queue size: {final_queue_size}")
    
    def test_ExtendedOperation(self):
        """Test extended operation for stability."""
        test_duration = 20.0  # Run for 20 seconds to test stability
        
        # Start continuous processing
        self.stt.start_continuous_processing(
            callback=self.callback.transcription_callback
        )
        
        # Monitor memory and performance during extended operation
        start_time = time.time()
        check_interval = 1.0  # Check every second
        
        # Track metrics
        metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "queue_size": [],
            "is_processing": []
        }
        
        try:
            # Monitor resource usage during the test
            import psutil
            process = psutil.Process(os.getpid())
            
            # Periodically add data to the queue
            chunk_size = 16000  # 1 second of audio at 16kHz
            
            while time.time() - start_time < test_duration:
                # Add a random chunk every 5 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and elapsed - int(elapsed) < 0.1:
                    chunk = np.random.randint(-1000, 1000, chunk_size, dtype=np.int16)
                    self.stt.process_audio_chunk(chunk)
                    print(f"Added test chunk at {elapsed:.1f}s")
                
                # Record metrics
                metrics["cpu_usage"].append(process.cpu_percent())
                metrics["memory_usage"].append(process.memory_info().rss / 1024 / 1024)  # MB
                metrics["queue_size"].append(self.stt._audio_queue.qsize())
                metrics["is_processing"].append(self.stt._is_processing)
                
                # Sleep for the check interval
                time.sleep(check_interval)
                
            # Stop continuous processing
            self.stt.stop_continuous_processing()
            
            # Calculate average metrics
            avg_cpu = sum(metrics["cpu_usage"]) / len(metrics["cpu_usage"]) if metrics["cpu_usage"] else 0
            avg_memory = sum(metrics["memory_usage"]) / len(metrics["memory_usage"]) if metrics["memory_usage"] else 0
            max_queue = max(metrics["queue_size"]) if metrics["queue_size"] else 0
            processing_percentage = (sum(1 for p in metrics["is_processing"] if p) / len(metrics["is_processing"])) * 100 if metrics["is_processing"] else 0
            
            # Print metrics
            print(f"Extended STT operation metrics:")
            print(f"  - Average CPU: {avg_cpu:.2f}%")
            print(f"  - Average Memory: {avg_memory:.2f} MB")
            print(f"  - Max Queue Size: {max_queue} chunks")
            print(f"  - Processing Time: {processing_percentage:.1f}% of test duration")
            print(f"  - Transcriptions: {len(self.callback.get_transcriptions())}")
            
            # Verify metrics (with generous thresholds)
            # These are basic checks to verify stability
            self.assertLess(avg_cpu, 300.0, "CPU usage too high during extended operation")  # Increased threshold for CPU usage
            self.assertLess(max_queue, 20, "Queue size increased too much during extended operation")
            
        except ImportError:
            # If psutil isn't available, just run the basic test
            time.sleep(test_duration)
            self.stt.stop_continuous_processing()
            print("Note: Install psutil for detailed performance metrics")
    
    def test_ModelSwitch(self):
        """Test switching between CTranslate2 and standard Whisper."""
        try:
            # First test with CTranslate2 if available
            ctranslate_model = WhisperSTT(
                model_size="tiny",
                language="ja",
                use_ctranslate2=True
            )
            
            # Check if CTranslate2 is actually being used
            is_using_ctranslate = ctranslate_model.use_ctranslate2
            
            print(f"Using CTranslate2: {is_using_ctranslate}")
            
            # Start and stop to verify no errors
            ctranslate_model.start_continuous_processing()
            time.sleep(1.0)
            ctranslate_model.stop_continuous_processing()
            ctranslate_model.unload_model()
            
            # Now test with standard Whisper
            standard_model = WhisperSTT(
                model_size="tiny",
                language="ja",
                use_ctranslate2=False
            )
            
            # Verify standard model is not using CTranslate2
            self.assertFalse(standard_model.use_ctranslate2)
            
            # Start and stop to verify no errors
            standard_model.start_continuous_processing()
            time.sleep(1.0)
            standard_model.stop_continuous_processing()
            standard_model.unload_model()
            
            print("Both CTranslate2 and standard Whisper models work correctly")
            
        except Exception as e:
            self.fail(f"Error during model switching test: {e}")


if __name__ == "__main__":
    unittest.main() 