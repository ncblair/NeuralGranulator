#include <torch/script.h>
#include <torch/torch.h>
#include <math.h>

#include "Granulator.h"
#define GRAIN_SAMPLE_RATE (16000.0)

// Constructor
//Voice::Voice() : window(size_t(juce::roundToInt(GRAIN_SAMPLE_RATE / 2)), juce::dsp::WindowingFunction<float>::WindowingMethod::hann){
Voice::Voice() {
    note = 60;
    amp = 1.0;
    cur_sample = 0;
    cur_samp_offset = 0;
    grain_sr = GRAIN_SAMPLE_RATE;
    needs_update = false;
    note_num_samples = 0;
    std::cout << "CONSTRUCTOR" << std::endl;
    percent_of_grain = 1.0;
    scan_percentage = 0.0;
    key_pressed = false;
    making_noise = false;
    needs_ramp = false;
    //TO DEAL WITH SCANNING, IMPLEMENT PITCH SHIFT DELAY

    // voice playback buffer probably only needs to be a few hundred samples long
    voice_playback_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr / 2)); 
    voice_playback_buffer.clear();
    // Allocate 16 second buffer so we can play really low slow grains
    note_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr * 16)); 
    note_buffer.clear();

    note_windowing_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr * 16)); 
    note_windowing_buffer.clear();
    // next_note_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr * 16)); 
    // next_note_buffer.clear();
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
    // std::cout << "Pitch Voice Run Time: " << juce::Time::getMillisecondCounter() - time << std::endl;
    std::cout << "received note on " << midinote << std::endl;
}

void Voice::pitch_voice() {
    note_num_samples = int(grain_buffer.getNumSamples() / std::pow(2., (note - 60.)/12.));
    
    std::cout << "note num samples " << note_num_samples << std::endl;
    std::cout << "percent of grain " << percent_of_grain << std::endl;
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
    smooth_grain();

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
    // std::cout << "START CUR SAMPLE " << cur_sample << std::endl;
    auto num_samples_in_grain = int(note_num_samples * percent_of_grain);
    auto sample_offset = int(note_num_samples * scan_percentage) % note_num_samples;
    cur_samp_offset = (sample_offset + cur_sample) % note_num_samples;
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
            // dual grain is playing simultaneously, halfway offset for smoothing
            auto dual_grain_sample = (cur_sample + num_samples_in_grain / 2) % num_samples_in_grain;
            auto dual_grain_sample_offset = (dual_grain_sample + sample_offset) % note_num_samples;

            auto furthest_sample_along_offset = juce::jmax(dual_grain_sample_offset, cur_samp_offset);
            auto furthest_sample_along_local = juce::jmax(dual_grain_sample, cur_sample);

            auto samples_to_end_of_buffer = note_num_samples - furthest_sample_along_offset;
            auto samples_to_end_of_grain = num_samples_in_grain - furthest_sample_along_local;

            // either go to end of grain, end of note buffer, or end of playback buffer
            auto samples_this_time = juce::jmin (samples_to_end_of_grain, samples_to_end_of_buffer); 
            samples_this_time = juce::jmin(samples_this_time, total_samples - position);

            // this will probably never happen
            if (samples_this_time > voice_playback_buffer.getNumSamples()) {
                std::cout << "resize voice playback buffer" << std::endl;
                voice_playback_buffer.setSize(grain_buffer.getNumChannels(), samples_this_time);
            }
            
            // we will apply the envelope to the voice_playback_buffer
            voice_playback_buffer.copyFrom(0, position, note_windowing_buffer, 0, cur_samp_offset, samples_this_time);
            voice_playback_buffer.addFrom(0, position, note_windowing_buffer, 0, dual_grain_sample_offset, samples_this_time);

            env->applyEnvelopeToBuffer(voice_playback_buffer, position, samples_this_time);
            
            // then we apply the add the enveloped content to the main playback buffer
            // this extra step means we never apply the envelope to our note buffer, which would be destructive
            buffer.addFrom(0, position, voice_playback_buffer, 0, position, samples_this_time); 
            
            position += samples_this_time;
            cur_sample += samples_this_time;
            cur_samp_offset += samples_this_time;

            if (cur_samp_offset == note_num_samples) {
                cur_samp_offset = cur_samp_offset % note_num_samples;
            }
            if (cur_sample == num_samples_in_grain) {
                cur_sample = 0;
                cur_samp_offset = sample_offset;
            }
            
        }
    }

    if (!env->isActive()) {
        making_noise = false; // free to assign a new note to this voice!!
    }
}
void Voice::tensor_to_buffer(const at::Tensor& tensor, juce::AudioSampleBuffer& buffer) {
    float* tensor_read_pointer = tensor.data_ptr<float>();
    for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
    {
        buffer.copyFrom(0, 0, tensor_read_pointer, buffer.getNumSamples());
    }
}

void Voice::set_percent_grain(double percent_grain) {
    percent_of_grain = percent_grain;
    smooth_grain();
}

void Voice::set_scan_percentage(double scan_percent) {
    scan_percentage = scan_percent;
    smooth_grain();
}

void Voice::smooth_grain() {
    note_num_samples = int(grain_buffer.getNumSamples() / std::pow(2., (note - 60.)/12.));
    //copy note buffer info to note_windowing_buffer
    note_windowing_buffer.copyFrom(0, 0, note_buffer, 0, 0, note_num_samples);
    auto samps_in_grain = int(note_num_samples * percent_of_grain);
    auto ramp_samples = int(samps_in_grain / 6);
    if (ramp_samples == 0) {
        return;
    }
    auto offset_samples = int(note_num_samples * scan_percentage) % note_num_samples;
    auto min_gain = 0.0;
    while (min_gain != 1.0) {
        auto ramp_samples_next = juce::jmin(ramp_samples, note_num_samples - offset_samples);
        auto max_gain = min_gain + double(ramp_samples_next) / double(ramp_samples);
        note_windowing_buffer.applyGainRamp(offset_samples, ramp_samples_next, min_gain, max_gain);
        
        min_gain = max_gain;
        if (ramp_samples_next + offset_samples == note_num_samples) {
            offset_samples = 0;
        }
        else {
            break;
        }
    }

    auto start_point = (int(note_num_samples * scan_percentage) + samps_in_grain - ramp_samples) % note_num_samples;

    while (min_gain != 0.0) {
        auto ramp_samples_next = juce::jmin(ramp_samples, note_num_samples - start_point);
        auto max_gain = min_gain - double(ramp_samples_next) / double(ramp_samples);
        note_windowing_buffer.applyGainRamp(start_point, ramp_samples_next, 1.0, 0.0);
        min_gain = max_gain;
        if (ramp_samples_next + start_point == note_num_samples) {
            start_point = 0;
        }
        else {
            break;
        }
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

void Granulator::set_grain_size(double percent_of_grain) {
    for (size_t i = 0; i < voices.size(); ++i) {
        voices[i].set_percent_grain(percent_of_grain);
        // voices[i].percent_of_grain = percent_of_grain;
    }
}

void Granulator::set_scan(double scan_percentage) {
    for (size_t i = 0; i < voices.size(); ++i) {
        voices[i].set_scan_percentage(scan_percentage);
        // voices[i].scan_percentage = scan_percentage;
    }
}