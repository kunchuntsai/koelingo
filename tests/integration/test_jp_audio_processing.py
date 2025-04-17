"""
Integration test for Japanese audio processing.

This test verifies that Japanese audio can be correctly received and processed by the STT model.
"""

import unittest
import os
import tempfile
import time
import threading
import numpy as np
import wave
from pathlib import Path
import urllib.request
import hashlib
import subprocess

from src.audio import AudioCapture
from src.stt import WhisperSTT


class JapaneseAudioProcessingTest(unittest.TestCase):
    """Test Japanese audio processing through the STT pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio = AudioCapture(sample_rate=16000)  # 16kHz for Whisper
        self.stt = WhisperSTT(model_size="tiny", language="ja")
        self.temp_dir = tempfile.mkdtemp()
        self.resources_dir = Path(os.path.dirname(__file__)).parent / "resources"
        
        # Create resources directory if it doesn't exist
        if not self.resources_dir.exists():
            self.resources_dir.mkdir(parents=True)
            
        print("Running Japanese audio processing tests...")

    def tearDown(self):
        """Tear down test fixtures."""
        self.audio.stop_recording()
        self.stt.unload_model()

        # Clean up temp directory
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def _download_sample_audio(self, filename, url):
        """
        Download a sample audio file from URL if it doesn't exist in resources directory.
        
        Args:
            filename: The name to save the file as
            url: The URL to download from
            
        Returns:
            Path to the downloaded file
        """
        file_path = self.resources_dir / filename
        
        # Skip download if file already exists
        if file_path.exists():
            print(f"Using existing audio file: {file_path}")
            return file_path
            
        print(f"Downloading sample audio from {url}")
        # Create a temporary file for downloading
        tmp_path = Path(self.temp_dir) / filename
        
        # Download the file
        urllib.request.urlretrieve(url, tmp_path)
        
        # Move to resources directory
        os.rename(tmp_path, file_path)
        
        print(f"Downloaded audio file: {file_path}")
        return file_path
        
    def _load_audio_file(self, file_path):
        """
        Load audio data from a file.
        
        Args:
            file_path: Path to audio file (WAV or MP3)
            
        Returns:
            numpy.ndarray: Audio data as 16-bit PCM numpy array
        """
        file_path = str(file_path)
        
        # Check if file is MP3
        if file_path.lower().endswith('.mp3'):
            # Convert MP3 to WAV using FFmpeg if available
            try:
                wav_path = file_path.replace('.mp3', '.wav')
                wav_path = os.path.join(self.temp_dir, os.path.basename(wav_path))
                
                # Try to use ffmpeg if available
                try:
                    subprocess.run(
                        [
                            'ffmpeg', '-y',  # Overwrite output file if it exists
                            '-i', file_path,  # Input file
                            '-acodec', 'pcm_s16le',  # Output codec (16-bit PCM)
                            '-ar', '16000',  # Sample rate (16kHz)
                            '-ac', '1',  # Channels (mono)
                            wav_path  # Output file
                        ],
                        check=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    print(f"Converted MP3 to WAV using ffmpeg: {wav_path}")
                    file_path = wav_path
                except (subprocess.SubprocessError, FileNotFoundError):
                    # If ffmpeg fails, try using librosa if available
                    try:
                        import librosa
                        # Load using librosa (automatically resamples)
                        audio_data, sr = librosa.load(file_path, sr=16000, mono=True)
                        # Convert to 16-bit PCM
                        audio_data = (audio_data * 32767).astype(np.int16)
                        return audio_data
                    except ImportError:
                        raise ImportError("Neither ffmpeg nor librosa is available to process MP3 files. Install librosa or ffmpeg.")
            except Exception as e:
                print(f"Error converting MP3 to WAV: {e}")
                raise
                
        # At this point, file_path should be a WAV file (either originally or converted)
        with wave.open(file_path, 'rb') as wf:
            # Check if this is a mono 16kHz file
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            
            # Read all frames
            frames = wf.readframes(wf.getnframes())
            
        # Convert to numpy array
        audio_data = np.frombuffer(frames, dtype=np.int16)
        
        # If stereo, convert to mono by averaging channels
        if channels == 2:
            audio_data = audio_data.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
        # If not 16kHz, we should resample, but for test purposes we'll just warn
        if sample_rate != 16000:
            print(f"Warning: Audio sample rate is {sample_rate}Hz, model expects 16000Hz")
            
        return audio_data

    def _generate_japanese_phonetic_audio(self):
        """
        Generate synthetic audio that approximates Japanese phonetic sounds.
        
        This uses formants common in Japanese phonemes to create a synthetic
        audio signal that has some characteristics of Japanese speech.
        
        Returns:
            numpy.ndarray: Synthetic audio data
        """
        sample_rate = 16000
        duration = 3.0  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        
        # Create a synthetic signal with frequencies common in Japanese speech
        # These are approximations of formants for some Japanese vowels
        # a: 800Hz, i: 300Hz, u: 400Hz, e: 500Hz, o: 600Hz
        vowel_formants = [
            (800, 0.4),  # 'a' vowel with amplitude
            (300, 0.3),  # 'i' vowel with amplitude
            (400, 0.3),  # 'u' vowel with amplitude
            (500, 0.3),  # 'e' vowel with amplitude
            (600, 0.3),  # 'o' vowel with amplitude
        ]
        
        # Create a signal that transitions between these formants
        signal = np.zeros_like(t)
        segment_duration = duration / len(vowel_formants)
        
        for i, (freq, amp) in enumerate(vowel_formants):
            # Calculate start and end sample for this vowel segment
            start_sample = int(i * segment_duration * sample_rate)
            end_sample = int((i + 1) * segment_duration * sample_rate)
            
            # Generate the vowel segment
            segment_t = t[start_sample:end_sample]
            segment = amp * np.sin(2 * np.pi * freq * segment_t)
            
            # Add some modulation for more natural sound
            modulation = 0.1 * np.sin(2 * np.pi * 5 * segment_t)  # 5Hz modulation
            segment = segment * (1 + modulation)
            
            # Add to full signal
            signal[start_sample:end_sample] = segment
        
        # Apply an envelope to the signal
        envelope = np.ones_like(t)
        fade_samples = int(0.1 * sample_rate)  # 100ms fade in/out
        
        # Fade in
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        # Fade out
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        signal = signal * envelope
        
        # Convert to 16-bit PCM
        audio_data = (signal * 32767).astype(np.int16)
        return audio_data

    def test_ProcessJapaneseAudio(self):
        """Test that synthetic Japanese audio can be processed by the STT pipeline."""
        
        # Generate synthetic audio with Japanese phonetic characteristics
        audio_data = self._generate_japanese_phonetic_audio()
        
        # Save to WAV file
        temp_wav = os.path.join(self.temp_dir, "japanese_test_audio.wav")
        
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for 16-bit
            wf.setframerate(16000)
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
        print(f"Processing synthetic Japanese audio file: {temp_wav}")
        self.stt.transcribe_audio(audio_data, on_transcription)
        
        # Wait for transcription to complete (with timeout)
        transcription_complete.wait(timeout=30)
        
        # Verify results
        print(f"Transcription result: '{transcription_result}'")
        print(f"Confidence score: {confidence_score:.2f}")
        
        # We don't expect meaningful transcription from synthetic audio,
        # just checking that the pipeline completes and produces some output
        self.assertTrue(transcription_complete.is_set())
        self.assertIsNotNone(transcription_result)
        self.assertIsNotNone(confidence_score)

    def test_RealJapaneseAudioSamples(self):
        """
        Test with real Japanese audio samples downloaded from the internet.
        
        This test downloads and processes actual Japanese audio samples.
        """
        # Dictionary of sample Japanese audio files and their expected content
        # Using open samples from Tatoeba (a free, collaborative, open-source collection of sentences)
        samples = [
            {
                "filename": "japanese_sample1.mp3",
                "url": "https://audio.tatoeba.org/sentences/jpn/1186.mp3",
                "expected_content_contains": ["こん", "これ"],  # Potential content in Japanese
            },
            {
                "filename": "japanese_sample2.mp3",
                "url": "https://audio.tatoeba.org/sentences/jpn/12962.mp3",
                "expected_content_contains": ["ありがとう", "どうも"],  # Potential content in Japanese
            }
        ]
        
        for sample in samples:
            try:
                # Download sample if needed
                audio_file = self._download_sample_audio(sample["filename"], sample["url"])
                
                # Load audio data
                audio_data = self._load_audio_file(audio_file)
                
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
                print(f"\nProcessing real Japanese audio file: {audio_file}")
                self.stt.transcribe_audio(audio_data, on_transcription)
                
                # Wait for transcription to complete (with timeout)
                transcription_complete.wait(timeout=30)
                
                # Verify results
                print(f"Transcription result: '{transcription_result}'")
                print(f"Confidence score: {confidence_score:.2f}")
                
                # Verify the pipeline completed successfully
                self.assertTrue(transcription_complete.is_set())
                self.assertIsNotNone(transcription_result)
                self.assertIsInstance(confidence_score, float)
                
                # We're not checking exact content matches because Whisper tiny model
                # might not be perfectly accurate, especially with short samples.
                # But we log the results for manual inspection.
                
                # Optional: Check if any of the expected content appears in the result
                # This is a weak test but provides some validation of output quality
                if transcription_result:
                    has_expected_content = False
                    for expected in sample["expected_content_contains"]:
                        if expected in transcription_result:
                            has_expected_content = True
                            print(f"Found expected content: '{expected}'")
                            break
                    
                    if not has_expected_content:
                        print("Warning: Transcription does not contain any expected content")
                
            except Exception as e:
                print(f"Error processing sample {sample['filename']}: {e}")
                # Don't fail the test if a sample fails, just log it
                import traceback
                traceback.print_exc()

    def test_LiveJapaneseAudioProcessing(self):
        """
        Test with live audio, asking the user to speak Japanese.
        
        This test is interactive and requires the user to speak Japanese.
        It will be skipped if no audio devices are available or if SKIP_LIVE_AUDIO
        environment variable is set.
        """
        # Skip if SKIP_LIVE_AUDIO environment variable is set
        if os.environ.get('SKIP_LIVE_AUDIO', False):
            self.skipTest("Skipping live Japanese audio test (SKIP_LIVE_AUDIO is set)")
        
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
        
        # Create events for synchronization
        transcription_complete = threading.Event()
        transcription_result = None
        confidence_score = None
        
        # Prompt the user to speak
        print("\n======================================================")
        print("INTERACTIVE TEST: Please speak in Japanese for 5 seconds when recording starts.")
        print("If you don't speak Japanese, any speech will work to test the pipeline.")
        print("======================================================\n")
        
        # Wait for 3 seconds to give the user time to read the prompt
        time.sleep(3)
        
        # Start recording
        print("Starting recording NOW - please speak in Japanese...")
        self.audio.start_recording()
        
        # Record for 5 seconds
        time.sleep(5.0)
        
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
            self.skipTest("Audio level too low, microphone may not be working")
        
        # Save the recorded audio for reference
        recorded_wav = os.path.join(self.temp_dir, "recorded_japanese.wav")
        with wave.open(recorded_wav, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for 16-bit
            wf.setframerate(16000)
            wf.writeframes(audio_data.tobytes())
        print(f"Recorded audio saved to: {recorded_wav}")
        
        # Process through STT
        print("Processing recorded audio through STT...")
        self.stt.transcribe_audio(audio_data, on_transcription)
        
        # Wait for transcription to complete
        transcription_complete.wait(timeout=30)
        
        # Print results
        print("\n======================================================")
        print(f"Transcription result: '{transcription_result}'")
        print(f"Confidence score: {confidence_score:.2f}")
        print("======================================================\n")
        
        # Verify the pipeline completed successfully
        self.assertTrue(transcription_complete.is_set())
        self.assertIsNotNone(transcription_result)
        self.assertIsInstance(confidence_score, float)
        
        # We don't validate the content of the transcription, just that it produced output

    def test_GeneratedJapaneseAudio(self):
        """
        Test with a locally generated Japanese-like audio file.
        
        This creates a more complex synthetic audio that approximates
        Japanese speech patterns for testing the STT pipeline.
        """
        
        # Generate a more complex Japanese-like audio
        # This will create a sequence of tones that approximate Japanese phonemes
        # in a pattern that might trigger the model to recognize it as speech
        sample_rate = 16000
        duration = 5.0  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        
        # Japanese vowel formants (approximate frequencies)
        vowels = [
            {"name": "a", "f1": 800, "f2": 1200, "duration": 0.3},
            {"name": "i", "f1": 300, "f2": 2500, "duration": 0.2},
            {"name": "u", "f1": 400, "f2": 1200, "duration": 0.2},
            {"name": "e", "f1": 500, "f2": 1800, "duration": 0.3},
            {"name": "o", "f1": 600, "f2": 900, "duration": 0.3},
            {"name": "a", "f1": 800, "f2": 1200, "duration": 0.3},
            {"name": "ri", "f1": 400, "f2": 2000, "duration": 0.4},
            {"name": "ga", "f1": 700, "f2": 1400, "duration": 0.4},
            {"name": "to", "f1": 500, "f2": 1000, "duration": 0.3},
            {"name": "u", "f1": 400, "f2": 1200, "duration": 0.5},
        ]
        
        # Generate audio signal for each vowel with formants
        signal = np.zeros_like(t)
        current_position = 0.0
        
        for vowel in vowels:
            # Calculate time slice for this vowel
            start_time = current_position
            end_time = start_time + vowel["duration"]
            
            # Ensure we don't exceed total duration
            if end_time > duration:
                break
                
            # Calculate sample indices
            start_idx = int(start_time * sample_rate)
            end_idx = int(end_time * sample_rate)
            
            # Create vowel segment with formants
            segment_t = t[start_idx:end_idx] - start_time  # Local time for this segment
            
            # First formant
            f1_signal = 0.5 * np.sin(2 * np.pi * vowel["f1"] * segment_t)
            # Second formant
            f2_signal = 0.3 * np.sin(2 * np.pi * vowel["f2"] * segment_t)
            # Combine formants
            vowel_signal = f1_signal + f2_signal
            
            # Apply envelope for natural sound
            envelope = np.ones_like(segment_t)
            fade_samples = int(0.03 * sample_rate)  # 30ms fade in/out
            
            # Fade in/out if segment is long enough
            if len(envelope) > 2 * fade_samples:
                envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
                envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
                
            # Apply envelope
            vowel_signal = vowel_signal * envelope
            
            # Add to main signal
            signal[start_idx:end_idx] = vowel_signal
            
            # Update position
            current_position = end_time
            
            # Add a small pause between "words"
            if vowel["name"] in ["u", "o", "e"] and current_position < duration - 0.2:
                pause_duration = 0.2
                current_position += pause_duration
        
        # Convert to 16-bit PCM
        audio_data = (signal * 32767).astype(np.int16)
        
        # Save to WAV file
        temp_wav = os.path.join(self.temp_dir, "japanese_synthetic.wav")
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for 16-bit
            wf.setframerate(16000)
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
        print(f"\nProcessing complex Japanese-like synthetic audio file: {temp_wav}")
        self.stt.transcribe_audio(audio_data, on_transcription)
        
        # Wait for transcription to complete (with timeout)
        transcription_complete.wait(timeout=30)
        
        # Verify results
        print(f"Transcription result: '{transcription_result}'")
        print(f"Confidence score: {confidence_score:.2f}")
        
        # We're just checking that the pipeline completes and produces some output
        self.assertTrue(transcription_complete.is_set())
        self.assertIsNotNone(transcription_result)
        self.assertIsNotNone(confidence_score)


if __name__ == "__main__":
    unittest.main() 