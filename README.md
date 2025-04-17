# KoeLingo (声リンゴ)

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![macOS](https://img.shields.io/badge/verified%20on-macOS-brightgreen.svg)

"Koe" means "voice" in Japanese, and "Lingo" represents language and linguistic elements. Together, KoeLingo is a fitting name for a project that translates Japanese speech to English in real-time conversations.

## Features

- Real-time Japanese speech-to-text transcription
- Real-time translation from Japanese to English
- Save transcripts in both languages
- High-performance audio capture with C++/Python hybrid architecture
- Optimized for macOS with Apple Silicon

## Architecture

KoeLingo uses a hybrid architecture approach:
1. Core functionality is developed in Python for rapid iteration
2. Performance-critical components are implemented in C++ with PyBind11
3. Automatic fallback to Python when C++ is not available

## Project Structure

```
koelingo/
├── cpp/                  # C++ implementation
│   └── audio/            # Audio capture C++ library
├── src/                  # Python implementation
│   ├── main.py           # Application entry point
│   ├── audio/            # Audio module with Python bindings
│   ├── ui/               # User interface components
│   ├── stt/              # Speech-to-text functionality
│   ├── translation/      # Translation functionality
│   ├── storage/          # Transcript storage
│   └── utils/            # Utility functions and configuration
├── scripts/              # Build and utility scripts
└── tests/                # Test files
    ├── audio/            # Audio module tests
    └── stt/              # Speech-to-text tests
```

## Prerequisites

- Python 3.8 or higher
- C++ compiler that supports C++17
- CMake 3.12 or higher
- PyBind11
- Audio libraries:
  - PortAudio
  - FFmpeg
- Machine Learning:
  - PyTorch
  - Transformers
- Translation:
  - OpenAI API key or local model
- macOS with Apple Silicon (optimized for, may work on other platforms)

## Development

This project is under active development - see the [PROGRESS](docs/3.implementation.md) file for details.

### Setup

1. Set up the development environment:
   ```bash
   # Run the local setup script
   ./scripts/local_setup.sh
   ```

2. Build C++ components:
   ```bash
   # Build the C++ components
   ./scripts/build.sh

   # Clean and rebuild
   ./scripts/build.sh --clean
   ```

3. Run the application:
   ```bash
   # Run the application
   ./scripts/run.sh
   ```

### Testing

Run tests using the test runner with formatted output:

```bash
# Run all tests
./scripts/run.sh --tests

# Run specific audio module tests
./scripts/run.sh --audio

# Run tests with verbose output
./scripts/run.sh --audio --verbose

# Clean build and run tests
./scripts/build.sh --clean && ./scripts/run.sh --audio
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.