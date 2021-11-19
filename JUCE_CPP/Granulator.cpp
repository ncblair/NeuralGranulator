#include <torch/script.h>
#include <torch/torch.h>

//=========GRANULATOR CLASSES
class Voice {
    private:
        int cur_sample;
        at::Tensor grain_data;
    public:
        int note;
        float amp;
        bool trigger;

        // Constructor
        Voice() {
            note = 60;
            amp = 1.0;
            trigger = false;
            cur_sample = 0;
        }

        void replace_grain(at::Tensor grain) {
            grain_data = grain;
        }

        void note_on() {
            trigger = true;
        }

        void note_off() {
            trigger = false;
        }

        // internal audio callback. return torch tensor of num_samples_grains
        at::Tensor get_audio_data (int num_samples) {
            at::Tensor idx = at::arange(cur_sample, cur_sample + num_samples);
            idx = idx % grain_data.size(0);
            cur_sample = (cur_sample + num_samples) % grain_data.size(0);
            return grain_data.take(idx) * amp;
        }
};

class Granulator {
    private:
        std::array<Voice, 12> voices; // 12 = MAX VOICES
        at::Tensor data;
    public:
        Granulator() {
            for (int i = 0; i < voices.size(); ++i) {
                voices[i] = Voice();

                //throw a sine wave in there for now
                voices[i].replace_grain(torch::sin((2 * juce::MathConstants<float>::pi * 440 / 16000) * torch::arange(8000)));
            }
            voices[0].note_on();
        }

        void replace_grain(at::Tensor grain) {
            for (int i = 0; i < voices.size(); ++i) {
                voices[i].replace_grain(grain);
            }
        }

        at::Tensor audio_callback(int num_samples) {
            data = torch::zeros(num_samples, /*dtype=*/torch::kFloat32);
            for (int i = 0; i < voices.size(); ++i) {
                if (voices[i].trigger) {
                    data = data + voices[i].get_audio_data(num_samples);
                }
            }
            return data;
        }
};