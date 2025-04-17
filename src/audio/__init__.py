"""
Audio module for KoeLingo.

This module provides audio capture and processing functionality.
It tries to use the optimized C++ implementation when available,
but falls back to the pure Python implementation if necessary.
"""

import logging
import os
import sys

# Try to import the AudioCapture class from the C++ module
try:
    # First try to import using a relative path (development mode)
    try:
        from .audio_capture_cc import AudioCaptureCpp as AudioCapture
        logging.info("Using C++ audio capture implementation (relative import)")
    except ImportError:
        # Then try with src.audio prefix (test environment)
        try:
            from src.audio.audio_capture_cc import AudioCaptureCpp as AudioCapture
            logging.info("Using C++ audio capture implementation (src.audio import)")
        except ImportError:
            # Finally, try the installed package (installed mode)
            from koelingo.audio.audio_capture_cc import AudioCaptureCpp as AudioCapture
            logging.info("Using C++ audio capture implementation (package import)")
except ImportError as e:
    # Log the error at debug level since this is expected behavior when C++ module isn't built
    logging.debug(f"C++ module not available: {e}")
    # Fall back to pure Python implementation
    from .audio_capture import AudioCapture
    logging.info("Using Python audio capture implementation")

__all__ = ['AudioCapture']
