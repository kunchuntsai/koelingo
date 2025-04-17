/**
 * @file audio_capture.cc
 * @brief Implementation of the AudioCapture class
 */

#include "audio_capture.h"
#include <portaudio.h>
#include <cmath>
#include <iostream>
#include <fstream>
#include <chrono>
#include <algorithm>

namespace koelingo {
namespace audio {

// AudioCapture constructor
AudioCapture::AudioCapture(int sample_rate, int chunk_size, int channels, int format_type)
    : sample_rate_(sample_rate),
      chunk_size_(chunk_size),
      channels_(channels),
      format_type_(format_type),
      pa_(nullptr),
      stream_(nullptr),
      is_recording_(false),
      audio_level_callback_(nullptr),
      recording_thread_(nullptr) {

    // Initialize PortAudio
    PaError err = Pa_Initialize();
    if (err != paNoError) {
        std::cerr << "PortAudio initialization error: " << Pa_GetErrorText(err) << std::endl;
        return;
    }

    pa_ = reinterpret_cast<void*>(1); // Mark as initialized

    // Calculate max buffer size (30 seconds of audio)
    max_buffer_size_ = static_cast<int>(buffer_seconds_ * sample_rate_ / chunk_size_);
}

// AudioCapture destructor
AudioCapture::~AudioCapture() {
    // Stop recording if active
    stop_recording();

    // Terminate PortAudio
    if (pa_) {
        Pa_Terminate();
        pa_ = nullptr;
    }
}

// Start recording audio
bool AudioCapture::start_recording(std::function<void(float)> audio_level_callback) {
    if (is_recording_) {
        return true;
    }

    if (!pa_) {
        std::cerr << "PortAudio not initialized" << std::endl;
        return false;
    }

    audio_level_callback_ = audio_level_callback;

    // Clear the audio buffer
    {
        std::lock_guard<std::mutex> lock(buffer_mutex_);
        audio_buffer_.clear();
    }

    // Open a PortAudio stream
    PaStreamParameters inputParams;
    inputParams.device = Pa_GetDefaultInputDevice();
    if (inputParams.device == paNoDevice) {
        std::cerr << "No default input device" << std::endl;
        return false;
    }

    inputParams.channelCount = channels_;
    inputParams.sampleFormat = format_type_;
    inputParams.suggestedLatency = Pa_GetDeviceInfo(inputParams.device)->defaultLowInputLatency;
    inputParams.hostApiSpecificStreamInfo = nullptr;

    PaError err = Pa_OpenStream(
        reinterpret_cast<PaStream**>(&stream_),
        &inputParams,
        nullptr,  // No output
        sample_rate_,
        chunk_size_,
        paClipOff,
        reinterpret_cast<PaStreamCallback*>(&AudioCapture::audio_callback),
        this
    );

    if (err != paNoError) {
        std::cerr << "Error opening PortAudio stream: " << Pa_GetErrorText(err) << std::endl;
        return false;
    }

    // Start the stream
    err = Pa_StartStream(reinterpret_cast<PaStream*>(stream_));
    if (err != paNoError) {
        std::cerr << "Error starting PortAudio stream: " << Pa_GetErrorText(err) << std::endl;
        Pa_CloseStream(reinterpret_cast<PaStream*>(stream_));
        stream_ = nullptr;
        return false;
    }

    is_recording_ = true;

    // Start background processing thread
    recording_thread_ = std::make_unique<std::thread>(&AudioCapture::process_audio, this);

    return true;
}

// Stop recording audio
void AudioCapture::stop_recording() {
    if (!is_recording_) {
        return;
    }

    is_recording_ = false;

    // Close the PortAudio stream
    if (stream_) {
        Pa_StopStream(reinterpret_cast<PaStream*>(stream_));
        Pa_CloseStream(reinterpret_cast<PaStream*>(stream_));
        stream_ = nullptr;
    }

    // Wait for the processing thread to finish
    if (recording_thread_ && recording_thread_->joinable()) {
        recording_thread_->join();
        recording_thread_.reset();
    }
}

// Get the current audio buffer
std::vector<char> AudioCapture::get_buffer() const {
    std::lock_guard<std::mutex> lock(buffer_mutex_);

    // Calculate total size
    size_t totalSize = 0;
    for (const auto& chunk : audio_buffer_) {
        totalSize += chunk.size();
    }

    // Concatenate all chunks
    std::vector<char> buffer;
    buffer.reserve(totalSize);
    for (const auto& chunk : audio_buffer_) {
        buffer.insert(buffer.end(), chunk.begin(), chunk.end());
    }

    return buffer;
}

// Save the audio buffer to a WAV file
bool AudioCapture::save_buffer_to_file(const std::string& filename) const {
    std::vector<char> buffer = get_buffer();
    if (buffer.empty()) {
        std::cerr << "Buffer is empty, nothing to save" << std::endl;
        return false;
    }

    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        std::cerr << "Failed to open file: " << filename << std::endl;
        return false;
    }

