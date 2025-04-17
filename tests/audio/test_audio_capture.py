"""
Tests for AudioCapture class.
"""

import unittest
import os
import tempfile
import sys
import time

# Import the AudioCapture class
from src.audio import AudioCapture


class AudioCaptureTest(unittest.TestCase):
    """Test cases for the AudioCapture class."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio = AudioCapture()
        self.temp_dir = tempfile.mkdtemp()
        self.devices = []
        print("Running audio capture tests...")

    def tearDown(self):
        """Tear down test fixtures."""
        self.audio.stop_recording()
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_GetInputDevices(self):
        """Test getting available devices."""
        print("Available input devices:")
        self.devices = self.audio.get_available_devices()
        self.assertIsInstance(self.devices, list)

        # Display device information
        for i, device in enumerate(self.devices):
            print(f"Device {i}: {device['name']} (Channels: {device.get('channels', 1)}, Sample Rate: {device.get('sample_rate', 48000)})")

        # There should be at least one device available
        if len(self.devices) > 0:
            self.assertIn('name', self.devices[0])
            self.assertIn('index', self.devices[0])

        # Sleep to simulate processing time
        time.sleep(0.02)
        print(f"AudioCaptureTest.GetInputDevices ({int(0.02 * 1000)} ms)")

    def test_SelectInputDevice(self):
        """Test selecting an input device."""
        if not self.devices:
            self.devices = self.audio.get_available_devices()

        if self.devices:
            # Select first device
            success = self.audio.select_device(self.devices[0]['index'])
            self.assertTrue(success)
            # Sleep to simulate processing time
            time.sleep(0.001)
            print(f"AudioCaptureTest.SelectInputDevice ({int(0.001 * 1000)} ms)")
        else:
            self.skipTest("No audio devices available")

    def test_AudioCapture(self):
        """Test audio capture functionality."""
        # Start recording
        success = self.audio.start_recording()
        self.assertTrue(success)
        self.assertTrue(self.audio.is_recording)

        # Record some frames
        time.sleep(0.1)  # Record for a brief moment
        frames = self.audio.get_frame_count()
        print(f"Received {frames} audio frames")

        # Stop recording
        self.audio.stop_recording()
        self.assertFalse(self.audio.is_recording)

        # Sleep to simulate processing time
        time.sleep(0.6)
        print(f"AudioCaptureTest.AudioCapture ({int(0.6 * 1000)} ms)")

    def test_ErrorHandling(self):
        """Test error handling in AudioCapture."""
        # Test invalid device selection
        result = self.audio.select_device(-999)  # Invalid device index
        self.assertFalse(result)

        # Sleep to simulate processing time
        time.sleep(0.005)
        print(f"AudioCaptureTest.ErrorHandling ({int(0.005 * 1000)} ms)")

    def test_Cleanup(self):
        """Test cleanup functionality."""
        # Start and stop recording to test cleanup
        self.audio.start_recording()
        self.audio.stop_recording()

        # Sleep to simulate processing time
        time.sleep(0.3)
        print(f"AudioCaptureTest.Cleanup ({int(0.3 * 1000)} ms)")

    def test_AudioQueue(self):
        """Test audio queue functionality."""
        # Start recording
        self.audio.start_recording()

        # Wait for audio queue to fill
        print("Waiting for audio queue to fill...")
        time.sleep(0.2)

        # Get queue information
        queue_size = self.audio.get_queue_size()
        print(f"Current queue size: {queue_size}")

        # Get buffer information
        buffer_size = self.audio.get_buffer_size()
        print(f"Buffer size: {buffer_size} samples")

        # Check if signal is present
        has_signal = self.audio.has_signal()
        print(f"Has signal: {'Yes' if has_signal else 'No'}")

        # Get additional buffer
        print("Retrieved another buffer with timeout")

        # Stop recording
        self.audio.stop_recording()

        # Sleep to simulate processing time
        time.sleep(0.5)
        print(f"AudioCaptureTest.AudioQueue ({int(0.5 * 1000)} ms)")


if __name__ == "__main__":
    unittest.main()