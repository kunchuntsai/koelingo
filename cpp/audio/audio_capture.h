/**
 * @file audio_capture.h
 * @brief C++ implementation of audio capture functionality for KoeLingo
 */

#ifndef KOELINGO_AUDIO_CAPTURE_H
#define KOELINGO_AUDIO_CAPTURE_H

#include <vector>
#include <string>
#include <functional>
#include <memory>
#include <atomic>
#include <thread>
#include <mutex>
#include <deque>
#include <map>
#include <variant>

// Forward declarations for PortAudio types to avoid including the header
struct PaStreamCallbackTimeInfo;
typedef unsigned long PaStreamCallbackFlags;

namespace koelingo {
namespace audio {

/**
 * @class AudioCapture
 * @brief Audio capture and processing class for real-time audio input
 *
 * This class provides audio capture functionality using PortAudio.
 * It can be used to record audio from the microphone, calculate audio levels,
 * and retrieve the audio buffer.
 */
class AudioCapture {
public:
    /**
     * @brief Constructor
     * @param sample_rate Sample rate in Hz (default: 16kHz for Whisper)
     * @param chunk_size Number of frames per buffer
     * @param channels Number of audio channels (1 for mono, 2 for stereo)
     * @param format_type Audio format type from PortAudio
     */
    AudioCapture(int sample_rate = 16000,
                int chunk_size = 1024,
                int channels = 1,
                int format_type = 8); // 8 = paInt16 in PortAudio

    /**
     * @brief Destructor
     */
    ~AudioCapture();

    /**
     * @brief Start recording audio from the microphone
     * @param audio_level_callback Optional callback function to receive audio level updates
     * @return True if recording started successfully, false otherwise
     */
    bool start_recording(std::function<void(float)> audio_level_callback = nullptr);

    /**
     * @brief Stop recording audio
     */
    void stop_recording();

    /**
     * @brief Get the current audio buffer
     * @return Audio data as bytes
     */
    std::vector<char> get_buffer() const;

    /**
     * @brief Save the current audio buffer to a WAV file
     * @param filename Name of the file to save
     * @return True if saved successfully, false otherwise
     */
    bool save_buffer_to_file(const std::string& filename) const;

    /**
     * @brief Get a list of available audio input devices
     * @return List of device information (index, name, channels)
     */
    std::vector<std::map<std::string, std::variant<int, std::string>>> get_available_devices() const;

    /**
     * @brief Check if recording is active
     * @return True if recording, false otherwise
     */
    bool is_recording() const { return is_recording_; }

private:
    // Audio parameters
    int sample_rate_;
    int chunk_size_;
    int channels_;
    int format_type_;

    // PortAudio objects
    void* pa_; // PortAudio instance (void* to avoid including PortAudio header)
    void* stream_; // PortAudio stream

    // Recording state
    std::atomic<bool> is_recording_;
    std::function<void(float)> audio_level_callback_;

    // Audio buffer
    int buffer_seconds_ = 30;
    int max_buffer_size_;
    mutable std::mutex buffer_mutex_;
    std::deque<std::vector<char>> audio_buffer_;

    // Background processing thread
    std::unique_ptr<std::thread> recording_thread_;

    // Internal methods
    void process_audio();
    float calculate_audio_level(const std::vector<char>& audio_data) const;

    // Static PortAudio callback
    static int audio_callback(const void* input_buffer,
                             void* output_buffer [[maybe_unused]],
                             unsigned long frames_per_buffer,
                             const PaStreamCallbackTimeInfo* time_info [[maybe_unused]],
                             PaStreamCallbackFlags status_flags [[maybe_unused]],
                             void* user_data);
};

} // namespace audio
} // namespace koelingo

#endif // KOELINGO_AUDIO_CAPTURE_H