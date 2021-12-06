#include <torch/script.h>
#include <torch/torch.h>
#include <math.h>

#include "Granulator.h"
#define GRAIN_SAMPLE_RATE (16000.0)

// Constructor
//Voice::Voice() : window(size_t(juce::roundToInt(GRAIN_SAMPLE_RATE / 2)), juce::dsp::WindowingFunction<float>::hann){
Voice::Voice() {
    note = 60;
    amp = 1.0;
    cur_sample = 0;
    grain_sr = GRAIN_SAMPLE_RATE;
    needs_update = false;
    note_num_samples = 0;
    key_pressed = false;
    making_noise = false;

    // Allocate 16 second buffer so we can play really low slow grains
    note_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr * 16)); 
    note_buffer.clear();
    grain_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr / 2));
    grain_buffer.clear();
    temp_buffer = juce::AudioSampleBuffer(1, grain_buffer.getNumSamples());
    temp_buffer.clear();

    interp = juce::Interpolators::Lagrange();

    env = new juce::ADSR();
    env->setSampleRate(grain_sr);
    env->setParameters(juce::ADSR::Parameters(0.001f,1.0f,1.0f,1.0f)); // default adsr parameters

    queue_grain(at::zeros(juce::roundToInt(grain_sr / 2))); // default is voice has empty grain
}

void Voice::update_grain() {
    //TODO MAKE GRAIN BLEND IN

    // hope this doesn't happen, would only happen if model spits out different sized grains
    if (temp_buffer.getNumSamples() > grain_buffer.getNumSamples()) {
        grain_buffer.setSize(grain_buffer.getNumChannels(), grain_buffer.getNumSamples());
    }
    grain_buffer.copyFrom(0, 0, temp_buffer.getReadPointer(0), temp_buffer.getNumSamples());
    // window.multiplyWithWindowingTable (grain_buffer.getReadPointer(0), grain_buffer.getNumSamples());
    if (making_noise) {
        pitch_voice();
    }
    needs_update = false;
}

void Voice::queue_grain(const at::Tensor& grain) {
    // while (needs_update) {
    //     juce::Time::waitForMillisecondCounter(juce::Time::getMillisecondCounter() + 1);
    // }
    // needs_update = false; // don't update while this is copying (probably not the best way)
    if (grain.size(0) > temp_buffer.getNumSamples()) {
        std::cout << "resize temp buffer" << std::endl;
        temp_buffer.setSize(grain_buffer.getNumChannels(), grain_buffer.getNumSamples());
    }
    tensor_to_buffer(grain, temp_buffer);
    needs_update = true;
}

void Voice::note_on(int midinote, float amplitude) {
    note = midinote;
    amp = amplitude;
    cur_sample = 0;
    // env.reset();
    // auto time = juce::Time::getMillisecondCounter();
    pitch_voice();
    env->noteOn();
    key_pressed = true;
    making_noise = true;
    //std::cout << "Pitch Voice Run Time: " << juce::Time::getMillisecondCounter() - time << std::endl;
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
        note_buffer.copyFrom(0, 0, grain_buffer, 0, 0, note_num_samples);
    }
    note_buffer.applyGain(amp);
}
void Voice::note_off() {
    // trigger release phase of voice
    key_pressed = false;
    env->noteOff();
}

// internal audio callback. return torch tensor of num_samples_grains
// at::Tensor get_audio_data (int num_samples) {
//     at::Tensor idx = at::arange(cur_sample, cur_sample + num_samples);
//     idx = idx % grain_data.size(0);
//     cur_sample = (cur_sample + num_samples) % grain_data.size(0);
//     return grain_data.take(idx) * amp;
// }

void Voice::mix_in_voice(juce::AudioSampleBuffer& buffer, int total_samples) {
    //total samples is the length of the audio callback buffer

    // copy samples from voice grain_buffer to processBlock buffer
    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        auto position = 0;
        // go through total_samples while not going out of range of our grain buffer
        while (position < total_samples)
        {
            // replace grain in audio thread if we have to, only when we are at cur_sample = 0 to avoid clicking
            if (needs_update && cur_sample == 0) {
                update_grain();
            }
            auto samples_to_end_of_buffer = note_num_samples - cur_sample;
            auto samples_this_time = juce::jmin (total_samples - position, samples_to_end_of_buffer); 

            env->applyEnvelopeToBuffer(note_buffer, cur_sample, samples_this_time);

            buffer.addFrom (channel,
                            position,
                            note_buffer,
                            channel,
                            cur_sample,                   
                            samples_this_time); 
            

            position += samples_this_time;
            cur_sample += samples_this_time;

            if (cur_sample == note_num_samples) {
                cur_sample = 0;
            }
        }
    }

    if (!env->isActive()) {
        making_noise = false; // free to replace this voice with a new pitch!
    }
}
void Voice::tensor_to_buffer(const at::Tensor& tensor, juce::AudioSampleBuffer& buffer) {
    float* tensor_read_pointer = tensor.data_ptr<float>();
    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        buffer.copyFrom(0, 0, tensor_read_pointer, buffer.getNumSamples());
    }
}

Granulator::Granulator() {
    grain_sample_rate = GRAIN_SAMPLE_RATE;
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
        if (voices[i].making_noise) {
            voices[i].mix_in_voice(buffer, total_samples);
        }
    }
}

void Granulator::note_on(int midinote, float amp) {
    for (size_t i = 0; i < voices.size(); ++i) {
        if (!voices[i].making_noise) {
            voices[i].note_on(midinote, amp);
            return;
        }
    }
    std::cout << "NO VOICES AVAILABLE" << std::endl;
}

void Granulator::note_off(int midinote) {
    for (size_t i = 0; i < voices.size(); ++i) {
        if (voices[i].key_pressed && voices[i].note == midinote) {
            voices[i].note_off();
        }
    }
}

void Granulator::setADSR(double attack, double decay, double sustain, double release) {
    for (size_t i = 0; i < voices.size(); ++i) {
        voices[i].env->setParameters(juce::ADSR::Parameters(
            float(attack), float(decay), float(sustain), float(release))
        );
    }
    std::cout << "SET ADSR PARAMS" << std::endl;
}