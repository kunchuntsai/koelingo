# KoeLingo Code Organization

This document explains the structure of the KoeLingo codebase, particularly focusing on the C++ and Python integration.

## Directory Structure

```
koelingo/
├── cpp/                   # C++ implementation
│   ├── audio/             # Audio capture C++ library
│   │   ├── audio_capture.h       # C++ header for audio capture
│   │   ├── audio_capture.cc      # C++ implementation
│   │   └── CMakeLists.txt        # Build configuration for C++ library
│   └── CMakeLists.txt      # Main C++ build configuration
├── src/                   # Python implementation
│   ├── audio/             # Audio module
│   │   ├── pybind/        # Python bindings for C++ implementation
│   │   │   ├── bindings.cc        # PyBind11 binding definitions
│   │   │   ├── __init__.py        # Python wrapper with fallback
│   │   │   └── README.md          # Documentation
│   │   ├── audio_capture.py       # Pure Python implementation (fallback)
│   │   └── CMakeLists.txt         # Build configuration for bindings
│   └── ...                # Other Python modules
└── ...                    # Project configuration files
```

## Architecture

KoeLingo uses a hybrid architecture:

1. **Core C++ Implementation**
   - Located in `cpp/audio/`
   - Contains the high-performance implementation of audio capture using PortAudio
   - Designed as a standalone C++ library that can be used in any C++ project

2. **Python Bindings**
   - Located in `src/audio/pybind/`
   - Provides Python bindings for the C++ implementation using PyBind11
   - Creates a seamless interface between Python and the C++ code

3. **Python Fallback**
   - Located in `src/audio/audio_capture.py`
   - Provides a pure Python implementation that serves as a fallback
   - Used when the C++ implementation is not available (e.g., missing dependencies)

4. **Unified Python Interface**
   - Located in `src/audio/pybind/__init__.py`
   - Provides a consistent API regardless of whether the C++ or Python implementation is used
   - Automatically selects the best available implementation

## Build Process

1. The C++ library in `cpp/audio/` is built first
2. The Python bindings in `src/audio/pybind/` are built second, linking against the C++ library
3. The build system ensures that the C++ library is available when building the Python bindings

## Usage

From a user's perspective, the implementation details are hidden:

```python
from koelingo.audio import AudioCapture

# Automatically uses C++ implementation if available, falls back to Python if not
audio = AudioCapture()

# Same API regardless of implementation
audio.start_recording()
```

## Development Guidelines

1. When modifying audio capture functionality:
   - Update the C++ implementation in `cpp/audio/`
   - Ensure the Python fallback in `src/audio/audio_capture.py` maintains compatible behavior

2. When adding new features:
   - First implement in the C++ library
   - Update the Python bindings
   - Add a fallback implementation in Python