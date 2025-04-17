cmake_minimum_required(VERSION 3.15)
project(koelingo VERSION 0.1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set the CMake module path to include our custom Find modules
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Set the install prefix to be local to the project
set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}/install")

# Set output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Python package directory
execute_process(
    COMMAND python3 -c "import site; print(site.getsitepackages()[0])"
    OUTPUT_VARIABLE PYTHON_PACKAGE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Set build type if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Tell PyBind11 to use FindPython instead of FindPythonInterp and FindPythonLibs
set(PYBIND11_FINDPYTHON ON)

# Find required packages
find_package(PortAudio REQUIRED)
find_package(pybind11 REQUIRED)

# Set compiler flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -g")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")
endif()

# Add subdirectories - build cpp/ first, then src/
add_subdirectory(cpp)
add_subdirectory(src/audio)