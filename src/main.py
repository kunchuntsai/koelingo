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
from src.audio.audio_capture import AudioCapture
from src.stt import WhisperSTT


class AudioInputHandler(QObject):
    """Handles audio input from the microphone."""

    # Signal to emit when audio level changes
    audio_level_changed = Signal(float)
    # Signal to emit when speech is detected (text, confidence)
    speech_detected = Signal(str, float)
    # Signal to emit when translation is completed
    translation_completed = Signal(str, str)

    def __init__(self):
        super().__init__()

        # Initialize audio capture
        self.audio_capture = AudioCapture(
            sample_rate=16000,  # Whisper requires 16kHz
            chunk_size=1024,
            channels=1
        )

        # Initialize Whisper STT
        self.stt = WhisperSTT(
            model_size="tiny",  # Start with tiny model for speed
            device="cpu",       # Default to CPU processing
            language="ja"       # Japanese language
        )

        self.is_recording = False
        self.translation_thread = None

    def start_recording(self):
        """Start recording audio from the microphone."""
        if self.is_recording:
            return

        self.is_recording = True

        # Start audio capture with level callback
        self.audio_capture.start_recording(
            audio_level_callback=self._audio_level_callback
        )

    def stop_recording(self):
        """Stop recording audio."""
        if not self.is_recording:
            return

        self.is_recording = False

        # Stop audio capture
        self.audio_capture.stop_recording()

        # Process the captured audio for STT
        self._process_captured_audio()

    def _audio_level_callback(self, level):
        """Callback for audio level updates."""
        self.audio_level_changed.emit(level)

    def _process_captured_audio(self):
        """Process the captured audio for speech recognition."""
        # Get audio data as numpy array
        audio_data = self.audio_capture.get_buffer_as_numpy()

        if len(audio_data) == 0:
            print("No audio data captured")
            return

        # Transcribe using Whisper STT
        self.stt.transcribe_audio(
            audio_data=audio_data,
            callback=self._on_transcription_complete
        )

    def _on_transcription_complete(self, transcription, confidence=0.7):
        """
        Callback when transcription is complete.

        Args:
            transcription: The transcribed text
            confidence: Confidence score from 0.0 to 1.0 (default: 0.7)
        """
        if not transcription:
            return

        # Emit signal with recognized Japanese text and confidence
        self.speech_detected.emit(transcription, confidence)

        # Simulate translation for now (will be replaced with actual translation later)
        self._simulate_translation(transcription)

    def _simulate_translation(self, japanese_text):
        """
        Temporarily simulate translation until translation module is implemented.

        This will be replaced with actual translation in Phase 4.
        """
        def process():
            # Simulate processing time
            time.sleep(1)

            # Example translation (fixed for demo purposes)
            if "お願い" in japanese_text:
                english_text = "I would like to ask for your help."
            elif "こんにちは" in japanese_text:
                english_text = "Hello."
            elif "ありがとう" in japanese_text:
                english_text = "Thank you."
            else:
                english_text = "This is a simulated translation. Real translation will be implemented in Phase 4."

            # Emit signal with original Japanese and translated English text
            self.translation_completed.emit(japanese_text, english_text)

        # Run in a separate thread to avoid freezing the UI
        self.translation_thread = threading.Thread(target=process)
        self.translation_thread.daemon = True
        self.translation_thread.start()

    def cleanup(self):
        """Clean up audio resources."""
        self.stop_recording()

        # Unload STT model to free memory
        if hasattr(self, 'stt') and self.stt:
            self.stt.unload_model()


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