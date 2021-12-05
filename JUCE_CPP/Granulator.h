#include <torch/script.h>
#include <torch/torch.h>
#include <juce_core/juce_core.h>
#include <juce_audio_utils/juce_audio_utils.h>

//=========GRANULATOR CLASSES
class Voice {
    private:
        int cur_sample;
        double grain_sr;
        int note_num_samples;
        juce::AudioSampleBuffer note_buffer;
        juce::AudioSampleBuffer grain_buffer;
        juce::AudioSampleBuffer temp_buffer;
        juce::Interpolators::Lagrange interp; //each voice gets its own resampling interpolator
        bool needs_update;
    public:
        int note;
        float amp;
        bool trigger;

        // Constructor
        Voice(double grain_sample_rate=16000);
        void update_grain(int note_number=60);
        void queue_grain(const at::Tensor& grain, int note_number=60);
        void note_on(int midinote, float amplitude=1.0);
        void note_off();
        void pitch_voice();
        void mix_in_voice(juce::AudioSampleBuffer& buffer, int total_samples);
        void tensor_to_buffer(const at::Tensor& tensor, juce::AudioSampleBuffer& buffer);
};

class Granulator {
    private:
        std::array<Voice, 12> voices; // 12 = MAX VOICES
    public:
        double grain_sample_rate;

        Granulator(double local_sr = 16000);
        void replace_grain(const at::Tensor& grain);
        void audio_callback(juce::AudioSampleBuffer& buffer, int total_samples);
        void note_on(int midinote, float amplitude);
        void note_off(int midinote);
};