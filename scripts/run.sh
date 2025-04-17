#!/bin/bash
# run.sh - Runner script for KoeLingo application

set -e  # Exit on error

# Print section header
print_header() {
    echo "===================================================================="
    echo "  $1"
    echo "===================================================================="
    echo
}

# Parse command-line arguments
parse_args() {
    # Default values
    DEBUG_MODE=0
    RUN_TESTS=0
    CLEAN_BUILD=0
    BUILD=0
    TEST_MODULE=""
    VERBOSE=0
    RUN_STT_TESTS=0
    RUN_STT_PERF_TESTS=0
    RUN_INTEGRATION_TESTS=0

    # Parse command-line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --debug)
                DEBUG_MODE=1
                shift
                ;;
            --tests)
                RUN_TESTS=1
                if [[ "$2" != --* && "$2" != "" ]]; then
                    TEST_MODULE="$2"
                    shift
                fi
                shift
                ;;
            --audio)
                RUN_TESTS=1
                TEST_MODULE="audio"
                shift
                ;;
            --stt)
                RUN_TESTS=1
                RUN_STT_TESTS=1
                shift
                ;;
            --stt-perf)
                RUN_TESTS=1
                RUN_STT_PERF_TESTS=1
                shift
                ;;
            --integration)
                RUN_TESTS=1
                RUN_INTEGRATION_TESTS=1
                shift
                ;;
            --all-stt)
                RUN_TESTS=1
                RUN_STT_TESTS=1
                RUN_STT_PERF_TESTS=1
                RUN_INTEGRATION_TESTS=1
                shift
                ;;
            --clean)
                CLEAN_BUILD=1
                BUILD=1
                shift
                ;;
            --build)
                BUILD=1
                shift
                ;;
            --verbose|-v)
                VERBOSE=1
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --debug     Run in debug mode"
                echo "  --tests     Run tests instead of the application"
                echo "              (can be followed by a specific module name)"
                echo "  --audio     Run audio tests specifically"
                echo "  --stt       Run speech-to-text tests"
                echo "  --stt-perf  Run STT performance tests"
                echo "  --integration Run integration tests (audio to STT)"
                echo "  --all-stt   Run all STT-related tests"
                echo "  --clean     Clean build before running"
                echo "  --build     Build before running"
                echo "  --verbose   Verbose output in tests"
                echo "  --help, -h  Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Run '$0 --help' for usage information."
                exit 1
                ;;
        esac
    done
}

# Activate virtual environment
activate_venv() {
    VENV_DIR="venv"

    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        echo "Virtual environment not found. Please run ./scripts/local_setup.sh first."
        exit 1
    fi

    # Activate virtual environment
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Set up Python paths
    echo "Setting up Python paths..."
    INSTALL_DIR="$(pwd)/build/install"

    # Add source code to Python path
    export PYTHONPATH="$(pwd):$(pwd)/src:${PYTHONPATH}"

    # Add install directory to Python path for compiled modules
    export PYTHONPATH="${INSTALL_DIR}:${PYTHONPATH}"

    # Add library path for native libraries
    if [[ "$OSTYPE" == "darwin"* ]]; then
        export DYLD_LIBRARY_PATH="${INSTALL_DIR}/lib:${DYLD_LIBRARY_PATH}"
    else
        export LD_LIBRARY_PATH="${INSTALL_DIR}/lib:${LD_LIBRARY_PATH}"
    fi
}

# Build the C++ components if needed
build_if_needed() {
    if [ $BUILD -eq 1 ]; then
        # Build options
        BUILD_OPTS=""

        if [ $DEBUG_MODE -eq 1 ]; then
            BUILD_OPTS="$BUILD_OPTS --debug"
        fi

        if [ $RUN_TESTS -eq 1 ]; then
            BUILD_OPTS="$BUILD_OPTS --tests"
        fi

        if [ $CLEAN_BUILD -eq 1 ]; then
            BUILD_OPTS="$BUILD_OPTS --clean"
        fi

        # Run build script
        ./scripts/build.sh $BUILD_OPTS
    fi
}

# Run the application
run_app() {
    print_header "Running KoeLingo Application"

    echo "Starting application..."
    python src/main.py
}

# Run tests
run_tests() {
    print_header "Running Tests"

    VERBOSITY=""
    if [ $VERBOSE -eq 1 ]; then
        VERBOSITY="--verbose"
    fi

    if [ $RUN_STT_TESTS -eq 1 ]; then
        echo "Running STT tests..."
        python -m tests.run_tests stt $VERBOSITY
    fi

    if [ $RUN_STT_PERF_TESTS -eq 1 ]; then
        echo "Running STT performance tests..."
        python -m tests.run_tests stt.test_performance $VERBOSITY
    fi

    if [ $RUN_INTEGRATION_TESTS -eq 1 ]; then
        echo "Running integration tests (audio to STT)..."
        python -m tests.run_tests integration.test_audio_stt $VERBOSITY
    fi

    if [ -n "$TEST_MODULE" ]; then
        echo "Running tests in module: $TEST_MODULE..."
        # Use our custom test runner
        python -m tests.run_tests $TEST_MODULE $VERBOSITY
    elif [ $RUN_STT_TESTS -eq 0 ] && [ $RUN_STT_PERF_TESTS -eq 0 ] && [ $RUN_INTEGRATION_TESTS -eq 0 ]; then
        echo "Running all tests..."
        # Use our custom test runner for all tests
        python -m tests.run_tests $VERBOSITY
    fi
}

# Main function
main() {
    print_header "KoeLingo Runner"

    # Get the directory of the script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Change to project root directory
    cd "$SCRIPT_DIR/.."

    # Parse command-line arguments
    parse_args "$@"

    # Activate virtual environment
    activate_venv

    # Build if needed
    build_if_needed

    # Run tests or application
    if [ $RUN_TESTS -eq 1 ]; then
        run_tests
    else
        run_app
    fi
}

# Run main function
main "$@"