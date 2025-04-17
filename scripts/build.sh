#!/bin/bash
# build.sh - Build script for KoeLingo C++ components

set -e  # Exit on error

# Parse command line arguments
CLEAN_BUILD=false
for arg in "$@"; do
  if [[ $arg == "--clean" ]]; then
    CLEAN_BUILD=true
  fi
done

# Print section header
print_header() {
    echo "===================================================================="
    echo "  $1"
    echo "===================================================================="
    echo
}

# Activate virtual environment
activate_venv() {
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "Virtual environment activated."
    else
        echo "Error: Virtual environment not found. Please run ./scripts/local_setup.sh first."
        exit 1
    fi
}

# Build the C++ components
build() {
    print_header "Building KoeLingo C++ Components"

    # Create build directory if it doesn't exist
    mkdir -p build
    cd build

    if [ "$CLEAN_BUILD" = true ]; then
        print_header "Performing clean build"
        rm -rf *
    fi

    # Run CMake
    echo "Running CMake..."
    cmake ..

    # Build the project
    echo "Building project..."
    cmake --build . -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)

    echo "Build completed successfully."
    cd ..
}

# Main function
main() {
    # Get the directory of the script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Change to project root directory
    cd "$SCRIPT_DIR/.."

    # Activate virtual environment
    activate_venv

    # Build the project
    build

    print_header "Build Complete"
    echo "KoeLingo C++ components have been built successfully."
}

# Run main function
main