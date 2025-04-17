# Find the PortAudio includes and library
#
# This module defines:
#  PORTAUDIO_INCLUDE_DIR - where to find portaudio.h
#  PORTAUDIO_LIBRARIES - the libraries to link against to use PortAudio
#  PORTAUDIO_FOUND - if false, do not try to use PortAudio
#  PORTAUDIO_VERSION - the version of PortAudio found

# Look for the portaudio.h header
find_path(PORTAUDIO_INCLUDE_DIR
  NAMES portaudio.h
  PATHS
    /usr/local/include
    /usr/include
    /opt/local/include
    /sw/include
  PATH_SUFFIXES portaudio
)

# Look for the PortAudio library
find_library(PORTAUDIO_LIBRARY
  NAMES portaudio
  PATHS
    /usr/local/lib
    /usr/lib
    /usr/local/lib64
    /usr/lib64
    /opt/local/lib
    /sw/lib
)

# Handle the QUIETLY and REQUIRED arguments and set PORTAUDIO_FOUND
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(PortAudio 
    REQUIRED_VARS PORTAUDIO_LIBRARY PORTAUDIO_INCLUDE_DIR
)

# Copy the results to the output variables
if(PORTAUDIO_FOUND)
  set(PORTAUDIO_LIBRARIES ${PORTAUDIO_LIBRARY})
  set(PORTAUDIO_INCLUDE_DIRS ${PORTAUDIO_INCLUDE_DIR})
else()
  set(PORTAUDIO_LIBRARIES)
  set(PORTAUDIO_INCLUDE_DIRS)
endif()

mark_as_advanced(PORTAUDIO_INCLUDE_DIR PORTAUDIO_LIBRARY) 