#include <torch/script.h>
#include <torch/torch.h>
#include <math.h>

#include "Granulator.h"

// Constructor
Voice::Voice(double grain_sample_rate) {
    note = 60;
    amp = 1.0;
    trigger = false;
    cur_sample = 0;
    grain_sr = grain_sample_rate;
    needs_update = false;
    grain_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr / 2));
    grain_buffer.clear();
    temp_buffer = juce::AudioSampleBuffer(1, grain_buffer.getNumSamples());
    temp_buffer.clear();
    queue_grain(at::zeros(juce::roundToInt(grain_sr / 2))); // default is voice has empty grain
}

void Voice::update_grain(int note_number) {
    // hope this doesn't happen
    if (temp_buffer.getNumSamples() > grain_buffer.getNumSamples()) {
        grain_buffer.setSize(grain_buffer.getNumChannels(), grain_buffer.getNumSamples());
    }
    grain_buffer.copyFrom(0, 0, temp_buffer.getReadPointer(0), temp_buffer.getNumSamples());
    juce::ignoreUnused(note_number);
    needs_update = false; 
}

void Voice::queue_grain(const at::Tensor& grain, int note_number) {
    juce::ignoreUnused(note_number);
    if (grain.size(0) > temp_buffer.getNumSamples()) {
        temp_buffer.setSize(grain_buffer.getNumChannels(), grain_buffer.getNumSamples());
    }
    tensor_to_buffer(grain, temp_buffer);
    needs_update = true;
}

void Voice::note_on() {
    trigger = true;
}

void Voice::note_off() {
    trigger = false;
}

// internal audio callback. return torch tensor of num_samples_grains
// at::Tensor get_audio_data (int num_samples) {
//     at::Tensor idx = at::arange(cur_sample, cur_sample + num_samples);
//     idx = idx % grain_data.size(0);
//     cur_sample = (cur_sample + num_samples) % grain_data.size(0);
//     return grain_data.take(idx) * amp;
// }

void Voice::mix_in_voice(juce::AudioSampleBuffer& buffer, int total_samples) {
    // replace grain in audio thread if we have to
    //std::cout<<this->needs_update;
    if (needs_update) {
        update_grain();
    }

    //total samples is the length of the buffer
    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        auto position = 0;
        // go through total_samples while not going out of range of our grain buffer
        while (position < total_samples)
        {
            auto samples_to_end_of_buffer = grain_buffer.getNumSamples() - cur_sample;
            auto samples_this_time = juce::jmin (total_samples - position, samples_to_end_of_buffer);

            buffer.addFrom (channel,
                            position,
                            grain_buffer,
                            channel,
                            cur_sample,                   
                            samples_this_time);                       


            position += samples_this_time;
            cur_sample += samples_this_time;

            if (cur_sample == grain_buffer.getNumSamples())
                cur_sample = 0;
        }
    }
}
void Voice::tensor_to_buffer(const at::Tensor& tensor, juce::AudioSampleBuffer& buffer) {
    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        auto* channelData = buffer.getWritePointer(channel);
        for (int i = 0; i < buffer.getNumSamples(); ++i)
        {
            channelData[i] = tensor[i].item<float>();
        }
    }
}


Granulator::Granulator(double local_sr) {
    grain_sample_rate = local_sr;
    for (size_t i = 0; i < voices.size(); ++i) {
        voices[i] = Voice(grain_sample_rate);
    }
    voices[0].note_on();
}

void Granulator::replace_grain(const at::Tensor& grain) {
    for (size_t i = 0; i < voices.size(); ++i) {
        voices[i].queue_grain(grain);
    }
}

void Granulator::audio_callback(juce::AudioSampleBuffer& buffer, int total_samples) {
    //data = torch::zeros(num_samples, /*dtype=*/torch::kFloat32);
    buffer.applyGain(0.0);
    for (size_t i = 0; i < voices.size(); ++i) {
        if (voices[i].trigger) {
            voices[i].mix_in_voice(buffer, total_samples);
        }
    }
}