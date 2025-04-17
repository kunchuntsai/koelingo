# Audio Module CMake Configuration

# Find required packages
find_package(PortAudio REQUIRED)
find_package(pybind11 REQUIRED)

# Include directories
include_directories(
    ${PORTAUDIO_INCLUDE_DIRS}
    ${CMAKE_INSTALL_PREFIX}/include  # Include installed headers
    ${CMAKE_SOURCE_DIR}/cpp/audio    # Include the direct path to the header
)

# Find PyBind bindings source
file(GLOB PYBIND_SRC
    "${CMAKE_CURRENT_SOURCE_DIR}/pybind/bindings.cc"
)

# PyBind11 module - link against the installed audio_capture library
pybind11_add_module(audio_capture_cc MODULE ${PYBIND_SRC})

# Link against the standalone library
target_link_libraries(audio_capture_cc PRIVATE audio_capture)

# Install Python module
install(TARGETS audio_capture_cc
    LIBRARY DESTINATION koelingo/audio
)