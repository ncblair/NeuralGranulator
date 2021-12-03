#include <torch/script.h>
#include <torch/torch.h>
#include <math.h>

//=========GRANULATOR CLASSES
class Voice {
    private:
        int cur_sample;
        double grain_sr;
        juce::AudioSampleBuffer grain_buffer;
        juce::AudioSampleBuffer temp_buffer;
        bool needs_update;
    public:
        int note;
        float amp;
        bool trigger;

        // Constructor
        Voice(double grain_sample_rate=16000) {
            note = 60;
            amp = 1.0;
            this->trigger = false;
            this->cur_sample = 0;
            grain_sr = grain_sample_rate;
            this->needs_update = false;
            this->grain_buffer = juce::AudioSampleBuffer(1, juce::roundToInt(grain_sr / 2));
            this->grain_buffer.clear();
            this->temp_buffer = juce::AudioSampleBuffer(1, grain_buffer.getNumSamples());
            this->temp_buffer.clear();
            queue_grain(at::zeros(juce::roundToInt(grain_sr / 2))); // default is voice has empty grain
        }

        void update_grain(int note=60) {
            // hope this doesn't happen
            if (this->temp_buffer.getNumSamples() > this->grain_buffer.getNumSamples()) {
                this->grain_buffer.setSize(this->grain_buffer.getNumChannels(), this->grain_buffer.getNumSamples());
            }
            this->grain_buffer.copyFrom(0, 0, this->temp_buffer.getReadPointer(0), this->temp_buffer.getNumSamples());
            juce::ignoreUnused(note);
            this->needs_update = false; 
        }

        void queue_grain(const at::Tensor& grain, int note=60) {
            juce::ignoreUnused(note);
            if (grain.size(0) > this->temp_buffer.getNumSamples()) {
                this->temp_buffer.setSize(this->grain_buffer.getNumChannels(), this->grain_buffer.getNumSamples());
            }
            tensor_to_buffer(grain, this->temp_buffer);
            this->needs_update = true;
        }

        void note_on() {
            this->trigger = true;
        }

        void note_off() {
            this->trigger = false;
        }

        // internal audio callback. return torch tensor of num_samples_grains
        // at::Tensor get_audio_data (int num_samples) {
        //     at::Tensor idx = at::arange(cur_sample, cur_sample + num_samples);
        //     idx = idx % grain_data.size(0);
        //     cur_sample = (cur_sample + num_samples) % grain_data.size(0);
        //     return grain_data.take(idx) * amp;
        // }

        void mix_in_voice(juce::AudioSampleBuffer& buffer, int total_samples) {
            // replace grain in audio thread if we have to
            //std::cout<<this->needs_update;
            if (this->needs_update) {
                this->update_grain();
            }

            //total samples is the length of the buffer
            for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
            {
                auto position = 0;
                // go through total_samples while not going out of range of our grain buffer
                while (position < total_samples)
                {
                    auto samples_to_end_of_buffer = this->grain_buffer.getNumSamples() - this->cur_sample;
                    auto samples_this_time = juce::jmin (total_samples - position, samples_to_end_of_buffer);
        
                    buffer.addFrom (channel,
                                    position,
                                    this->grain_buffer,
                                    channel,
                                    this->cur_sample,                   
                                    samples_this_time);                       


                    position += samples_this_time;
                    this->cur_sample += samples_this_time;
        
                    if (this->cur_sample == grain_buffer.getNumSamples())
                        this->cur_sample = 0;
                }
            }
        }
        void tensor_to_buffer(const at::Tensor& tensor, juce::AudioSampleBuffer& buffer) {
            for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
            {
                auto* channelData = buffer.getWritePointer(channel);
                for (int i = 0; i < buffer.getNumSamples(); ++i)
                {
                    channelData[i] = tensor[i].item<float>();
                }
            }
        }
};

class Granulator {
    private:
        std::array<Voice, 12> voices; // 12 = MAX VOICES
    public:
        double grain_sample_rate;

        Granulator(double local_sr = 16000) {
            grain_sample_rate = local_sr;
            for (int i = 0; i < voices.size(); ++i) {
                voices[i] = Voice(grain_sample_rate);
            }
            voices[0].note_on();
        }

        void replace_grain(const at::Tensor& grain) {
            for (int i = 0; i < voices.size(); ++i) {
                voices[i].queue_grain(grain);
            }
        }

        void audio_callback(juce::AudioSampleBuffer& buffer, int total_samples) {
            //data = torch::zeros(num_samples, /*dtype=*/torch::kFloat32);
            buffer.applyGain(0.0);
            for (int i = 0; i < voices.size(); ++i) {
                if (voices[i].trigger) {
                    voices[i].mix_in_voice(buffer, total_samples);
                }
            }
        }
};