# AudioCapture Library
add_library(audio_capture SHARED
    audio_capture.cc
)

# Library properties
set_target_properties(audio_capture PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
)

# Include directories
target_include_directories(audio_capture
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/../include
        ${PORTAUDIO_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(audio_capture
    PRIVATE
        ${PORTAUDIO_LIBRARIES}
)

# Install targets
install(TARGETS audio_capture
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

# Install headers
install(FILES audio_capture.h
    DESTINATION include/koelingo/audio
)