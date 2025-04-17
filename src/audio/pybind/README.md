# KoeLingo Audio Module C++ Bindings

This directory contains C++ implementations of the KoeLingo audio capture functionality with Python bindings using PyBind11.

## Overview

The C++ implementation provides significantly better performance compared to the pure Python implementation, especially for audio processing tasks. The hybrid approach allows:

1. Fast prototyping using Python
2. Production-quality performance using C++
3. Graceful fallback to Python when C++ is not available

## Build Instructions

### Prerequisites

- CMake 3.15 or newer
- A C++17 compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- PortAudio development libraries
- Python 3.9 or newer with development headers
- PyBind11

On macOS, you can install the dependencies using Homebrew:

```bash
brew install cmake portaudio python pybind11
```

### Building the Extension

From the project root directory:

```bash
# Create a build directory
mkdir -p build && cd build

# Configure with CMake
cmake ..

# Build the extension
cmake --build .

# Install the extension (optional)
cmake --install .
```

This will build the C++ library and PyBind11 extension module.

## Usage

The bindings are designed to be a drop-in replacement for the Python implementation:

```python
# Import the AudioCapture class
from koelingo.audio import AudioCapture

# Create an instance (automatically selects C++ or Python implementation)
audio = AudioCapture()

# The API is identical to the Python version
audio.start_recording(lambda level: print(f"Audio level: {level:.2f}"))
# ...
audio.stop_recording()

# Check if using C++ implementation
if audio.using_cpp_implementation:
    print("Using optimized C++ implementation")
else:
    print("Using Python implementation")
```

## Troubleshooting

If the C++ extension fails to load, the module will automatically fall back to the Python implementation. The following common issues might prevent the C++ extension from loading:

1. Missing PortAudio library
2. Incompatible C++ compiler or standard library
3. PyBind11 version mismatch

Check the logs for detailed error messages about why the C++ implementation could not be loaded.

## Development

When modifying the C++ implementation, ensure that the Python fallback implementation stays in sync to maintain consistent behavior.

The key files are:
- `audio_capture.cpp` - C++ implementation of audio capture
- `bindings.cpp` - PyBind11 bindings for the C++ implementation
- `__init__.py` - Python module that selects the best available implementation