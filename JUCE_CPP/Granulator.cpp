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
    note_num_samples = 0;
    // Allocate 16 second buffer so we can play really low slow grains
    note_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr * 16)); 
    note_buffer.clear();
    grain_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr / 2));
    grain_buffer.clear();
    temp_buffer = juce::AudioSampleBuffer(1, grain_buffer.getNumSamples());
    temp_buffer.clear();
    interp = juce::Interpolators::Lagrange();
    env = juce::ADSR();
    env.setSampleRate(grain_sample_rate);
    env.setParameters(juce::ADSR::Parameters(0.1f,1.0f,0.6f,1.0f)); // default adsr parameters
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

void Voice::note_on(int midinote, float amplitude) {
    note = midinote;
    amp = amplitude;
    cur_sample = 0;
    //PITCH THE VOICE HERE (or figure that out in a background thread)
    pitch_voice();
    trigger = true;
    env.reset();
    env.noteOn();
}

void Voice::pitch_voice() {
    note_num_samples = int(grain_buffer.getNumSamples() / std::pow(2., (note - 60.)/12.));
    if (note != 60) {
        interp.process (std::pow(2., (note - 60.)/12.), 
                    grain_buffer.getReadPointer(0), 
                    note_buffer.getWritePointer(0), 
                    note_num_samples);
    }
    else {
        note_buffer.addFrom(0, 0, grain_buffer, 0, 0, note_num_samples);
    }
    note_buffer.applyGain(amp);
}
void Voice::note_off() {
    // trigger release phase of voice
    env.noteOff();
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


    //total samples is the length of the audio callback buffer

    // copy samples from voice grain_buffer to processBlock buffer
    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        auto position = 0;
        // go through total_samples while not going out of range of our grain buffer
        while (position < total_samples)
        {
            auto samples_to_end_of_buffer = note_num_samples - cur_sample;
            auto samples_this_time = juce::jmin (total_samples - position, samples_to_end_of_buffer); 

            buffer.addFrom (channel,
                            position,
                            note_buffer,
                            channel,
                            cur_sample,                   
                            samples_this_time); 

            // apply envelope to grain:
            env.applyEnvelopeToBuffer(buffer, position, samples_this_time);                   

            position += samples_this_time;
            cur_sample += samples_this_time;

            if (cur_sample == note_num_samples)
                cur_sample = 0;
        }
    }

    // if envelope is finished releasing, turn off voice and reset envelope
    if (!env.isActive()) {
        trigger = false;
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

void Granulator::note_on(int midinote, float amp) {
    for (size_t i = 0; i < voices.size(); ++i) {
        if (!voices[i].trigger) {
            voices[i].note_on(midinote, amp);
            return;
        }
    }
}

void Granulator::note_off(int midinote) {
    for (size_t i = 0; i < voices.size(); ++i) {
        if (voices[i].trigger && voices[i].note == midinote) {
            voices[i].note_off();
        }
    }
}