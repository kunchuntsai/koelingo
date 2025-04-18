#!/bin/bash
# local_setup.sh - Setup script for KoeLingo development environment

set -e  # Exit on error

# Print section header
print_header() {
    echo "===================================================================="
    echo "  $1"
    echo "===================================================================="
    echo
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        echo "Detected macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        echo "Detected Linux"
    else
        echo "Unsupported OS: $OSTYPE"
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_header "Installing system dependencies"

    if [[ "$OS" == "macos" ]]; then
        echo "Checking for Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Please install Homebrew first:"
            echo "https://brew.sh/"
            exit 1
        fi

        echo "Installing dependencies with Homebrew..."
        brew install python portaudio cmake pybind11
    elif [[ "$OS" == "linux" ]]; then
        echo "Installing dependencies with apt..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip portaudio19-dev cmake libpython3-dev

        # Install pybind11 with pip
        sudo pip3 install pybind11
    fi

    echo "System dependencies installed successfully."
}

# Set up Python virtual environment
setup_venv() {
    print_header "Setting up Python virtual environment"

    VENV_DIR="venv"

    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    else
        echo "Virtual environment already exists at $VENV_DIR"
    fi

    # Activate virtual environment
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt

    # Install OpenAI Whisper from GitHub
    echo "Installing OpenAI Whisper from GitHub..."
    pip install git+https://github.com/openai/whisper.git

    echo "Python environment setup complete."
    echo
    echo "To activate the virtual environment in the future, run:"
    echo "source venv/bin/activate"
}

# Verify test dependencies
verify_test_deps() {
    print_header "Verifying test dependencies"
    
    # Ensure we're in the virtual environment
    source "venv/bin/activate"
    
    # Check for test dependencies
    echo "Checking for test dependencies..."
    python -c "import matplotlib" &>/dev/null || pip install matplotlib
    python -c "import psutil" &>/dev/null || pip install psutil
    
    # Create a test runner script if it doesn't exist
    if [ ! -f "run_tests.sh" ]; then
        echo "Creating test runner script..."
        cat > run_tests.sh << 'EOF'
#!/bin/bash
# run_tests.sh - Run all KoeLingo tests

# Activate virtual environment
source venv/bin/activate

# Set Python paths
export PYTHONPATH=$(pwd):$PYTHONPATH

# Run audio tests
echo "======================================================================"
echo "  Running Audio Processing Tests"
echo "======================================================================"
python -m tests.run_tests audio.test_continuous_processing --verbose

# Run STT tests
echo "======================================================================"
echo "  Running Speech-to-Text Tests"
echo "======================================================================"
python -m tests.run_tests stt.test_continuous_stt --verbose

# Run integration tests
echo "======================================================================"
echo "  Running Integration Tests"
echo "======================================================================"
python -m tests.run_tests integration.test_realtime_pipeline --verbose

# Run stability test
echo "======================================================================"
echo "  Running Stability Tests"
echo "======================================================================"
python -m tests.stability_tests --duration=60
EOF
        chmod +x run_tests.sh
    fi
    
    echo "Test dependencies verified."
    echo "You can run tests with: ./run_tests.sh"
}

# Main function
main() {
    print_header "KoeLingo Development Environment Setup"

    # Get the directory of the script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Change to project root directory
    cd "$SCRIPT_DIR/.."

    # Detect operating system
    detect_os

    # Install system dependencies
    install_system_deps

    # Set up Python virtual environment
    setup_venv
    
    # Verify test dependencies
    verify_test_deps

    print_header "Setup Complete"
    echo "KoeLingo development environment has been set up successfully."
    echo
    echo "Next steps:"
    echo "1. To build the C++ components: ./scripts/build.sh"
    echo "2. To run the application: ./scripts/run.sh"
    echo "3. To run all tests: ./run_tests.sh"
}

# Run main function
main