    // WAV file header
    struct WAVHeader {
        char riff[4] = {'R', 'I', 'F', 'F'};
        uint32_t fileSize = 0; // Will be set later
        char wave[4] = {'W', 'A', 'V', 'E'};
        char fmt[4] = {'f', 'm', 't', ' '};
        uint32_t fmtChunkSize = 16;
        uint16_t audioFormat = 1; // PCM
        uint16_t numChannels = 0; // Will be set
        uint32_t sampleRate = 0; // Will be set
        uint32_t byteRate = 0; // Will be set
        uint16_t blockAlign = 0; // Will be set
        uint16_t bitsPerSample = 0; // Will be set
        char data[4] = {'d', 'a', 't', 'a'};
        uint32_t dataSize = 0; // Will be set later
    } header;

    // Set header values
    header.numChannels = static_cast<uint16_t>(channels_);
    header.sampleRate = static_cast<uint32_t>(sample_rate_);

    // Assuming format_type is paInt16, which is 16-bit PCM
    header.bitsPerSample = 16;
    header.blockAlign = header.numChannels * (header.bitsPerSample / 8);
    header.byteRate = header.sampleRate * header.blockAlign;

    header.dataSize = static_cast<uint32_t>(buffer.size());
    header.fileSize = 36 + header.dataSize;

    // Write header
    file.write(reinterpret_cast<const char*>(&header), sizeof(header));

    // Write audio data
    file.write(buffer.data(), buffer.size());

    return file.good();
}

// Calculate audio level from raw data
float AudioCapture::calculate_audio_level(const std::vector<char>& audio_data) const {
    if (audio_data.empty()) {
        return 0.0f;
    }

    // Convert bytes to 16-bit samples
    const int16_t* samples = reinterpret_cast<const int16_t*>(audio_data.data());
    size_t sample_count = audio_data.size() / sizeof(int16_t);

    // Calculate RMS
    float sum = 0.0f;
    for (size_t i = 0; i < sample_count; i++) {
        float sample = samples[i] / 32768.0f; // Normalize to [-1.0, 1.0]
        sum += sample * sample;
    }

    float rms = sqrtf(sum / sample_count);

    // Convert to dB
    float db = 20.0f * log10f(std::max(rms, 0.0000001f)); // Avoid log(0)

    // Normalize to [0.0, 1.0] range, assuming -60dB is silence
    float normalized = std::max(0.0f, (db + 60.0f) / 60.0f);
    return std::min(normalized, 1.0f);
}

// Audio processing thread
void AudioCapture::process_audio() {
    while (is_recording_) {
        // Sleep to avoid busy waiting
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

// Static callback for PortAudio
int AudioCapture::audio_callback(const void* input_buffer, void* output_buffer [[maybe_unused]],
                              unsigned long frames_per_buffer,
                              const PaStreamCallbackTimeInfo* time_info [[maybe_unused]], PaStreamCallbackFlags status_flags [[maybe_unused]],
                              void* user_data) {
    AudioCapture* self = static_cast<AudioCapture*>(user_data);

    if (!input_buffer || !self) {
        return paContinue;
    }

    // Calculate buffer size in bytes
    size_t buffer_size = frames_per_buffer * self->channels_ * (self->format_type_ == paInt16 ? 2 : 4);

    // Create a new buffer for this chunk
    std::vector<char> buffer(static_cast<const char*>(input_buffer),
                           static_cast<const char*>(input_buffer) + buffer_size);

    // Calculate audio level if callback is set
    if (self->audio_level_callback_) {
        float level = self->calculate_audio_level(buffer);
        self->audio_level_callback_(level);
    }

    // Add buffer to the queue
    {
        std::lock_guard<std::mutex> lock(self->buffer_mutex_);
        self->audio_buffer_.push_back(std::move(buffer));

        // Limit buffer size
        while (static_cast<int>(self->audio_buffer_.size()) > self->max_buffer_size_) {
            self->audio_buffer_.pop_front();
        }
    }

    return paContinue;
}

// Get available audio devices
std::vector<std::map<std::string, std::variant<int, std::string>>> AudioCapture::get_available_devices() const {
    std::vector<std::map<std::string, std::variant<int, std::string>>> devices;

    if (!pa_) {
        return devices;
    }

    int numDevices = Pa_GetDeviceCount();
    for (int i = 0; i < numDevices; i++) {
        const PaDeviceInfo* deviceInfo = Pa_GetDeviceInfo(i);
        if (deviceInfo && deviceInfo->maxInputChannels > 0) {
            std::map<std::string, std::variant<int, std::string>> device;
            device["index"] = i;
            device["name"] = std::string(deviceInfo->name);
            device["channels"] = deviceInfo->maxInputChannels;
            devices.push_back(device);
        }
    }

    return devices;
}

} // namespace audio
} // namespace koelingo