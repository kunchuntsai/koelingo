#!/usr/bin/env python3
"""
KoeLingo Translator - Language Translation Application

This is the main entry point for the KoeLingo application.
It initializes the main window and handles audio input.
"""

import sys
import time
import threading
import numpy as np
import pyaudio
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


class AudioInputHandler(QObject):
    """Handles audio input from the microphone."""

    # Signal to emit when audio level changes
    audio_level_changed = Signal(float)
    # Signal to emit when speech is detected
    speech_detected = Signal(str)
    # Signal to emit when translation is completed
    translation_completed = Signal(str)

    def __init__(self):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.frames = []

        # Audio parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024

    def start_recording(self):
        """Start recording audio from the microphone."""
        if self.is_recording:
            return

        self.is_recording = True
        self.frames = []

        def callback(in_data, frame_count, time_info, status):
            if self.is_recording:
                self.frames.append(in_data)
                self.process_audio(in_data)
            return (in_data, pyaudio.paContinue)

        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            stream_callback=callback
        )

    def stop_recording(self):
        """Stop recording audio."""
        if not self.is_recording:
            return

        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

            # Simulate speech recognition and translation
            # In a real app, this would call actual STT and translation services
            self._simulate_processing()

    def process_audio(self, audio_data):
        """Process audio data to calculate audio level."""
        # Convert bytes to numpy array
        data = np.frombuffer(audio_data, dtype=np.int16)

        # Calculate RMS to get audio level
        rms = np.sqrt(np.mean(np.square(data.astype(np.float32))))

        # Normalize to 0-1 range (assuming 16-bit audio)
        # Increase sensitivity by applying a much stronger scaling
        # to match the visualizer demo's responsiveness
        normalized = min(1.0, rms / 32768.0)

        # Apply a much stronger non-linear scaling to increase responsiveness
        # This will make the meter behave more like the demo example
        if normalized > 0.0005:  # Lower threshold to catch quieter sounds
            # Apply cubic root scaling to dramatically boost lower levels
            # and add a significant base level so it's always somewhat visible
            level = min(1.0, 0.2 + (normalized ** 0.33) * 2.0)

            # Add some artificial variation to make it more visually dynamic
            # Only if we're not at extremes of the range
            if 0.3 < level < 0.9:
                # Add a small random variation (±10%)
                variation = (np.random.random() - 0.5) * 0.2
                level = max(0.2, min(1.0, level + level * variation))
        else:
            # Even for very quiet sounds, show a minimal level
            level = 0.1

        # Emit signal with the audio level
        self.audio_level_changed.emit(level)

    def _simulate_processing(self):
        """Simulate processing for demo purposes."""
        # This would be replaced with actual STT and translation calls
        def process():
            # Simulate STT (Speech-to-Text)
            time.sleep(1)  # Simulate processing time
            if self.is_recording:
                return  # Cancel if recording started again

            # Example Japanese text (would come from STT service)
            japanese_text = "で、えっと。お願いするかもしれないけど、基本的に返信も交えた上でタグ付けていうのは管理して行きたいなと思っております。"
            self.speech_detected.emit(japanese_text)

            # Simulate translation
            time.sleep(1)  # Simulate processing time
            if self.is_recording:
                return  # Cancel if recording started again

            # Example translation (would come from translation service)
            english_text = "So, uh. I may ask you to do so, but I would like to manage the tagging with basic replies."
            self.translation_completed.emit(english_text)

        # Run in a separate thread to avoid freezing the UI
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()

    def cleanup(self):
        """Clean up audio resources."""
        self.stop_recording()
        if self.audio:
            self.audio.terminate()


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)

    window = MainWindow()
    audio_handler = AudioInputHandler()

    # Connect signals
    window.recordingStateChanged.connect(lambda state:
        audio_handler.start_recording() if state else audio_handler.stop_recording())
    audio_handler.speech_detected.connect(window.update_input_text)
    audio_handler.translation_completed.connect(window.update_output_text)
    audio_handler.audio_level_changed.connect(window.update_audio_level)

    window.show()

    try:
        sys.exit(app.exec())
    finally:
        audio_handler.cleanup()


if __name__ == "__main__":
    main()