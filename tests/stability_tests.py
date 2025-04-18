#!/usr/bin/env python3
"""
Stability testing for KoeLingo.

This script performs extended stability tests for continuous real-time processing.
"""

import os
import sys
import time
import argparse
import threading
import logging
import traceback
from datetime import datetime, timedelta
import psutil
import numpy as np
import matplotlib.pyplot as plt

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.audio import AudioCapture
from src.stt import WhisperSTT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("stability_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StabilityTest:
    """Extended stability testing for continuous processing."""
    
    def __init__(self, test_duration=300, model_size="tiny", use_ctranslate2=True):
        """
        Initialize the stability test.
        
        Args:
            test_duration: Duration in seconds (default: 5 minutes)
            model_size: Whisper model size (default: tiny)
            use_ctranslate2: Whether to use CTranslate2 (default: True)
        """
        self.test_duration = test_duration
        self.model_size = model_size
        self.use_ctranslate2 = use_ctranslate2
        
        # Set up components
        self.audio = None
        self.stt = None
        
        # Setup tracking
        self.lock = threading.Lock()
        self.audio_chunks = 0
        self.audio_levels = []
        self.transcriptions = []
        self.confidences = []
        self.is_running = False
        
        # Metrics tracking
        self.metrics = {
            "timestamp": [],
            "cpu_usage": [],
            "memory_usage": [],
            "audio_chunks": [],
            "transcriptions": [],
            "queue_size": []
        }
        
        # Set up process for monitoring
        self.process = psutil.Process(os.getpid())
    
    def audio_level_callback(self, level):
        """Handle audio level updates."""
        with self.lock:
            self.audio_levels.append(level)
    
    def chunk_callback(self, chunk):
        """Handle audio chunk processing."""
        with self.lock:
            self.audio_chunks += 1
    
    def transcription_callback(self, text, confidence):
        """Handle transcription results."""
        with self.lock:
            logger.info(f"Transcription: '{text}' (confidence: {confidence:.2f})")
            self.transcriptions.append(text)
            self.confidences.append(confidence)
    
    def collect_metrics(self):
        """Collect system metrics at regular intervals."""
        while self.is_running:
            try:
                # Get current metrics
                current_time = time.time() - self.start_time
                cpu_percent = self.process.cpu_percent()
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                
                with self.lock:
                    chunks = self.audio_chunks
                    transcription_count = len(self.transcriptions)
                
                # Get queue size if available
                queue_size = 0
                if self.stt and hasattr(self.stt, '_audio_queue'):
                    queue_size = self.stt._audio_queue.qsize()
                
                # Record metrics
                self.metrics["timestamp"].append(current_time)
                self.metrics["cpu_usage"].append(cpu_percent)
                self.metrics["memory_usage"].append(memory_mb)
                self.metrics["audio_chunks"].append(chunks)
                self.metrics["transcriptions"].append(transcription_count)
                self.metrics["queue_size"].append(queue_size)
                
                # Log current status
                if int(current_time) % 30 == 0:  # Log every 30 seconds
                    logger.info(f"Status at {int(current_time)}s: "
                             f"CPU={cpu_percent:.1f}%, "
                             f"Memory={memory_mb:.1f}MB, "
                             f"Chunks={chunks}, "
                             f"Transcriptions={transcription_count}, "
                             f"Queue={queue_size}")
                
                # Sleep for a second
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                logger.error(traceback.format_exc())
    
    def setup(self):
        """Set up the audio and STT components."""
        try:
            # Initialize audio component
            self.audio = AudioCapture(
                sample_rate=16000,
                chunk_size=1024,
                channels=1
            )
            
            # Initialize STT component
            self.stt = WhisperSTT(
                model_size=self.model_size,
                device="cpu",
                language="ja",
                use_ctranslate2=self.use_ctranslate2
            )
            
            logger.info("Components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up components: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def run(self):
        """Run the stability test."""
        # Setup components
        if not self.setup():
            logger.error("Failed to set up components, aborting test")
            return False
        
        try:
            logger.info(f"Starting stability test for {self.test_duration} seconds")
            logger.info(f"Model: {self.model_size}, CTranslate2: {self.use_ctranslate2}")
            
            # Set running flag
            self.is_running = True
            self.start_time = time.time()
            
            # Start metrics collection thread
            metrics_thread = threading.Thread(target=self.collect_metrics)
            metrics_thread.daemon = True
            metrics_thread.start()
            
            # Start STT component
            self.stt.start_continuous_processing(
                callback=self.transcription_callback
            )
            
            # Start audio component
            self.audio.start_recording(
                audio_level_callback=self.audio_level_callback,
                chunk_processing_callback=self.chunk_callback,
                continuous_mode=True
            )
            
            # Calculate end time
            end_time = self.start_time + self.test_duration
            
            # Display initial progress
            logger.info("Test running...")
            
            # Wait for test to complete
            while time.time() < end_time and self.is_running:
                # Calculate progress
                elapsed = time.time() - self.start_time
                progress = int((elapsed / self.test_duration) * 100)
                
                # Print progress every 5%
                if progress % 5 == 0:
                    remaining = self.test_duration - elapsed
                    eta = datetime.now() + timedelta(seconds=remaining)
                    logger.info(f"Progress: {progress}% (ETA: {eta.strftime('%H:%M:%S')})")
                
                # Sleep a bit to avoid busy waiting
                time.sleep(5)
            
            # Clean up
            logger.info("Test complete, cleaning up...")
            self.is_running = False
            
            # Stop audio and STT
            self.audio.stop_recording()
            time.sleep(0.5)
            self.stt.stop_continuous_processing()
            time.sleep(0.5)
            self.stt.unload_model()
            
            # Wait for metrics thread to finish
            metrics_thread.join(timeout=2.0)
            
            # Process and report results
            self.report_results()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
            self.is_running = False
            self.audio.stop_recording()
            self.stt.stop_continuous_processing()
            self.stt.unload_model()
            return False
            
        except Exception as e:
            logger.error(f"Error during stability test: {e}")
            logger.error(traceback.format_exc())
            self.is_running = False
            if self.audio:
                self.audio.stop_recording()
            if self.stt:
                self.stt.stop_continuous_processing()
                self.stt.unload_model()
            return False
    
    def report_results(self):
        """Process and report test results."""
        try:
            # Calculate summary statistics
            if not self.metrics["timestamp"]:
                logger.error("No metrics collected during test")
                return
            
            # Calculate averages and max values
            avg_cpu = sum(self.metrics["cpu_usage"]) / len(self.metrics["cpu_usage"])
            avg_memory = sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"])
            max_cpu = max(self.metrics["cpu_usage"])
            max_memory = max(self.metrics["memory_usage"])
            max_queue = max(self.metrics["queue_size"])
            
            # Calculate processing rates
            final_chunks = self.metrics["audio_chunks"][-1]
            final_transcriptions = self.metrics["transcriptions"][-1]
            chunks_per_second = final_chunks / self.test_duration
            
            # Log results
            logger.info(f"\n{'='*50}")
            logger.info(f"STABILITY TEST RESULTS")
            logger.info(f"{'='*50}")
            logger.info(f"Test duration: {self.test_duration} seconds")
            logger.info(f"Model: {self.model_size}, CTranslate2: {self.use_ctranslate2}")
            logger.info(f"\nResource Usage:")
            logger.info(f"  - Average CPU: {avg_cpu:.2f}%")
            logger.info(f"  - Max CPU: {max_cpu:.2f}%")
            logger.info(f"  - Average Memory: {avg_memory:.2f} MB")
            logger.info(f"  - Max Memory: {max_memory:.2f} MB")
            logger.info(f"  - Max Queue Size: {max_queue}")
            logger.info(f"\nProcessing Statistics:")
            logger.info(f"  - Audio Chunks Processed: {final_chunks}")
            logger.info(f"  - Transcriptions Generated: {final_transcriptions}")
            logger.info(f"  - Processing Rate: {chunks_per_second:.2f} chunks/second")
            logger.info(f"  - Audio to Transcription Ratio: {final_transcriptions/final_chunks if final_chunks else 0:.4f}")
            logger.info(f"{'='*50}")
            
            # Create plots
            self.plot_results()
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            logger.error(traceback.format_exc())
    
    def plot_results(self):
        """Create and save charts of the test results."""
        try:
            # Create figure with subplots
            plt.figure(figsize=(12, 10))
            
            # Plot CPU usage
            plt.subplot(3, 1, 1)
            plt.plot(self.metrics["timestamp"], self.metrics["cpu_usage"])
            plt.title("CPU Usage")
            plt.xlabel("Time (seconds)")
            plt.ylabel("CPU (%)")
            plt.grid(True)
            
            # Plot memory usage
            plt.subplot(3, 1, 2)
            plt.plot(self.metrics["timestamp"], self.metrics["memory_usage"])
            plt.title("Memory Usage")
            plt.xlabel("Time (seconds)")
            plt.ylabel("Memory (MB)")
            plt.grid(True)
            
            # Plot queue size and processed chunks
            plt.subplot(3, 1, 3)
            plt.plot(self.metrics["timestamp"], self.metrics["queue_size"], label="Queue Size")
            plt.plot(self.metrics["timestamp"], 
                     [c - self.metrics["audio_chunks"][0] for c in self.metrics["audio_chunks"]], 
                     label="Chunks Processed")
            plt.title("Processing Performance")
            plt.xlabel("Time (seconds)")
            plt.ylabel("Count")
            plt.legend()
            plt.grid(True)
            
            # Adjust layout and save
            plt.tight_layout()
            plt.savefig("stability_test_results.png")
            logger.info("Saved plots to stability_test_results.png")
            
        except Exception as e:
            logger.error(f"Error creating plots: {e}")
            logger.error(traceback.format_exc())


def main():
    """Run a stability test with command line arguments."""
    parser = argparse.ArgumentParser(description="Run extended stability tests for KoeLingo.")
    parser.add_argument(
        "-d", "--duration", 
        type=int, 
        default=300, 
        help="Test duration in seconds (default: 300)"
    )
    parser.add_argument(
        "-m", "--model", 
        type=str, 
        default="tiny", 
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: tiny)"
    )
    parser.add_argument(
        "--no-ctranslate2", 
        action="store_true", 
        help="Disable CTranslate2 optimization"
    )
    
    args = parser.parse_args()
    
    # Run the test
    test = StabilityTest(
        test_duration=args.duration,
        model_size=args.model,
        use_ctranslate2=not args.no_ctranslate2
    )
    
    success = test.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 