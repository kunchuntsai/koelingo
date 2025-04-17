"""
PyBind11 binding module for C++ audio capture implementation.

This module loads the C++ implementation of the audio capture functionality
and provides a wrapper to ensure compatibility with the Python implementation.
"""

import os
import sys
import logging
from typing import Optional, Callable, Any, Dict, List, Union

# Try to import the C++ extension
try:
    from .audio_capture_cpp import AudioCaptureCpp
    _HAS_CPP_IMPL = True
except ImportError as e:
    logging.warning(f"Failed to import C++ audio capture implementation: {e}")
    logging.warning("Falling back to pure Python implementation")
    _HAS_CPP_IMPL = False

# Import the Python implementation for fallback
from ..audio_capture import AudioCapture as PyAudioCapture


class AudioCapture:
    """
    Wrapper class that provides a unified interface to either the C++ or Python
    implementation of audio capture functionality.

    This class automatically selects the best available implementation, preferring
    the C++ implementation for performance, but falling back to the Python implementation
    if the C++ one is not available.
    """

    def __init__(self,
                sample_rate: int = 16000,
                chunk_size: int = 1024,
                channels: int = 1,
                format_type: int = 8):  # 8 = paInt16 in PortAudio
        """
        Initialize the audio capture module.

        Args:
            sample_rate: Sample rate in Hz (default: 16kHz for Whisper)
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1 for mono, 2 for stereo)
            format_type: Audio format type from PortAudio
        """
        self._impl = None

        # Try to use C++ implementation first
        if _HAS_CPP_IMPL:
            try:
                self._impl = AudioCaptureCpp(sample_rate, chunk_size, channels, format_type)
                self._using_cpp = True
                logging.info("Using C++ audio capture implementation")
            except Exception as e:
                logging.warning(f"Failed to initialize C++ audio capture: {e}")
                self._impl = None

        # Fall back to Python implementation if needed
        if self._impl is None:
            self._impl = PyAudioCapture(sample_rate, chunk_size, channels, format_type)
            self._using_cpp = False
            logging.info("Using Python audio capture implementation")

    def start_recording(self, audio_level_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Start recording audio from the microphone.

        Args:
            audio_level_callback: Optional callback function to receive audio level updates

        Returns:
            bool: True if recording started successfully, False otherwise
        """
        return self._impl.start_recording(audio_level_callback)

    def stop_recording(self) -> None:
        """Stop recording audio from the microphone."""
        self._impl.stop_recording()

    def get_buffer(self) -> bytes:
        """
        Get the current audio buffer.

        Returns:
            bytes: Audio data from the buffer
        """
        return self._impl.get_buffer()

    def save_buffer_to_file(self, filename: str) -> bool:
        """
        Save the current audio buffer to a WAV file.

        Args:
            filename: Name of the file to save

        Returns:
            bool: True if saved successfully, False otherwise
        """
        return self._impl.save_buffer_to_file(filename)

    def get_available_devices(self) -> List[Dict[str, Union[int, str]]]:
        """
        Get a list of available audio input devices.

        Returns:
            list: List of dictionaries with device information
        """
        return self._impl.get_available_devices()

    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._impl.is_recording

    @property
    def using_cpp_implementation(self) -> bool:
        """Check if using C++ implementation."""
        return self._using_cpp