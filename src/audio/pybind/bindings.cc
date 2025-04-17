/**
 * @file bindings.cc
 * @brief PyBind11 bindings for the AudioCapture class
 */

#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include "audio_capture.h"  // Include directly from cpp/audio

namespace py = pybind11;
using namespace koelingo::audio;

PYBIND11_MODULE(audio_capture_cc, m) {
    m.doc() = "Python bindings for AudioCapture C++ class";

    py::class_<AudioCapture>(m, "AudioCaptureCpp")
        .def(py::init<int, int, int, int>(),
             py::arg("sample_rate") = 16000,
             py::arg("chunk_size") = 1024,
             py::arg("channels") = 1,
             py::arg("format_type") = 8)
        .def("start_recording", &AudioCapture::start_recording,
             py::arg("audio_level_callback") = nullptr,
             "Start recording audio from the microphone")
        .def("stop_recording", &AudioCapture::stop_recording,
             "Stop recording audio")
        .def("get_buffer", &AudioCapture::get_buffer,
             "Get the current audio buffer as bytes")
        .def("save_buffer_to_file", &AudioCapture::save_buffer_to_file,
             py::arg("filename"),
             "Save the current audio buffer to a WAV file")
        .def("get_available_devices", &AudioCapture::get_available_devices,
             "Get a list of available audio input devices")
        .def_property_readonly("is_recording", &AudioCapture::is_recording,
             "Check if recording is active");
}