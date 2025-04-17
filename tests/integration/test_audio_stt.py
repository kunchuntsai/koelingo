"""
Integration tests for the audio capture to STT pipeline.
"""

import unittest
import os
import tempfile
import time
import threading
import numpy as np

from src.audio import AudioCapture
from src.stt import WhisperSTT


class AudioToSTTPipelineTest(unittest.TestCase):
    """Test the integration between audio capture and STT modules."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio = AudioCapture(sample_rate=16000)  # 16kHz for Whisper
        self.stt = WhisperSTT(model_size="tiny")
        self.temp_dir = tempfile.mkdtemp()
        print("Running audio-to-STT integration tests...")

    def tearDown(self):
        """Tear down test fixtures."""
        self.audio.stop_recording()
        self.stt.unload_model()

        # Clean up temp directory
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_AudioToSTTPipeline(self):
        """Test the entire pipeline from audio capture to STT processing."""
        # Record a short audio segment (simulated)
        # We don't use actual microphone to make the test repeatable

        # Create synthetic audio data (1 second of a sine wave at 440 Hz)
        sample_rate = 16000
        duration = 1.0  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        # Create a complex tone with harmonics for more realistic audio
        audio_data = (
            0.5 * np.sin(2 * np.pi * 440 * t) +
            0.3 * np.sin(2 * np.pi * 880 * t) +
            0.2 * np.sin(2 * np.pi * 1320 * t)
        )

        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)

        # Save to WAV file
        temp_wav = os.path.join(self.temp_dir, "test_audio.wav")

        import wave
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())

        # Synchronization event
        transcription_complete = threading.Event()
        transcription_result = None
        confidence_score = None

        # Callback function for the STT module
        def on_transcription(text, confidence):
            nonlocal transcription_result, confidence_score
            transcription_result = text
            confidence_score = confidence
            transcription_complete.set()

        # Process the audio file through STT
        print(f"Processing audio file: {temp_wav}")
        self.stt.transcribe_audio(audio_data, on_transcription)

        # Wait for transcription to complete (with timeout)
        transcription_complete.wait(timeout=30)

        # Verify results
        print(f"Transcription result: '{transcription_result}'")
        print(f"Confidence score: {confidence_score:.2f}")

        # For synthetic audio, we're not testing correctness of transcription
        # but rather that the pipeline completes without errors
        self.assertTrue(transcription_complete.is_set())

        # Check that a confidence score was produced
        self.assertIsNotNone(confidence_score)
        self.assertIsInstance(confidence_score, float)
        self.assertGreaterEqual(confidence_score, 0.0)
        self.assertLessEqual(confidence_score, 1.0)

        # For test to pass, main goal is to verify pipeline completion, not content

    def test_LiveAudioToSTT(self):
        """
        Test with live audio if available.

        This test is skipped if no audio devices are available or if SKIP_LIVE_AUDIO
        environment variable is set.
        """
        # Skip if SKIP_LIVE_AUDIO environment variable is set
        if os.environ.get('SKIP_LIVE_AUDIO', False):
            self.skipTest("Skipping live audio test (SKIP_LIVE_AUDIO is set)")

        # Get available audio devices
        devices = self.audio.get_available_devices()

        if not devices:
            self.skipTest("No audio input devices available")

        # Try to find built-in microphone first
        selected_device = None
        for device in devices:
            device_name = device['name'].lower()
            if 'built-in' in device_name or 'internal' in device_name or 'macbook' in device_name:
                selected_device = device
                break

        # If no built-in microphone found, use the first available device
        if selected_device is None:
            selected_device = devices[0]

        print(f"Using audio device: {selected_device['name']}")

        # Select the device
        self.audio.select_device(selected_device['index'])

        # Create event for synchronization
        recording_complete = threading.Event()
        transcription_complete = threading.Event()
        transcription_result = None
        confidence_score = None

        # Start recording for 2 seconds
        print("Starting audio recording...")
        self.audio.start_recording()

        # Record for a short time
        time.sleep(2.0)

        # Stop recording
        self.audio.stop_recording()
        print("Recording stopped")

        # Callback for transcription
        def on_transcription(text, confidence):
            nonlocal transcription_result, confidence_score
            transcription_result = text
            confidence_score = confidence
            transcription_complete.set()

        # Get the audio data
        audio_data = self.audio.get_buffer_as_numpy()

        # Check if audio contains actual signal
        audio_level = np.max(np.abs(audio_data.astype(np.float32) / 32768.0))
        print(f"Maximum audio level: {audio_level:.4f}")

        if audio_level < 0.01:
            print("Warning: Very low audio level detected, microphone might not be capturing sound")

        # Process through STT
        print("Processing recorded audio through STT...")
        self.stt.transcribe_audio(audio_data, on_transcription)

        # Wait for transcription to complete
        transcription_complete.wait(timeout=30)

        # Print results
        print(f"Transcription result: '{transcription_result}'")
        print(f"Confidence score: {confidence_score:.2f}")

        # We don't check the content of the transcription,
        # just that the pipeline completed successfully
        self.assertTrue(transcription_complete.is_set())

        # Check that a confidence score was produced
        self.assertIsNotNone(confidence_score)
        self.assertIsInstance(confidence_score, float)


if __name__ == "__main__":
    unittest.main()