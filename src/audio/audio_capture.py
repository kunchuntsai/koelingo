"""
Audio capture module for KoeLingo.

This module handles microphone input and audio processing.
"""

import pyaudio
import numpy as np
import wave
import threading
import time
from typing import Optional, Callable, Tuple
from collections import deque


class AudioCapture:
    """Audio capture and processing class for real-time audio input."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        format_type: int = pyaudio.paInt16,
    ):
        """
        Initialize the audio capture module.

        Args:
            sample_rate: Sample rate in Hz (default: 16kHz for Whisper)
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1 for mono, 2 for stereo)
            format_type: Audio format type from pyaudio
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format_type = format_type

        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_level_callback = None
        self._recording_thread = None

        # Audio buffer for storing chunks (30 seconds of audio)
        self.buffer_seconds = 30
        self.max_buffer_size = int(self.buffer_seconds * self.sample_rate / self.chunk_size)
        self.audio_buffer = []

        # Frame counter for testing purposes
        self.frame_count = 0

        # Audio queue for processing
        self.audio_queue = deque(maxlen=100)

        # Selected device index
        self.selected_device_index = None

    def start_recording(self, audio_level_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Start recording audio from the microphone.

        Args:
            audio_level_callback: Optional callback function to receive audio level updates

        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if self.is_recording:
            return True

        try:
            self.audio_level_callback = audio_level_callback

            # Use selected device if specified
            input_device = None
            if self.selected_device_index is not None:
                input_device = self.selected_device_index

            self.stream = self.audio.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )

            self.is_recording = True
            self.audio_buffer = []
            self.frame_count = 0
            self.audio_queue.clear()

            # Start a thread to process audio in background
            self._recording_thread = threading.Thread(target=self._process_audio)
            self._recording_thread.daemon = True
            self._recording_thread.start()

            return True
        except Exception as e:
            print(f"Error starting audio recording: {e}")
            return False

    def stop_recording(self) -> None:
        """Stop recording audio from the microphone."""
        if not self.is_recording:
            return

        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if self._recording_thread and self._recording_thread.is_alive():
            self._recording_thread.join(timeout=1.0)

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream."""
        if self.is_recording:
            # Add the chunk to our buffer
            self.audio_buffer.append(in_data)
            self.frame_count += 1

            # Add to processing queue
            self.audio_queue.append(in_data)

            # Keep buffer at maximum size
            while len(self.audio_buffer) > self.max_buffer_size:
                self.audio_buffer.pop(0)

            return (in_data, pyaudio.paContinue)
        return (in_data, pyaudio.paComplete)

    def _process_audio(self) -> None:
        """Process audio in a background thread."""
        while self.is_recording:
            # If we have data and a callback for audio levels
            if self.audio_buffer and self.audio_level_callback:
                # Calculate audio level from the latest chunk
                latest_chunk = self.audio_buffer[-1]
                audio_array = np.frombuffer(latest_chunk, dtype=np.int16)
                audio_level = self._calculate_audio_level(audio_array)

                # Call the callback with the audio level
                self.audio_level_callback(audio_level)

            # Sleep to avoid using too much CPU
            time.sleep(0.05)

    def _calculate_audio_level(self, audio_array: np.ndarray) -> float:
        """
        Calculate the audio level from a numpy array of audio samples.

        Args:
            audio_array: Numpy array of audio samples

        Returns:
            float: Audio level between 0.0 and 1.0
        """
        # Calculate RMS (root mean square) as audio level
        if len(audio_array) == 0:
            return 0.0

        # Normalize to range 0.0 - 1.0
        rms = np.sqrt(np.mean(np.square(audio_array.astype(np.float32))))
        normalized = min(1.0, rms / 32768.0)  # 16-bit max value is 32768

        return normalized

    def get_buffer(self) -> bytes:
        """
        Get the current audio buffer.

        Returns:
            bytes: Audio data from the buffer
        """
        return b''.join(self.audio_buffer)

    def get_buffer_as_numpy(self) -> np.ndarray:
        """
        Get the current audio buffer as a numpy array.

        Returns:
            np.ndarray: Audio data as a numpy array
        """
        buffer_bytes = self.get_buffer()
        return np.frombuffer(buffer_bytes, dtype=np.int16)

    def save_buffer_to_file(self, filename: str) -> bool:
        """
        Save the current audio buffer to a WAV file.

        Args:
            filename: Name of the file to save

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            buffer_data = self.get_buffer()
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format_type))
                wf.setframerate(self.sample_rate)
                wf.writeframes(buffer_data)
            return True
        except Exception as e:
            print(f"Error saving audio to file: {e}")
            return False

    def get_available_devices(self) -> list:
        """
        Get a list of available audio input devices.

        Returns:
            list: List of dictionaries with device information
        """
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            # Only include input devices
            if device_info["maxInputChannels"] > 0:
                devices.append({
                    "index": i,
                    "name": device_info["name"],
                    "channels": device_info["maxInputChannels"],
                    "sample_rate": int(device_info["defaultSampleRate"])
                })
        return devices

    def select_device(self, device_index: int) -> bool:
        """
        Select an input device for recording.

        Args:
            device_index: Index of the device to use

        Returns:
            bool: True if device was selected successfully, False otherwise
        """
        try:
            # Verify the device index is valid
            self.audio.get_device_info_by_index(device_index)
            self.selected_device_index = device_index
            return True
        except Exception:
            return False

    def get_frame_count(self) -> int:
        """
        Get the number of audio frames recorded.

        Returns:
            int: Number of audio frames
        """
        return self.frame_count

    def get_queue_size(self) -> int:
        """
        Get the current size of the audio queue.

        Returns:
            int: Number of chunks in the queue
        """
        return len(self.audio_queue)

    def get_buffer_size(self) -> int:
        """
        Get the size of audio buffer in samples.

        Returns:
            int: Buffer size in samples
        """
        return self.chunk_size

    def has_signal(self) -> bool:
        """
        Check if there is a meaningful audio signal present.

        Returns:
            bool: True if signal is detected, False otherwise
        """
        if not self.audio_buffer:
            return False

        # Convert last buffer to numpy array
        audio_array = np.frombuffer(self.audio_buffer[-1], dtype=np.int16)

        # Calculate RMS level
        level = self._calculate_audio_level(audio_array)

        # Return True if level is above threshold
        return level > 0.05  # Arbitrary threshold

    def __del__(self):
        """Clean up resources when object is deleted."""
        self.stop_recording()
        if self.audio:
            self.audio.terminate()


# Example callback function
def print_audio_level(level):
    """Print the audio level."""
    bars = int(level * 50)
    display = '#' * bars + ' ' * (50 - bars)
    print(f"\rLevel: [{display}] {level:.2f}", end='')


if __name__ == "__main__":
    # Example usage
    audio_capture = AudioCapture()
    print("Available devices:")
    devices = audio_capture.get_available_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']}")

    try:
        audio_capture.start_recording(print_audio_level)
        print("Recording... Press Ctrl+C to stop")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping recording...")
    finally:
        audio_capture.stop_recording()
        audio_capture.save_buffer_to_file("recorded_audio.wav")
        print("\nSaved audio to 'recorded_audio.wav'")